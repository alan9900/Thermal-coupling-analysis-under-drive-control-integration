"""Preprocessing tests; never label these as FE energy/convergence validation."""
import copy,csv,json,math,subprocess
from pathlib import Path
import numpy as np
from m4_inputs import validate,radiation_W
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4'
def reject(f):
    try:f()
    except ValueError:return
    raise AssertionError('Expected rejection')
def main():
    groups=[];p=json.loads((ROOT/'configs/m4_case0.json').read_text(encoding='utf-8'))
    assert validate(p);groups.append('Engineering mode accepts finite explicit candidates')
    reject(lambda:validate(p,'strict'));groups.append('Strict mode refuses unknown calibrated internal/contact/cooling parameters')
    q=copy.deepcopy(p);q['engineering']['contact_h_W_m2K']=[];reject(lambda:validate(q));groups.append('Missing contact uncertainty range is rejected')
    q=copy.deepcopy(p);q['materials']['steel']['cp_J_kgK']=0;reject(lambda:validate(q));groups.append('Nonpositive heat capacity rejected')
    assert all(v is None for v in p['unknown_actual'].values());groups.append('Raw actual unknowns remain null')
    a=radiation_W(350,300,.04,.4,.8,.7);b=radiation_W(300,350,.04,.4,.8,.7)
    assert a>0 and b==-a and radiation_W(300,300,.04,.4,.8,.7)==0;groups.append('Absolute-K radiation reverses with temperature difference')
    reject(lambda:radiation_W(-25,300,.04,.4,.8,.7));groups.append('Negative Kelvin rejected')
    imp=json.loads((OUT/'import_checks.json').read_text());assert imp['parts']==129 and imp['solids']==131 and imp['oil_solids']==3;groups.append('Native import matches CAD part/solid counts')
    faces=json.loads((OUT/'brake_friction_faces.json').read_text());assert .03<faces['near']['area_m2']<.04 and .03<faces['far']['area_m2']<.04
    assert sum(r['disc_power_fraction'] for r in faces.values())==1;groups.append('Only two friction annuli, SI area and power fractions sum to one')
    src=json.loads((OUT/'input_checks.json').read_text());assert len(src['cases'])==4 and max(c['budget_residual_W'] for c in src['cases'])<1e-6;groups.append('Four accepted M1-derived source budgets close; inverter stays external')
    pilot=json.loads((OUT/'pilot_source.json').read_text());t=np.array(pilot['time_s']);Q=np.array([pilot['disc_W'],pilot['pad_W']]).T
    assert np.all(np.diff(t)>0) and np.max(np.abs(np.trapezoid(Q,t,axis=0)-pilot['source_energy_J']))<1e-7
    groups.append('Pilot table integrates exactly to archived M1-derived disc/pad energy')
    assert subprocess.check_output(['git','rev-parse','M3-v1.0^{}'],text=True).strip()=='7a6b9b1512495283fa12dd4a2a7ffdf698554d3e'
    assert not subprocess.check_output(['git','diff','M3-v1.0','--name-only','--','cad/m3_helical','scripts/m3_helical','results/m3_helical'],text=True).strip()
    groups.append('M3 annotated tag points to approved merge; accepted helical source/CAD/results unchanged')
    r=dict(status='PASS_PREPROCESSING_ONLY',test_groups=len(groups),groups=groups,
        FE_energy_balance='NOT VALIDATED',mesh_independence='NOT VALIDATED',time_step_independence='NOT VALIDATED')
    (OUT/'input_tests.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
if __name__=='__main__':main()
