"""Fresh retries after external interruption; never overwrite partial native runs."""
import hashlib,json,shutil,subprocess,time,re
from datetime import datetime
from export_native_brake import ROOT,RUN

RETRIES={'B_normal12_rd95h_dt4':'B_normal12_rd95h_dt4_retry1',
         'A_normal12_rd95_dt1':'A_normal12_rd95_dt1_retry1'}
PENDING=[*RETRIES.values(),'C_normal12_rd95_contact_high','C_normal12_rd95_cooling_low','C_normal12_rd95_cooling_high']

def complete(name):
    p=RUN/'studies'/name/'study.out'
    if not p.exists():return False
    with p.open('rb') as f:
        f.seek(max(0,p.stat().st_size-16000));tail=f.read().decode('ascii',errors='replace')
    if 'RUN COMPLETED' not in tail:return False
    assert re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0',tail),name+' native errors'
    return True

def prepare():
    records=[]
    for old,new in RETRIES.items():
        source=RUN/'studies'/old;dest=RUN/'studies'/new
        assert not complete(old),'Already complete: do not retry'
        dest.mkdir(exist_ok=False)
        files={}
        for p in source.iterdir():
            if p.name in ['study.dat','study.out','study.rth','study.mntr']:
                with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
                files[p.name]=dict(bytes=p.stat().st_size,sha256=h,modified_at=datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat())
        records.append(dict(study=old,status='INTERRUPTED_NO_TERMINAL_NATIVE_LOG',accepted_results=False,
            reason='Observed no running process and no terminal completion after interruption. Specific external cause unknown.',files=files,retry=new))
        for name in ['study.dat','source_intervals.csv']:
            if (source/name).exists():shutil.copy2(source/name,dest/name)
        meta=json.loads((source/'study_settings.json').read_text(encoding='utf-8-sig'))
        meta.update(retry_of=str(source),retry_prepared_at=datetime.now().astimezone().isoformat(),
            status='GENERATED_NOT_EXECUTED',capacity_weights=str(ROOT/'results/m4/studies'/new/'FE_capacity_weights.npz'))
        meta.pop('execution_status',None)
        (dest/'study_settings.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    out=ROOT/'results/m4/attempts/external_interruption_20261022.json'
    out.write_text(json.dumps(dict(studies=records,native_inputs_unchanged=True),indent=2)+'\n',encoding='utf-8')
    # Keep the complete interrupted logs locally; finite tails accompany receipts.
    for old in RETRIES:
        p=RUN/'studies'/old/'study.out'
        with p.open('rb') as f:f.seek(max(0,p.stat().st_size-12000));tail=f.read()
        (out.parent/(old+'_interrupted_tail.txt')).write_bytes(tail)

def main():
    prepare();pending=list(PENDING);active={};events=[]
    for n in pending:assert not (RUN/'studies'/n/'study.out').exists()
    while pending or active:
        for name,(p,streams) in list(active.items()):
            if complete(name):
                p.wait(timeout=30);assert p.returncode==0,(name,p.returncode)
                for s in streams:s.close()
                del active[name];events.append(dict(study=name,event='COMPLETED',at=datetime.now().astimezone().isoformat()))
                print('Completed',name,flush=True)
            elif p.poll() is not None and p.returncode!=0:raise RuntimeError(name+' launcher failure')
        while pending and len(active)<2:
            name=pending.pop(0);logs=[(RUN/(name+'_queue.log')).open('w'),(RUN/(name+'_queue.err')).open('w')]
            p=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(RUN/'run_native_studies.ps1'),'-Cases',name,'-Cores','4'],
                stdout=logs[0],stderr=logs[1],creationflags=subprocess.CREATE_NO_WINDOW)
            active[name]=(p,logs);events.append(dict(study=name,event='LAUNCHED',parent_pid=p.pid,at=datetime.now().astimezone().isoformat()))
            print('Launched',name,p.pid,flush=True)
        (RUN/'queue_20261022.json').write_text(json.dumps(dict(pending=pending,active=list(active),events=events,max_jobs=2,cores_each=4),indent=2)+'\n',encoding='utf-8')
        if pending or active:time.sleep(10)

if __name__=='__main__':main()
