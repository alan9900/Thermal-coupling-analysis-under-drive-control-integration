"""Reuse native binary view factors only for the identical generated geometry.

This changes neither radiation facets nor emissivity. The solver independently
checks the loaded matrix. Do not reuse between mesh variants or CAD cases.
"""
import argparse,json,re
from export_native_brake import RUN

def prepare(source, targets):
    base=RUN/'studies'/source;sm=json.loads((base/'study_settings.json').read_text())
    for target in targets:
        folder=RUN/'studies'/target;assert not (folder/'study.out').exists(),'Never edit an executing or archived input'
        m=json.loads((folder/'study_settings.json').read_text())
        assert m['original_sha256']==sm['original_sha256'],'Original Mechanical geometry input must be identical'
        path=folder/'study.dat';text=path.read_text();assert 'vfopt,read' not in text.lower()
        match=re.search(r'^solve\s*$',text,re.M|re.I);assert match
        command="! Identical geometry/facets: read previously computed native binary view factors\nvfopt,read,'"+str(base/'study').replace('\\','/')+"',vf\n"
        text=text[:match.start()]+command+text[match.start():];path.write_text(text)
        m['viewfactor_reuse_from']=str(base);m['viewfactor_reuse_condition']='Same original Mechanical input SHA; native complete zero-error source required before execution'
        (folder/'study_settings.json').write_text(json.dumps(m,indent=2)+'\n');print('Prepared view-factor reuse',target,'from',source)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('targets',nargs='+');a=p.parse_args();prepare(a.source,a.targets)
