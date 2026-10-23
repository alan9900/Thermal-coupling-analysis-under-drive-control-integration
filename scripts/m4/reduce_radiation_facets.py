"""Native RSURF decimation, separately verified from solid-mesh refinement.

Never relabel this as unchanged radiation geometry. Preserve the un-decimated
inputs/results and quantify the temperature and integrated-flux differences.
"""
import argparse,hashlib,json,re,shutil
from export_native_brake import RUN,ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('name');p.add_argument('--reduction',type=float,default=.95)
    a=p.parse_args();assert a.reduction in [.9,.95];base=RUN/'studies'/a.base;folder=RUN/'studies'/a.name
    folder.mkdir(exist_ok=False);text=(base/'study.dat').read_text(encoding='utf-8-sig')
    # The finely tessellated annulus decimates successfully. The already
    # coarse case face contains small holes; decimating it triggered a native
    # "Critical topology breaking" error. Preserve it without decimation.
    def decimate(match):
        line=match[1];assert ',,,101' in line or ',,,102' in line
        reduction=a.reduction if ',,,101' in line else 0.
        return 'rdec,define,%.12g\n'%reduction+line
    text,n=re.subn(r'^(RSURF[^\n]*)$',decimate,text,flags=re.M|re.I);assert n==2
    text=re.sub(r'^vfopt,read[^\n]*\n','',text,flags=re.M|re.I)
    needle='esel,a,ename,,252\ncm,M4_BC_RECORDS,elem'
    text=text.replace(needle,'esel,a,ename,,252\nesel,a,ename,,174\ncm,M4_BC_RECORDS,elem')
    if a.name.endswith(('dt2','dt4')):text=text.replace('outres,fflux,all','outres,fflux,none')
    first=re.search(r'^solve\s*$',text,re.M|re.I);assert first
    text=text[:first.start()]+'! Tight heat-flow tolerance; retain documented native radiosity flux tolerance\ncnvtol,heat,,1.e-6\nradopt,,1.e-4\n'+text[first.start():]
    (folder/'study.dat').write_text(text)
    if (base/'source_intervals.csv').exists():shutil.copy2(base/'source_intervals.csv',folder/'source_intervals.csv')
    m=json.loads((base/'study_settings.json').read_text(encoding='utf-8-sig'));m.pop('viewfactor_reuse_from',None);m.pop('viewfactor_reuse_condition',None)
    m.update(radiation_reduction=a.reduction,case_radiation_reduction=0.,nonlinear_heat_tolerance=1e-6,radiosity_flux_tolerance=1e-4,
        derived_from=str(base),parent_input_sha256=hashlib.sha256((base/'study.dat').read_bytes()).hexdigest(),derived_input_sha256=hashlib.sha256((folder/'study.dat').read_bytes()).hexdigest(),
        status='GENERATED_NOT_EXECUTED',capacity_weights=str(ROOT/'results/m4/studies'/a.name/'FE_capacity_weights.npz'),
        radiation_change='Native RDEC applied to disc RSURF101 only; case RSURF102 un-decimated. Solid mesh, heat sources, TCC and cooling unchanged. Requires independent facet-reduction error check.')
    (folder/'study_settings.json').write_text(json.dumps(m,indent=2)+'\n');print(folder)

if __name__=='__main__':main()
