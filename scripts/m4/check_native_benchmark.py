"""Check actual MAPDL temperatures against discrete heat balance, not Case0."""
import json,csv,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4'
RUN=Path('E:/ansys_runs/m4_native_benchmark')
def main():
    log=(RUN/'benchmark2.out').read_text(errors='replace')
    assert 'NUMBER OF ERROR   MESSAGES ENCOUNTERED=          0' in log
    assert 'NUMBER OF WARNING MESSAGES ENCOUNTERED=          0' in log
    hot,cold=map(float,(RUN/'benchmark_temperatures.csv').read_text().strip().split(','))
    C=7800*500*.1**3;H=2000*6*.1**2;dt=.5
    expected_hot=25+1000*10/C;expected_cold=25+(hot-25)/(1+H*dt/C)**20
    cooling=[];T=hot
    for i in range(20):
        T=25+(T-25)/(1+H*dt/C);cooling.append(dict(time_s=10+(i+1)*dt,T_C=T,Q_out_W=H*(T-25)))
    lost=sum(r['Q_out_W']*dt for r in cooling);balance=C*(cold-hot)+lost
    assert max(abs(hot-expected_hot),abs(cold-expected_cold))<1e-9
    assert abs(balance)<1e-7 and abs(C*(hot-25)-10000)<1e-7
    shutil.copy2(RUN/'benchmark2.out',OUT/'native_benchmark_actual.out')
    shutil.copy2(RUN/'benchmark_temperatures.csv',OUT/'native_benchmark_temperatures.csv')
    result=dict(status='PASS_NATIVE_SINGLE_ELEMENT_BENCHMARK_ONLY',solver='MAPDL 2024 R1',
        native_hot_C=hot,native_cold_C=cold,analytic_BE_hot_C=expected_hot,analytic_BE_cold_C=expected_cold,
        stored_J=C*(hot-25),cooling_boundary_J=lost,cooling_balance_residual_J=balance,
        warnings=0,errors=0,Case0_energy_balance='NOT YET VALIDATED',
        limitations='Symmetry makes this cube isothermal; checks solver units/capacity/BE convection, not spatial mesh accuracy or radiation.')
    (OUT/'native_benchmark_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
