"""Resume unexecuted inputs; preserve all interrupted native attempts."""
import json,subprocess,hashlib
from pathlib import Path
from export_native_brake import RUN,ROOT

def main():
    studies=RUN/'studies'
    interrupted=studies/'B_normal24_rd95_dt1'
    (interrupted/'interruption_receipt.json').write_text(json.dumps({
        'status':'STOPPED_EXPENSIVE_RADIOSITY_ITERATIONS_NO_COMPLETE_STEP',
        'input_preserved':True,'solver_error_claim':False,
        'reason':'1e-6 radiosity criterion repeated expensive coupling iterations; no temperature accepted.',
        'replacement':'B_normal24_rd95h_dt1; heat 1e-6, radiosity 1e-4, separately validated'},indent=2)+'\n')
    sources=['C_normal12_rd95_dt1',*['C_normal12_rd95_'+x for x in ['contact_low','contact_high','cooling_low','cooling_high']],'D_normal12_rd95_dt1']
    for name in sources:
        folder=studies/name;assert not (folder/'study.out').exists(),name
        p=folder/'study.dat';text=p.read_text();assert 'radopt,,1.e-6' in text
        text=text.replace('radopt,,1.e-6','radopt,,1.e-4');p.write_text(text)
        m=json.loads((folder/'study_settings.json').read_text());m['radiosity_flux_tolerance']=1e-4
        m['derived_input_sha256']=hashlib.sha256(text.encode()).hexdigest()
        (folder/'study_settings.json').write_text(json.dumps(m,indent=2)+'\n')
    mesh=['B_normal24_rd95h_dt1','B_normal24_rd90h_dt1','B_normal12_rd95h_dt1','B_normal12_rd95h_dt2','B_normal12_rd95h_dt4']
    for label,names,wait in [('mesh_h',mesh,None),('sources_h',sources,'C_normal12_dt1')]:
        script=RUN/('queue_'+label+'.ps1')
        commands=["$ErrorActionPreference='Stop'"]
        if wait:
            commands += ["$log='"+str(studies/wait/'study.out').replace('\\','/')+"'",
                "do { $complete=(Get-Content -LiteralPath $log -Tail 60 | Out-String) -match 'RUN COMPLETED'; if(-not $complete){Start-Sleep -Seconds 10} } while(-not $complete)"]
        commands += ["& 'E:/ansys_runs/m4_case0_20261021/run_native_studies.ps1' -Cases @("+','.join("'"+n+"'" for n in names)+") -Cores 4"]
        script.write_text('\n'.join(commands)+'\n')
        ps="Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','"+str(script).replace('\\','/')+"') -WindowStyle Hidden -RedirectStandardOutput '"+str(RUN/('queue_'+label+'.log')).replace('\\','/')+"' -RedirectStandardError '"+str(RUN/('queue_'+label+'.err')).replace('\\','/')+"' -PassThru | Select-Object Id"
        subprocess.run(['powershell','-NoProfile','-Command',ps],check=True)
    watch=['C_normal12_dt1',*mesh,*sources]
    with (RUN/'post_queue_h.log').open('w') as out,(RUN/'post_queue_h.err').open('w') as err:
        p=subprocess.Popen(['E:/ansys_runs/m4_python_ascii/Scripts/python.exe',str(ROOT/'scripts/m4/watch_completed.py'),*watch],cwd=ROOT,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    print('Postprocessor PID',p.pid)

if __name__=='__main__':main()
