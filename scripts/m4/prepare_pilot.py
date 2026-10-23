"""First brake-only diagnostic; not the final combined Case0 acceptance run."""
import csv,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];RUN=Path('E:/ansys_runs/m4_case0_20261021');OUT=ROOT/'results/m4'
def main():
    rows=list(csv.DictReader((ROOT/'results/m2/cases/B_brake_only_forcing.csv').open()))
    rows=[r for r in rows if int(r['segment_id'])==2]
    start=float(rows[0]['start_s']);eps=1e-7;points=[]
    for i,r in enumerate(rows):
        a=float(r['start_s'])-start;b=float(r['end_s'])-start
        q=[float(r[k+'_engineering_W']) for k in ['disc','pad']]
        points.extend([(a+(eps if i else 0),*q),(b,*q)])
    stop=float(rows[-1]['end_s'])-start;points.extend([(stop+eps,0,0),(stop+30,0,0)])
    arr=np.array(points);target=np.array([sum((float(r['end_s'])-float(r['start_s']))*float(r[k+'_engineering_W']) for r in rows) for k in ['disc','pad']])
    raw=np.trapezoid(arr[:,1:],arr[:,0],axis=0);arr[:,1:]*=target/raw
    assert max(abs(np.trapezoid(arr[:,1:],arr[:,0],axis=0)-target))<1e-7
    payload=dict(label='M4_B_brake_only_DIAGNOSTIC_NOT_VALIDATED',time_s=arr[:,0].tolist(),disc_W=arr[:,1].tolist(),pad_W=arr[:,2].tolist(),
        source_energy_J=target.tolist(),duration_s=stop+30,brake_duration_s=stop,transition_epsilon_s=eps,
        brake_bin_end_s=[float(r['end_s'])-start for r in rows],
        limitations=['No hot-air feedback yet','Internal motor/gear sources excluded in first diagnostic','Mesh/time/energy acceptance pending'])
    for path in [RUN/'pilot_source.json',OUT/'pilot_source.json']:path.write_text(json.dumps(payload,indent=2)+'\n')
    print('Pilot interval-to-linear-table energy PASS:',target)
if __name__=='__main__':main()
