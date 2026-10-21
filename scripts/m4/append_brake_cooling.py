"""Append an explicit source-free cooldown to an UNEXECUTED brake input."""
import argparse,json,re,hashlib
from export_native_brake import RUN
def main():
    p=argparse.ArgumentParser();p.add_argument('study');p.add_argument('--divisor',type=int,required=True);a=p.parse_args()
    folder=RUN/'studies'/a.study;assert not (folder/'study.out').exists()
    m=json.loads((folder/'study_settings.json').read_text(encoding='utf-8-sig'));assert not m.get('cooldown_appended_s')
    path=folder/'study.dat';text=path.read_text(encoding='utf-8-sig');match=re.search(r'^finish\s*\n/exit,nosa\s*$',text,re.M|re.I);assert match
    dt=5/a.divisor;t=m['duration_s'];commands=['! Explicit source-free 30s cooling; finite contacts and boundaries retained']
    for typ in [95,96,97,98]:commands.extend(['allsel','esel,s,type,,%d'%typ,'nsle','sf,all,hflux,0'])
    for i in range(6*a.divisor):
        t+=dt;commands.extend(['allsel','deltim,%.14g,%.14g,%.14g'%(dt,dt,dt),'time,%.14g'%t,'solve'])
    text=text[:match.start()]+'\n'.join(commands)+'\nfinish\n/exit,nosa\n';path.write_text(text)
    m.update(duration_s=t,expected_sets=m['expected_sets']+6*a.divisor,cooldown_appended_s=30,
       cooldown_step_s=dt,brake_duration_s=m['duration_s'],input_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (folder/'study_settings.json').write_text(json.dumps(m,indent=2)+'\n');print(a.study,m['expected_sets'],t)
if __name__=='__main__':main()
