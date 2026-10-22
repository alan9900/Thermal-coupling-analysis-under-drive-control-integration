"""Native zero-source probe: actual new mesh volumes, shape audit and equilibrium."""
import hashlib,json,re
from pathlib import Path
from export_native_brake import ROOT,RUN

def prepare(mesh):
    original=RUN/'mesh_variants'/('mesh_'+mesh)/'mechanical_ds.dat'
    text=original.read_text(encoding='utf-8-sig');first=re.search(r'^solve\s*$',text,re.M|re.I);assert first
    name='probe_'+mesh+'_base';folder=RUN/'studies'/name;folder.mkdir(exist_ok=False)
    commands=['finish','/prep7','allsel','esel,s,ename,,278','shpp,default','shpp,on','check,esel,err',
        '*get,N_BAD,elem,0,count','*cfopen,shape_errors,txt','*vwrite,N_BAD','(F12.0)','*cfclos',
        'allsel','esel,s,ename,,278','check,esel,warn','*get,N_WARN,elem,0,count',
        '*cfopen,shape_warnings,txt','*vwrite,N_WARN','(F12.0)','*cfclos','allsel','finish','/solu',
        'allsel','bfedele,all,hgen']
    for typ in [95,96,97,98]:commands+=['allsel','esel,s,type,,%d'%typ,'nsle','sf,all,hflux,0']
    commands+=['allsel','esel,s,ename,,152','esel,a,ename,,252','esel,a,ename,,174','cm,M4_BC_RECORDS,elem','allsel',
        'outres,erase','outres,all,none','outres,nsol,all','outres,veng,all','outres,cont,all','outres,misc,all,M4_BC_RECORDS',
        'deltim,1,1,1','time,1','solve','finish','/exit,nosa']
    path=folder/'study.dat';path.write_text(text[:first.start()]+'\n'+'\n'.join(commands)+'\n',encoding='utf-8')
    meta=dict(case='ZERO_SOURCE_'+mesh,classification='NUMERICAL_EQUILIBRIUM_CHECK_NOT_CALIBRATION',
        status='GENERATED_NOT_EXECUTED',duration_s=1,expected_sets=1,source_energy_J=[0,0],
        original_input=str(original),original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
        capacity_weights=str(ROOT/'results/m4/studies'/('probe_'+mesh)/'FE_capacity_weights.npz'))
    (folder/'study_settings.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    return name

if __name__=='__main__':
    import sys
    print(prepare(sys.argv[1]))
