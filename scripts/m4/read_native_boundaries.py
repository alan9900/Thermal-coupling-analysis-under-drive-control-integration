"""Discover native SURF152 power and SURF252 records, preserving signed data."""
import os,re,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4';RUN=Path('E:/ansys_runs/m4_case0_20261021')
def surface_groups(path):
    et={};mode={};groups={};block=False
    with path.open() as f:
        for line in f:
            match=re.match(r'et,\s*(\d+),\s*(\d+)',line,re.I)
            if match:et[int(match[1])]=int(match[2])
            match=re.match(r'keyop,\s*(\d+),\s*8,\s*([12])',line,re.I)
            if match:mode[int(match[1])]=int(match[2])
            if line.lower().startswith('eblock,10'):block=True;continue
            if block and line.strip()=='-1':block=False;continue
            if not block:continue
            values=line.split()
            if len(values)<9 or not all(x.lstrip('-').isdigit() for x in values):continue
            v=list(map(int,values))
            if et.get(v[2])==152:groups.setdefault(v[2],[]).append(v[0])
    return groups,mode
def main():
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    s=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    try:
        m=dpf.Model(str(RUN/'native_archive/B_wholebody/file.rth'),server=s)
        groups,mode=surface_groups(RUN/'pilot_ds.dat');print('SURF152 groups',[(k,len(v),mode.get(k)) for k,v in groups.items()],flush=True)
        answers={}
        for typ,ids in groups.items():
            sc=dpf.Scoping(ids=ids,location='Elemental',server=s)
            fc=dpf.operators.result.smisc(data_sources=m.metadata.data_sources,mesh_scoping=sc,time_scoping=[46],item_index=2,server=s).outputs.fields_container()
            fields=[dict(ids=[int(i) for i in f.scoping.ids],values=np.array(f.data,copy=True).ravel().tolist(),unit=f.unit) for f in fc]
            answers[str(typ)]=dict(mode=mode.get(typ),requested=len(ids),fields=fields)
            print('SURF152',typ,[(len(r['values']),sum(r['values']),r['unit']) for r in fields],flush=True)
        prop=m.metadata.meshed_region.property_field('apdl_element_type')
        sc=dpf.Scoping(ids=[int(i) for i,t in zip(prop.scoping.ids,prop.data) if int(t)==252],location='Elemental',server=s)
        radiation={}
        for item in [4,5,6,7,8,9,10,11]:
            fc=dpf.operators.result.nmisc(data_sources=m.metadata.data_sources,mesh_scoping=sc,time_scoping=[46],item_index=item,server=s).outputs.fields_container()
            radiation[str(item)]=[dict(ids=[int(i) for i in f.scoping.ids],values=np.array(f.data,copy=True).ravel().tolist(),unit=f.unit) for f in fc]
            print('SURF252',item,[(len(r['values']),min(r['values']),max(r['values'])) for r in radiation[str(item)]],flush=True)
        (OUT/'native_boundary_discovery.json').write_text(json.dumps(dict(surf152=answers,surf252=radiation),indent=2)+'\n')
    finally:s.shutdown()
if __name__=='__main__':main()
