"""Halve actual time steps while keeping existing piecewise source powers."""
import csv,hashlib,json,re,shutil
from export_native_brake import ROOT,RUN

def prepare():
    name='C_normal12_rd95_time2';base=RUN/'studies/C_normal12_rd95_dt1';folder=RUN/'studies'/name
    folder.mkdir(exist_ok=False)
    raw=(base/'study.dat').read_text(encoding='utf-8-sig')
    def half(m):
        v=[float(x) for x in m[1].split(',')];assert len(v)==3 and max(v)-min(v)<1e-10
        return 'deltim,'+','.join('%.14g'%(x/2) for x in v)
    text=re.sub(r'(?im)^deltim,([^\r\n]+)',half,raw)
    (folder/'study.dat').write_text(text,encoding='utf-8')
    old=list(csv.DictReader((base/'source_intervals.csv').open()));rows=[]
    for r in old:
        dt=float(r['dt_s']);end=float(r['time_s'])
        for time in [end-dt/2,end]:rows.append(dict(r,time_s=time,dt_s=dt/2))
    with (folder/'source_intervals.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    m=json.loads((base/'study_settings.json').read_text(encoding='utf-8-sig'))
    for key in ['execution_status','viewfactor_sha256']:m.pop(key,None)
    m.update(status='GENERATED_NOT_EXECUTED',expected_sets=2*m['expected_sets'],step_divisor=2,
        capacity_weights=str(ROOT/'results/m4/studies'/name/'FE_capacity_weights.npz'),
        time_refinement='DELTIM halved; source powers held in the same existing bins. No physical source rebinning.',
        actual_native_input_sha256=hashlib.sha256((folder/'study.dat').read_bytes()).hexdigest())
    (folder/'study_settings.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    from reuse_view_factors import prepare as reuse
    reuse('C_normal12_rd95_dt1',[name])
    return name

if __name__=='__main__':print(prepare())
