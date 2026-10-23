"""Actual native SHPP/CHECK audit; no altered limits and no thermal solve."""
import argparse,hashlib,json,re,subprocess,time,shutil
from export_native_brake import RUN,ROOT
def main():
    p=argparse.ArgumentParser();p.add_argument('meshes',nargs='+',choices=['normal6','normal12','normal24']);a=p.parse_args()
    out=ROOT/'results/m4/meshes';records={}
    for mesh in a.meshes:
        source=RUN/'mesh_variants'/('mesh_'+mesh)/'mechanical_ds.dat'
        text=source.read_text(encoding='utf-8-sig');first=re.search(r'^solve\s*$',text,re.M|re.I);assert first
        folder=RUN/'shape_checks'/mesh;folder.mkdir(parents=True,exist_ok=False)
        commands=['finish','/prep7','allsel','esel,s,ename,,278','shpp,default','shpp,on','check,esel,err',
          '*get,N_BAD,elem,0,count',"*cfopen,shape_errors,txt","*vwrite,N_BAD","(F12.0)",'*cfclos',
          'allsel','esel,s,ename,,278','check,esel,warn','*get,N_WARN,elem,0,count',
          "*cfopen,shape_warnings,txt","*vwrite,N_WARN","(F12.0)",'*cfclos',
          'allsel','esel,s,ename,,278','shpp,summary','finish','/exit,nosa']
        dest=folder/'audit.dat';dest.write_text(text[:first.start()]+'\n'+'\n'.join(commands)+'\n')
        solver='E:/Program Files/ANSYS Inc/v241/ANSYS/bin/winx64/ANSYS241.exe'
        subprocess.run([solver,'-b','-smp','-np','2','-p','ansys','-j','audit','-dir',str(folder),'-i',str(dest),'-o',str(folder/'audit.out')],check=False)
        deadline=time.time()+900
        while time.time()<deadline:
            log=folder/'audit.out'
            if log.exists() and 'RUN COMPLETED' in log.read_text(encoding='utf-8-sig', errors='replace')[-16000:]:break
            time.sleep(5)
        else:raise TimeoutError(mesh)
        errors=int(float((folder/'shape_errors.txt').read_text(encoding='utf-8-sig')))
        warnings=int(float((folder/'shape_warnings.txt').read_text(encoding='utf-8-sig')))
        target=out/('native_shape_'+mesh+'.out');shutil.copy2(log,target)
        records[mesh]=dict(status='PASS_NATIVE_SHAPE_ERROR_LIMITS' if errors==0 else 'BLOCKED_NATIVE_SHAPE_ERRORS',
            error_elements=errors,warning_elements=warnings,input_source=str(source),
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),audit_input_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
            method='SHPP DEFAULT + ON, CHECK ESEL ERR / WARN, all SOLID278; unchanged native default limits; no thermal solve and no mesh edits')
        (out/'native_shape_checks.json').write_text(json.dumps(records,indent=2)+'\n');print(mesh,records[mesh],flush=True)
if __name__=='__main__':main()
