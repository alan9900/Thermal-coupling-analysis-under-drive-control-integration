"""Bounded two-solver queue; reserve the existing mesh and D jobs until terminal.

This replaces only a waiting parent queue, never a native solver. Inputs and
source histories are unchanged. After the mesh sequence completes its slot is
available to an independent uncertainty study, avoiding needless idle cores.
"""
import argparse,json,re,subprocess,time
from datetime import datetime
from export_native_brake import RUN

PENDING=['A_normal12_rd95_dt1','C_normal12_rd95_contact_high',
         'C_normal12_rd95_cooling_low','C_normal12_rd95_cooling_high']

def terminal(name):
    path=RUN/'studies'/name/'study.out'
    if not path.exists():return False
    with path.open('rb') as f:
        f.seek(max(0,path.stat().st_size-16000));tail=f.read().decode('ascii',errors='replace')
    if 'RUN COMPLETED' not in tail:return False
    assert re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0',tail),name+' failed'
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('--adopt',choices=PENDING,action='append',default=[]);a=p.parse_args()
    pending=[n for n in PENDING if n not in a.adopt]
    assert all(not (RUN/'studies'/n/'study.out').exists() for n in pending),'Never relaunch an existing attempt'
    assert all((RUN/'studies'/n/'study.out').exists() for n in a.adopt)
    active={};records=[dict(case=n,event='ADOPT_EXISTING_NATIVE_NO_RELAUNCH',at=datetime.now().isoformat()) for n in a.adopt]
    receipt=RUN/'source_queue_rebalanced.json'
    while pending or active:
        for name,(p,streams) in list(active.items()):
            if terminal(name):
                p.wait(timeout=30)
                assert p.returncode==0,(name,p.returncode)
                for s in streams:s.close()
                del active[name];records.append(dict(case=name,event='COMPLETED_ZERO_ERRORS',at=datetime.now().isoformat()))
                print('Completed:',name,flush=True)
            elif p.poll() is not None and p.returncode!=0:raise RuntimeError(name+' launcher failed')
        reserved=sum(not terminal(n) for n in ['D_normal12_rd95_dt1','B_normal12_rd95h_dt4',*a.adopt])
        while pending and reserved+len(active)<2:
            name=pending.pop(0)
            out=(RUN/(name+'_queue.log')).open('w');err=(RUN/(name+'_queue.err')).open('w')
            p=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(RUN/'run_native_studies.ps1'),'-Cases',name,'-Cores','4'],
                stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            active[name]=(p,[out,err]);records.append(dict(case=name,event='LAUNCHED',parent_pid=p.pid,at=datetime.now().isoformat()))
            print('Launched:',name,'parent',p.pid,flush=True)
        receipt.write_text(json.dumps(dict(max_native_jobs=2,cores_each=4,pending=pending,
            active=list(active),records=records,scope='Queue scheduling only; no native solver stopped or input changed.'),indent=2)+'\n',encoding='utf-8')
        if pending or active:time.sleep(10)

if __name__=='__main__':main()
