"""Read actual solved RTH with DPF; diagnostics never imply validation.

Use an ASCII Python environment path with DPF 7.1. The 2024 local server
uses legacy insecure gRPC on loopback only, not network access.
"""
import csv,hashlib,json,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];RUN=Path('E:/ansys_runs/m4_case0_20261021');OUT=ROOT/'results/m4'
def main():
    s=json.loads((RUN/'pilot_solve_state.json').read_text())
    assert s['state']=='Solved','No successful solve: refuse temperature extraction'
    path=Path(s['result_file']);assert path.is_file()
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    try:
        model=dpf.Model(str(path),server=server);mesh=model.metadata.meshed_region
        times=np.array(model.metadata.time_freq_support.time_frequencies.data)
        named=model.metadata.available_named_selections
        selected=[n for n in named if n.lower().startswith('m4_')]
        assert selected,'Actual body named selections missing'
        groups={n:model.metadata.named_selection(n) for n in selected}
        rows=[]
        for k,time in enumerate(times,1):
            fc=model.results.temperature(time_scoping=[k]).eval();field=fc[0]
            ids=np.array(field.scoping.ids);T=np.array(field.data).reshape(-1);sort=np.argsort(ids);ids=ids[sort];T=T[sort]
            for n,scope in groups.items():
                scoped=np.array(scope.ids)
                idx=np.searchsorted(ids,scoped);valid=idx<len(ids);idx=idx[valid];scoped=scoped[valid];idx=idx[ids[idx]==scoped]
                assert len(idx),n
                vals=T[idx];rows.append(dict(time_s=float(time),part=n,minimum=float(vals.min()),maximum=float(vals.max()),
                    nodal_arithmetic_mean=float(vals.mean()),temperature_unit=field.unit,classification='ACTUAL_FE_DIAGNOSTIC_NOT_VALIDATED'))
        with (OUT/'pilot_temperature_history.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        # Actual surface triangles and actual FE nodal field for a scientific plot.
        skin=dpf.operators.mesh.skin(mesh=mesh,server=server).outputs.mesh()
        points=np.array(skin.nodes.coordinates_field.data);point_ids=np.array(skin.nodes.scoping.ids)
        tri=[]
        for e in skin.elements:
            c=list(e.connectivity)
            if len(c)==3:tri.append(c)
            elif len(c)==4:tri.extend([[c[0],c[1],c[2]],[c[0],c[2],c[3]]])
            else:raise ValueError('Unimplemented skin topology: '+str(len(c)))
        ids=np.array(field.scoping.ids);vals=np.array(field.data).reshape(-1);sort=np.argsort(ids);ids=ids[sort];vals=vals[sort]
        idx=np.searchsorted(ids,point_ids);assert np.all(idx<len(ids)) and np.all(ids[idx]==point_ids)
        np.savez_compressed(OUT/'pilot_actual_FE_surface.npz',points=points,triangles=np.array(tri),temperature=vals[idx])
        receipt=dict(status='ACTUAL_RTH_READ_DIAGNOSTIC_ONLY',server=server.version,result_file=str(path),result_bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),time_points=len(times),first_time_s=float(times[0]),last_time_s=float(times[-1]),
            temperature_unit=field.unit,named_selections=selected,mesh_nodes=mesh.nodes.n_nodes,mesh_elements=mesh.elements.n_elements,
            FE_energy_balance='NOT VALIDATED',mesh_independence='NOT VALIDATED',time_step_independence='NOT VALIDATED',
            mean_definition='Nodal arithmetic mean, not volume-weighted mean or stored energy')
        (OUT/'pilot_postprocessing.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    finally:server.shutdown()
if __name__=='__main__':main()
