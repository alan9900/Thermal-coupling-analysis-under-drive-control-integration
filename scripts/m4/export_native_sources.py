"""Controlled one-cycle A/C/D studies from immutable accepted M1-derived bins.

Not the archived six-cycle M2 scenario. Exact interval integration preserves
M1-derived energy under rebinning. Internal spatial allocations are S3.
"""
import argparse,csv,hashlib,json,re
from pathlib import Path
import numpy as np
from export_native_brake import ROOT,RUN
KEYS=['copper','iron','rotor_other','inverter_external','gear_mesh','gear_bearing','gear_other','disc','pad']
def aggregate(rows,width):
    start=float(rows[0]['start_s']);end=float(rows[-1]['end_s']);edges=np.linspace(start,end,int(np.ceil((end-start)/width))+1)
    out=[]
    for a,b in zip(edges[:-1],edges[1:]):
        q=np.zeros(9)
        for r in rows:
            overlap=max(0,min(b,float(r['end_s']))-max(a,float(r['start_s'])))
            q+=overlap*np.array([float(r[k+'_engineering_W']) for k in KEYS])
        out.append((b-a,q/(b-a)))
    expected=sum((float(r['end_s'])-float(r['start_s']))*np.array([float(r[k+'_engineering_W']) for k in KEYS]) for r in rows)
    actual=sum(dt*q for dt,q in out);assert np.max(abs(actual-expected))<1e-7
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['A','C','D'],required=True);p.add_argument('--divisor',type=int,default=1)
    p.add_argument('--input',type=Path,default=RUN/'face_scoped_ds.dat');p.add_argument('--name')
    p.add_argument('--capacity-json',type=Path,default=ROOT/'results/m4/FE_capacity_checks.json')
    a=p.parse_args();assert a.divisor in [1,2]
    case={'A':'A_internal_only','C':'C_combined','D':'D_preheat_braking'}[a.case]
    path=ROOT/'results/m2/cases'/f'{case}_forcing.csv';raw=list(csv.DictReader(path.open()))
    source=[]
    for seg in ([1,2,3] if a.case=='D' else [1,2]):
        rows=[r for r in raw if int(r['segment_id'])==seg]
        isbrake=seg==(3 if a.case=='D' else 2)
        # Preserve the accepted braking bins; 1 s drive, 4 s high-load hold.
        source.extend(aggregate(rows,(.25 if isbrake else (4 if a.case=='D' and seg==2 else 1))/a.divisor))
    source.extend([(5/a.divisor,np.zeros(9))]*(6*a.divisor))
    if a.case=='A':source=[(dt,np.r_[q[:7],0,0]) for dt,q in source]
    text=a.input.read_text(encoding='utf-8-sig');m=re.search(r'^solve\s*$',text,re.M|re.I);assert m;prefix=text[:m.start()]
    pilot=json.loads((RUN/'pilot_source.json').read_text(encoding='utf-8-sig'))
    areas=[]
    for table,q in [('_loadvari571',pilot['disc_W'][0]/2),('_loadvari573',pilot['disc_W'][0]/2),('_loadvari575',pilot['pad_W'][0]/2),('_loadvari577',pilot['pad_W'][0]/2)]:
        value=float(re.search(re.escape(table)+r'\(1,1,1\)\s*=\s*([\d.Ee+\-]+)',prefix)[1]);areas.append(q/value)
    cap=json.loads(a.capacity_json.read_text(encoding='utf-8-sig'));vol=cap['body_volume_m3']
    name=a.name or (case+'_dt'+str(a.divisor));assert re.fullmatch('[A-Za-z0-9_]+',name)
    folder=RUN/'studies'/name;folder.mkdir(parents=True,exist_ok=False)
    commands=['! Same actual Mechanical FE mesh/contacts; only controlled heat-source mask changes',
        'allsel','esel,s,ename,,152','esel,a,ename,,252','esel,a,ename,,174','cm,M4_BC_RECORDS,elem','allsel',
        'outres,erase','outres,all,none','outres,nsol,all','outres,rsol,all','outres,veng,all','outres,fflux,all','outres,cont,all','outres,misc,all,M4_BC_RECORDS']
    t=0;record=[]
    for dt,q in source:
        t+=dt
        # Inverter remains external. Never add EMOT/gear totals again.
        distribution={'MOTOR_WINDING':q[0],'MOTOR_STATOR':q[1],'MOTOR_ROTOR_OTHER':q[2],
            'STAGE1_GEAR':q[4]/2,'STAGE2_GEAR':q[4]/2,'OIL_INVENTORY':q[6]}
        for ax in ['INPUT','INTERMEDIATE','OUTPUT']:
            for j in [1,2]:distribution[ax+'_BEARING_'+str(j)]=q[5]/6
        assert abs(sum(distribution.values())-sum(q[:3])-sum(q[4:7]))<1e-8
        for body,power in distribution.items():
            commands+=['cmsel,s,M4_'+body,'bfe,all,hgen,1,%.14g'%(power/vol['M4_'+body])]
        for typ,power,area in zip([95,96,97,98],[q[7]/2,q[7]/2,q[8]/2,q[8]/2],areas):
            commands+=['allsel','esel,s,type,,%d'%typ,'nsle','sf,all,hflux,%.14g'%(power/area)]
        commands+=['allsel','deltim,%.14g,%.14g,%.14g'%(dt,dt,dt),'time,%.14g'%t,'solve']
        record.append(dict(time_s=t,dt_s=dt,**dict(zip(KEYS,q.tolist())),internal_applied_W=sum(distribution.values()),source_applied_W=sum(q)-q[3]))
    commands+=['finish','/exit,nosa'];dest=folder/'study.dat';dest.write_text(prefix+'\n'+'\n'.join(commands)+'\n')
    with (folder/'source_intervals.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(record[0]));w.writeheader();w.writerows(record)
    settings=dict(case=case,classification='S3_CONCEPT_NOT_CALIBRATED',duration_s=t,expected_sets=len(source),step_divisor=a.divisor,
        original_input=str(a.input),original_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),
        source_volume_basis=str(a.capacity_json),source_volume_basis_sha256=hashlib.sha256(a.capacity_json.read_bytes()).hexdigest(),
        archived_forcing=str(path),forcing_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        applied_energy_J=sum(r['dt_s']*r['source_applied_W'] for r in record),
        inverter_external_J=sum(r['dt_s']*r['inverter_external'] for r in record),
        spatial_loss_allocation='S3: copper to winding, iron to stator, rotor/other to equivalent rotor; gear mesh 50/50 driven wheels, bearings 1/6 each, other to oil. No calibrated tooth/pinion distribution.',
        status='GENERATED_NOT_EXECUTED',cooling='Finite h, prescribed 25C bulk; no coolant-flow/capacity calibration or hot-air feedback',
        comparison_scope='First drive/optional 60s hold/first brake/30s cooling; not full six-cycle M2 peaks',
        capacity_weights=str(ROOT/'results/m4/studies'/name/'FE_capacity_weights.npz'))
    (folder/'study_settings.json').write_text(json.dumps(settings,indent=2)+'\n');print(folder,'steps',len(source),'applied J',settings['applied_energy_J'])
if __name__=='__main__':main()
