"""Actual component surface FE temperatures at each component's peak set."""
import argparse,csv,json,os
from pathlib import Path
import numpy as np
from export_native_brake import RUN,ROOT
from dpf_regions import solid_regions

PARTS=['BRAKE_DISC_HAT','OUTPUT_BEARING_2','GEAR_CASE_REAR','OIL_INVENTORY','MOTOR_WINDING','PAD_NEAR']
def main():
    ap=argparse.ArgumentParser();ap.add_argument('study');a=ap.parse_args()
    folder=RUN/'studies'/a.study;out=ROOT/'results/m4/studies'/a.study
    assert (out/'native_archive_manifest.json').exists(),'Only completed, postprocessed results'
    hist=list(csv.DictReader((out/'pilot_temperature_history.csv').open()))
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    receipt=[]
    try:
        m=dpf.Model(str(folder/'study.rth'),server=server);mesh=m.metadata.meshed_region
        regions=solid_regions(m);times=np.array(m.metadata.time_freq_support.time_frequencies.data,copy=True)
        for part in PARTS:
            name='M4_'+part;rows=[r for r in hist if r['part']==name]
            peak=max(rows,key=lambda r:float(r['maximum']));time=float(peak['time_s']);k=int(np.argmin(abs(times-time)))+1
            scope=dpf.Scoping(ids=regions[name].tolist(),location='Elemental',server=server)
            body=dpf.operators.mesh.from_scoping(scoping=scope,mesh=mesh,server=server).outputs.mesh()
            skin=dpf.operators.mesh.skin(mesh=body,server=server).outputs.mesh()
            points=np.array(skin.nodes.coordinates_field.data,copy=True);ids=np.array(skin.nodes.scoping.ids)
            tri=[]
            with skin.elements.connectivities_field.as_local_field() as connections:
                for eid in skin.elements.scoping.ids:
                    c=list(connections.get_entity_data_by_id(int(eid)))
                    if len(c)==3:tri.append(c)
                    elif len(c)==4:tri.extend([[c[0],c[1],c[2]],[c[0],c[2],c[3]]])
                    else:raise ValueError('Unsupported surface topology')
            fc=m.results.temperature(time_scoping=[k]).eval();f=fc[0]
            nids=np.array(f.scoping.ids);values=np.array(f.data,copy=True).ravel()
            order=np.argsort(nids);nids=nids[order];values=values[order]
            idx=np.searchsorted(nids,ids);assert np.all(idx<len(nids)) and np.all(nids[idx]==ids)
            path=out/(part+'_peak_field.npz')
            np.savez_compressed(path,points=points,triangles=np.array(tri),temperature=values[idx],time_s=time)
            receipt.append(dict(part=name,time_s=time,volume_nodal_max_C=float(peak['maximum']),surface_max_C=float(values[idx].max()),
                coordinates='m',temperature='degC',result_set=k,file=path.name,
                classification='ACTUAL_RTH_FE_FIELD_S3; numerical qualification separate, not measured temperature'))
            print('Actual field exported',name,flush=True)
        (out/'component_field_checks.json').write_text(json.dumps({'status':'ACTUAL_FE_SURFACES_EXPORTED','components':receipt},indent=2)+'\n')
    finally:server.shutdown()

if __name__=='__main__':main()
