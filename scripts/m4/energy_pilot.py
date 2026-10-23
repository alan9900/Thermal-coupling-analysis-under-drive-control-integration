"""Actual whole-model FE balance with native boundary powers, not inferred losses.

SURF152 SMISC2 = signed input heat-flow or outward convection W depending
on KEYOPT8; SURF252 NMISC7 = outward net radiosity flux, NMISC4 = m2.
Preserve native generic SMISC unit metadata separately; never integrate J as W.
MKS quantities are explicitly interpreted using the native element definitions.
"""
import os,json,csv,argparse
from pathlib import Path
import numpy as np
from read_native_boundaries import surface_groups,ROOT,OUT,RUN
def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('--study',type=Path);a=ap.parse_args()
    result=RUN/'native_archive/B_wholebody/file.rth';input_path=RUN/'pilot_ds.dat'
    if a.study:
        result=a.study/'study.rth';input_path=a.study/'study.dat';OUT=ROOT/'results/m4/studies'/a.study.name
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    s=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    try:
        m=dpf.Model(str(result),server=s)
        times=np.array(m.metadata.time_freq_support.time_frequencies.data);sets=list(range(1,len(times)+1))
        groups,modes=surface_groups(input_path);lookup={i:k for k,ids in groups.items() for i in ids}
        sc=dpf.Scoping(ids=list(lookup),location='Elemental',server=s)
        fc=dpf.operators.result.smisc(data_sources=m.metadata.data_sources,mesh_scoping=sc,time_scoping=sets,item_index=2,server=s).outputs.fields_container()
        powers=np.zeros((len(times),len(groups)));types=list(groups)
        for j,f in enumerate(fc):
            ids=np.array(f.scoping.ids);values=np.array(f.data,copy=True).ravel()
            for k,typ in enumerate(types):powers[j,k]=values[np.isin(ids,groups[typ])].sum()
        print('Native input and convection read',len(fc),flush=True)
        apdl=m.metadata.meshed_region.property_field('apdl_element_type')
        sc=dpf.Scoping(ids=[int(i) for i,t in zip(apdl.scoping.ids,apdl.data) if int(t)==252],location='Elemental',server=s)
        area_fc=dpf.operators.result.nmisc(data_sources=m.metadata.data_sources,mesh_scoping=sc,time_scoping=[1],item_index=4,server=s).outputs.fields_container()
        area_f=area_fc[0];areas=dict(zip(map(int,area_f.scoping.ids),np.array(area_f.data,copy=True).ravel()))
        rad_fc=dpf.operators.result.nmisc(data_sources=m.metadata.data_sources,mesh_scoping=sc,time_scoping=sets,item_index=7,server=s).outputs.fields_container()
        rad=[]
        for f in rad_fc:
            vals=np.array(f.data,copy=True).ravel();rad.append(sum(areas[int(i)]*v for i,v in zip(f.scoping.ids,vals)))
        assert len(fc)==len(rad_fc)==len(times)
        print('Signed radiosity boundary read',flush=True)
        sources=powers[:,[k for k,t in enumerate(types) if modes[t]==1]].sum(axis=1)
        internal=np.zeros(len(times))
        if a.study and (a.study/'source_intervals.csv').is_file():
            source_rows=list(csv.DictReader((a.study/'source_intervals.csv').open()))
            ends=np.array([float(r['time_s']) for r in source_rows]);inside=np.array([float(r['internal_applied_W']) for r in source_rows])
            for k,t in enumerate(times):
                j=int(np.argmin(abs(ends-t)));assert abs(ends[j]-t)<1e-7
                internal[k]=inside[j]
            sources+=internal
        convection=powers[:,[k for k,t in enumerate(types) if modes[t]==2]].sum(axis=1)
        hist=list(csv.DictReader((OUT/'pilot_temperature_history.csv').open()))
        stored=np.array([sum(float(r['stored_energy_above_25C_J']) for r in hist if abs(float(r['time_s'])-t)<1e-8) for t in times])
        dt=np.diff(np.r_[0,times]);Ein=np.cumsum(sources*dt);Econv=np.cumsum(convection*dt);Erad=np.cumsum(np.array(rad)*dt)
        residual=Ein-stored-Econv-Erad
        scale=max(Ein[-1],1);relative=float(np.max(np.abs(residual))/scale)
        rows=[dict(time_s=float(t),input_W=float(q),convection_out_W=float(c),radiation_net_out_W=float(r),
            input_J=float(ei),stored_J=float(u),convection_out_J=float(ec),radiation_net_out_J=float(er),residual_J=float(res))
            for t,q,c,r,ei,u,ec,er,res in zip(times,sources,convection,rad,Ein,stored,Econv,Erad,residual)]
        with (OUT/'pilot_FE_energy_balance.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        receipt=dict(status='PASS_DIAGNOSTIC_DISCRETE_FE_BALANCE' if relative<.005 else 'BLOCKED_ENERGY_RESIDUAL',
            max_relative_residual=relative,tolerance=.005,final=rows[-1],SURF152_type_modes=modes,
            reported_SMISC_metadata_units=[f.unit for f in fc],interpretation='Native MKS HFCTOT is W per SURF152 definition; generic reader unit metadata retained.',
            quadrature='Backward Euler right endpoints consistent with native time integration; storage integral rho cp N_i dV.',
            physical_contact_scopes=('Explicit finite interface faces, S3 uncalibrated conductance' if a.study else 'Original whole-body diagnostic only; no physically validated coupling claim'),
            mesh_time_independence='NOT VALIDATED')
        (OUT/'pilot_FE_energy_checks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    finally:s.shutdown()
if __name__=='__main__':main()
