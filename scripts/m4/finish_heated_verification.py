"""Finish coupled-source verification after current jobs, without geometry edits."""
import csv,json,os,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime
from export_native_brake import ROOT,RUN
from post_completed_studies import process

PY=str(ROOT/'tmp/m3_cad/Scripts/python.exe')
def command(script,*args):
    subprocess.run([sys.executable,str(ROOT/'scripts/m4'/script),*map(str,args)],cwd=ROOT,check=True)
def native(name):
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(RUN/'run_native_studies.ps1'),'-Cases',name,'-Cores','4'],check=True)

def main():
    required=['A_normal12_rd95_dt1_retry1','B_normal12_rd95h_dt4_retry1',
        'C_normal12_rd95_contact_high','C_normal12_rd95_cooling_low','C_normal12_rd95_cooling_high']
    while not all((ROOT/'results/m4/studies'/n/'native_archive_manifest.json').exists() for n in required):time.sleep(10)
    print('Existing interrupted tasks complete; starting heated-region mesh verification',flush=True)
    for file in ['mechanical_heated_mesh.py','run_heated_mesh.wbjn']:
        shutil.copy2(ROOT/'scripts/m4'/file,RUN/file)
    wb='E:/Program Files/ANSYS Inc/v241/Framework/bin/Win64/runwb2.bat'
    result=subprocess.run(['cmd.exe','/c',wb,'-B','-R',str(RUN/'run_heated_mesh.wbjn')],cwd=RUN)
    for mesh in ['global14','global7']:
        folder=RUN/'mesh_variants'/('mesh_'+mesh)
        assert (folder/'input_export_complete.json').exists(),'Actual Mechanical mesh/export incomplete: '+mesh
        dest=ROOT/'results/m4/meshes'/('mesh_'+mesh);dest.mkdir(exist_ok=False)
        for file in ['mesh_audit.json','input_export_complete.json','actual_mesh.png']:shutil.copy2(folder/file,dest/file)
    print('Actual global14/global7 meshes exported',flush=True)
    from export_zero_probe import prepare as probe
    from reuse_view_factors import prepare as reuse
    for mesh in ['global14','global7']:
        base=probe(mesh);name='probe_'+mesh
        command('reduce_radiation_facets.py',base,name,'--reduction','.95')
        native(name);process(name)
        folder=ROOT/'results/m4/studies'/name
        errors=int(float((RUN/'studies'/name/'shape_errors.txt').read_text()))
        warnings=int(float((RUN/'studies'/name/'shape_warnings.txt').read_text()))
        assert errors==0,'Native default shape-error limit failed'
        rows=list(csv.DictReader((folder/'pilot_temperature_history.csv').open()))
        maximum=max(max(abs(float(r['minimum'])-25),abs(float(r['maximum'])-25)) for r in rows)
        assert maximum<1e-5,('No-source equilibrium failed',maximum)
        (folder/'zero_source_checks.json').write_text(json.dumps(dict(status='PASS_NATIVE_ZERO_SOURCE_AND_SHAPE',
            max_temperature_deviation_K=maximum,error_elements=errors,warning_elements=warnings,
            scope='All physical regions remain at 25C; not a convection-cooling experiment.'),indent=2)+'\n')
        base='C_'+mesh+'_base';source='C_'+mesh+'_rd95_dt1'
        command('export_native_sources.py','--case','C','--name',base,'--input',RUN/'mesh_variants'/('mesh_'+mesh)/'mechanical_ds.dat',
            '--capacity-json',folder/'FE_capacity_checks.json')
        command('reduce_radiation_facets.py',base,source,'--reduction','.95');reuse(name,[source])
    from refine_same_source_time import prepare as time_case
    time_name=time_case()
    # Conservative memory use: the finest heated-region mesh runs alone.
    for source in ['C_global14_rd95_dt1',time_name,'C_global7_rd95_dt1']:
        print('Running coupled verification',source,flush=True);native(source);process(source)
    print('All heated-source verification runs completed; acceptance remains separate',flush=True)

if __name__=='__main__':main()
