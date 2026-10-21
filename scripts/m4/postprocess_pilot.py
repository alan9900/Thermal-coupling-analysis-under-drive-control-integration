"""Read actual solved RTH with DPF; diagnostics never imply validation.

Use an ASCII Python environment path with DPF 7.1. The 2024 local server
uses legacy insecure gRPC on loopback only, not network access.
"""
import csv,hashlib,json,os,sys
import argparse
from pathlib import Path
import numpy as np
from dpf_regions import solid_regions
ROOT=Path(__file__).resolve().parents[2];RUN=Path('E:/ansys_runs/m4_case0_20261021');OUT=ROOT/'results/m4'
def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('--native-recovery',action='store_true');ap.add_argument('--study',type=Path)
    args=ap.parse_args();expected=None
    s=json.loads((RUN/'pilot_solve_state.json').read_text())
    if args.study:
        expected=json.loads((args.study/'study_settings.json').read_text());path=args.study/'study.rth'
        OUT=ROOT/'results/m4/studies'/args.study.name;OUT.mkdir(parents=True,exist_ok=True)
        log=(args.study/'study.out').read_text(errors='replace')
        assert 'RUN COMPLETED' in log and 'NUMBER OF ERROR   MESSAGES ENCOUNTERED=          0' in log
        s={'state':expected.get('Mechanical_state','EXTERNAL_NATIVE_RUN_COMPLETED_NOT_MECHANICAL_SOLVED')}
    elif args.native_recovery:
        # Mechanical's result transfer failed after native completion. Do not
        # relabel its SolveFailed state: prove native completion separately.
        path=RUN/'native_archive/B_wholebody/file.rth'
        log=(path.parent/'solve.out').read_text(errors='replace')
        assert 'RUN COMPLETED' in log and 'NUMBER OF ERROR   MESSAGES ENCOUNTERED=          0' in log
    else:
        assert s['state']=='Solved','No successful solve: refuse temperature extraction'
        path=Path(s['result_file'])
    assert path.is_file()
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    try:
        model=dpf.Model(str(path),server=server);mesh=model.metadata.meshed_region
        times=np.array(model.metadata.time_freq_support.time_frequencies.data)
        expected=expected or dict(json.loads((RUN/'pilot_source.json').read_text()),expected_sets=46)
        assert abs(times[-1]-expected['duration_s'])<1e-7 and len(times)==expected['expected_sets'],'Native result is incomplete'
        named=model.metadata.available_named_selections
        selected=[n for n in named if n.lower().startswith('m4_')]
        assert selected,'Actual body named selections missing'
        regions=solid_regions(model);groups={}
        for n,elems in regions.items():
            scope=dpf.Scoping(ids=elems.tolist(),location='Elemental',server=server)
            groups[n]=dpf.operators.scoping.transpose(mesh_scoping=scope,meshed_region=mesh,server=server).outputs.mesh_scoping_as_scoping()
        capacity=np.load(Path(expected.get('capacity_weights',ROOT/'results/m4/FE_capacity_weights.npz')))
        weight_names=capacity['names'].tolist();weight_ids=capacity['node_ids'];W=capacity['weights_J_K']
        rows=[];disc_peak=(-1e30,0)
        for k,time in enumerate(times,1):
            fc=model.results.temperature(time_scoping=[k]).eval();field=fc[0]
            ids=np.array(field.scoping.ids);T=np.array(field.data).reshape(-1);sort=np.argsort(ids);ids=ids[sort];T=T[sort]
            for n,scope in groups.items():
                scoped=np.array(scope.ids)
                idx=np.searchsorted(ids,scoped);valid=idx<len(ids);idx=idx[valid];scoped=scoped[valid];idx=idx[ids[idx]==scoped]
                assert len(idx),n
                vals=T[idx];j=np.searchsorted(ids,weight_ids);valid=j<len(ids)
                valid[valid]=ids[j[valid]]==weight_ids[valid]
                aligned=np.zeros(len(weight_ids));aligned[valid]=T[j[valid]]
                w=W[weight_names.index(n)];assert np.all(w[~valid]==0)
                rows.append(dict(time_s=float(time),part=n,minimum=float(vals.min()),maximum=float(vals.max()),
                    nodal_arithmetic_mean=float(vals.mean()),capacity_weighted_mean=float(w@aligned/w.sum()),
                    stored_energy_above_25C_J=float(w@(aligned-25)),temperature_unit=field.unit,
                    classification='ACTUAL_FE_DIAGNOSTIC_NOT_VALIDATED'))
                if n=='M4_BRAKE_DISC_HAT' and vals.max()>disc_peak[0]:disc_peak=(float(vals.max()),k)
        with (OUT/'pilot_temperature_history.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        # Actual surface triangles and actual FE nodal field for a scientific plot.
        # Only the physical disc solid; contact, target and radiosity ghost
        # elements must never become the temperature plot skin.
        disc_scope=dpf.Scoping(ids=regions['M4_BRAKE_DISC_HAT'].tolist(),location='Elemental',server=server)
        disc_mesh=dpf.operators.mesh.from_scoping(scoping=disc_scope,mesh=mesh,server=server).outputs.mesh()
        skin=dpf.operators.mesh.skin(mesh=disc_mesh,server=server).outputs.mesh()
        points=np.array(skin.nodes.coordinates_field.data);point_ids=np.array(skin.nodes.scoping.ids)
        tri=[]
        for e in skin.elements:
            c=list(e.connectivity)
            if len(c)==3:tri.append(c)
            elif len(c)==4:tri.extend([[c[0],c[1],c[2]],[c[0],c[2],c[3]]])
            else:raise ValueError('Unimplemented skin topology: '+str(len(c)))
        field=model.results.temperature(time_scoping=[disc_peak[1]]).eval()[0]
        ids=np.array(field.scoping.ids);vals=np.array(field.data).reshape(-1);sort=np.argsort(ids);ids=ids[sort];vals=vals[sort]
        idx=np.searchsorted(ids,point_ids);assert np.all(idx<len(ids)) and np.all(ids[idx]==point_ids)
        np.savez_compressed(OUT/'pilot_actual_FE_surface.npz',points=points,triangles=np.array(tri),temperature=vals[idx],time_s=times[disc_peak[1]-1])
        receipt=dict(status='ACTUAL_RTH_READ_DIAGNOSTIC_ONLY',server=server.version,result_file=str(path),result_bytes=path.stat().st_size,
            sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),time_points=len(times),first_time_s=float(times[0]),last_time_s=float(times[-1]),
            temperature_unit=field.unit,named_selections=selected,mesh_nodes=mesh.nodes.n_nodes,mesh_elements=mesh.elements.n_elements,
            FE_energy_balance='NOT VALIDATED',mesh_independence='NOT VALIDATED',time_step_independence='NOT VALIDATED',
            mean_definition='Both arithmetic and integral(rho cp T dV)/integral(rho cp dV); actual FE capacity weights, not CAD volume')
        receipt['Mechanical_original_state']=s['state']
        receipt['native_recovery']=args.native_recovery
        (OUT/'pilot_postprocessing.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    finally:server.shutdown()
if __name__=='__main__':main()
