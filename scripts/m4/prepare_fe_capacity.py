"""Precompute true FE capacity weights, with independent element-volume checks."""
import os,json,sys,collections,argparse
from pathlib import Path
import numpy as np
from fe_capacity import weights
from dpf_regions import solid_regions
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4'
def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',type=Path,default=OUT);a=ap.parse_args();OUT=a.out;OUT.mkdir(parents=True,exist_ok=True)
    print('Starting FE capacity extraction',a.result,flush=True)
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    print('DPF server',server.version,flush=True)
    try:
        m=dpf.Model(a.result,server=server);mesh=m.metadata.meshed_region
        print('Native model mesh loaded',flush=True)
        xyz=np.array(mesh.nodes.coordinates_field.data);nodeids=np.array(mesh.nodes.scoping.ids);order=np.argsort(nodeids);sortedids=nodeids[order]
        config=json.loads((ROOT/'configs/m4_case0.json').read_text(encoding='utf-8'))
        regions=solid_regions(m);names=list(regions);which={};rhocp=[]
        print('Resolved solid regions',len(names),flush=True)
        for k,name in enumerate(names):
            for eid in regions[name]:which[int(eid)]=k
            mat=config['materials'][config['body_materials'][name[3:].lower()]];rhocp.append(mat['rho_kg_m3']*mat['cp_J_kgK'])
        apdl=mesh.property_field('apdl_element_type');solid=np.array(apdl.scoping.ids)[np.array(apdl.data)==278]
        pertype=collections.defaultdict(list);idsbytype=collections.defaultdict(list)
        with mesh.elements.connectivities_field.as_local_field() as conn:
            for eid in solid:
                c=np.array(conn.get_entity_data_by_id(int(eid)),dtype=int,copy=True)
                pertype[len(c)].append(c);idsbytype[len(c)].append(int(eid))
        capacity=np.zeros((len(names),len(xyz)));bodyvol=np.zeros(len(names));allids=[];allvol=[]
        for count,cells in pertype.items():
            cells=np.array(cells);assert count in [4,5,6,8],('Unsupported FE topology',count)
            for a in range(0,len(cells),30000):
                c=cells[a:a+30000];body=np.array([which[e] for e in idsbytype[count][a:a+30000]])
                w,v=weights(xyz[c]);allids.extend(idsbytype[count][a:a+30000]);allvol.extend(v)
                for k in np.unique(body):
                    select=body==k;np.add.at(capacity[k],c[select].ravel(),(w[select]*rhocp[k]).ravel());bodyvol[k]+=v[select].sum()
        # DPFArray views can outlive the native owner if passed through
        # np.asarray. Copy while both FieldsContainer and Field remain alive.
        fc=m.results.elemental_volume(time_scoping=[1]).eval();field=fc[0]
        volume_data=np.array(field.data,copy=True).ravel();volume_ids=list(field.scoping.ids)
        fv={int(i):float(v) for i,v in zip(volume_ids,volume_data)}
        errors=[abs(v-fv[i])/max(v,1e-30) for i,v in zip(allids,allvol)]
        assert max(errors)<1e-6,('FE quadrature differs from native element volume',max(errors))
        np.savez_compressed(OUT/'FE_capacity_weights.npz',node_ids=nodeids,weights_J_K=capacity,names=np.array(names),body_volumes_m3=bodyvol)
        receipt=dict(status='PASS_FE_CAPACITY_INTEGRATION_NOT_FULL_ENERGY_BALANCE',solid_elements=len(solid),topologies={str(k):len(v) for k,v in pertype.items()},
            max_native_volume_relative_error=max(errors),body_C_J_K={n:float(c.sum()) for n,c in zip(names,capacity)},body_volume_m3=dict(zip(names,bodyvol)),
            definition='Integral rho cp N_i dV; affine topology analytic tests, native element-volume cross-check; excludes contact/radiation ghost mass')
        (OUT/'FE_capacity_checks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    finally:server.shutdown()
if __name__=='__main__':main()
