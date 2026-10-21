"""Audit and plot completed baseline paths; wait for actual postprocessing."""
import argparse,subprocess,sys,time
from pathlib import Path
from export_native_brake import ROOT
def main():
    p=argparse.ArgumentParser();p.add_argument('studies',nargs='+');a=p.parse_args();left=list(a.studies)
    while left:
        for name in list(left):
            folder=ROOT/'results/m4/studies'/name
            if not (folder/'native_archive_manifest.json').exists():continue
            for script in ['contact_audit.py','extract_paths.py','export_component_fields.py','plot_component_fields.py']:
                interpreter=str(ROOT/'tmp/m3_cad/Scripts/python.exe') if script=='plot_component_fields.py' else sys.executable
                with (folder/(script+'.log')).open('w',encoding='utf-8') as stream:
                    subprocess.run([interpreter,str(ROOT/'scripts/m4'/script),name],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
                print(name,script,'completed',flush=True)
            left.remove(name)
        if left:time.sleep(10)
if __name__=='__main__':main()
