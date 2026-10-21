"""Reproduce the Mechanical-generated FE model with selective result output.

Physics, mesh, finite contacts and source tables are unchanged. Retain nodal
temperature, volume, thermal/contact flux and boundary MISC records. Avoid
writing unused miscellaneous records for every solid at every time point.
"""
import json,re,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUN=Path('E:/ansys_runs/m4_case0_20261021')
def main():
    p=argparse.ArgumentParser();p.add_argument('--divisor',type=int,default=1);p.add_argument('--input',type=Path,default=RUN/'face_scoped_ds.dat');p.add_argument('--name')
    a=p.parse_args();assert a.divisor in [1,2,4]
    original=a.input;text=original.read_text();match=re.search(r'^solve\s*$',text,re.M|re.I);assert match
    prefix=text[:match.start()]
    name=a.name or ('B_brake_dt'+str(a.divisor));assert re.fullmatch('[A-Za-z0-9_]+',name)
    folder=RUN/'studies'/name;folder.mkdir(parents=True,exist_ok=True)
    source=json.loads((RUN/'pilot_source.json').read_text());ends=source['brake_bin_end_s']
    commands=['! Selective records: physical quantities unchanged','allsel','esel,s,ename,,152','esel,a,ename,,252',
        'cm,M4_BC_RECORDS,elem','allsel','outres,erase','outres,all,none','outres,nsol,all','outres,rsol,all',
        'outres,veng,all','outres,fflux,all','outres,cont,all','outres,misc,all,M4_BC_RECORDS']
    prev=0
    for end in ends:
        dt=(end-prev)/a.divisor
        commands+=['deltim,%.14g,%.14g,%.14g'%(dt,dt,dt),'time,%.14g'%end,'solve'];prev=end
    commands+=['finish','/exit,nosa']
    path=folder/'study.dat';path.write_text(prefix+'\n'+'\n'.join(commands)+'\n')
    meta=dict(case='B_BRAKE_ONLY_CONCEPT',classification='S3_NOT_CALIBRATED',source_model='Mechanical Case0 face-scoped',
        original_input=str(original),original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
        duration_s=ends[-1],expected_sets=16*a.divisor,step_divisor=a.divisor,source_energy_J=source['source_energy_J'],
        physics_change='None: output selection only; no whole-body contact fallback',
        run_command='ANSYS241.exe -b -smp -np 2 -p ansys -j study -dir "'+str(folder)+'" -i "'+str(path)+'" -o "'+str(folder/'study.out')+'"')
    if a.input!=RUN/'face_scoped_ds.dat':meta['capacity_weights']=str(ROOT/'results/m4/studies'/name/'FE_capacity_weights.npz')
    (folder/'study_settings.json').write_text(json.dumps(meta,indent=2)+'\n');print(folder)
if __name__=='__main__':main()
