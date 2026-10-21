"""Signed heat-path cuts plus a separate drive-subassembly energy balance.

Do not sum serial shaft/bearing sections. The brake/drive cut has two solid
connections: sleeve-to-shaft and bracket-to-case. Native case net radiosity
also contains the open-enclosure boundary; it is not pure mutual exchange.
"""
import argparse,csv,json,os,re
from pathlib import Path
import numpy as np
from export_native_brake import ROOT,RUN
from read_native_boundaries import surface_groups
from dpf_regions import solid_regions

BRAKE={'M4_BRAKE_DISC_HAT','M4_DISC_HUB','M4_HUB_REMOVABLE_SLEEVE','M4_CALIPER','M4_CALIPER_REACTION_BRACKET','M4_PAD_NEAR','M4_PAD_FAR'}

def main():
    p=argparse.ArgumentParser();p.add_argument('study');a=p.parse_args();folder=RUN/'studies'/a.study;out=ROOT/'results/m4/studies'/a.study
    audit=json.loads((out/'contact_output_audit.json').read_text(encoding='utf-8-sig'));assert audit['status'].startswith('PASS_'),'Unverified contact extraction'
    contacts=list(csv.DictReader((out/'contact_path_heat_rates.csv').open()));hist=list(csv.DictReader((out/'pilot_temperature_history.csv').open()))
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    try:
        model=dpf.Model(str(folder/'study.rth'),server=server);mesh=model.metadata.meshed_region;regions=solid_regions(model)
        times=np.array(model.metadata.time_freq_support.time_frequencies.data);sets=list(range(1,len(times)+1))
        drive_nodes=set();brake_nodes=set()
        for name,ids in regions.items():
            scope=dpf.Scoping(ids=ids.tolist(),location='Elemental',server=server)
            nodes=dpf.operators.scoping.transpose(mesh_scoping=scope,meshed_region=mesh,server=server).outputs.mesh_scoping_as_scoping()
            (brake_nodes if name in BRAKE else drive_nodes).update(map(int,nodes.ids))
        groups,modes=surface_groups(folder/'study.dat');ambient=groups[99];coolant=groups[100];drive_ambient=set();brake_ambient=set()
        # DPF's RTH mesh omits SURF152 load elements although their MISC
        # results are available. Read their original node IDs from EBLOCK;
        # do not invent geometry for an absent DPF mesh element.
        boundary_nodes={};block=False;ambient_ids=set(ambient)
        for line in (folder/'study.dat').open():
            if line.lower().startswith('eblock,10'):block=True;continue
            if block and line.strip()=='-1':block=False;continue
            if block:
                values=line.split()
                if len(values)>=9 and all(v.lstrip('-').isdigit() for v in values):
                    v=list(map(int,values))
                    if v[0] in ambient_ids:boundary_nodes[v[0]]=set(v[5:])-{0}
        assert set(boundary_nodes)==set(ambient)
        for eid in ambient:
            nodes=boundary_nodes[eid]
            if nodes.issubset(drive_nodes):drive_ambient.add(eid)
            elif nodes.issubset(brake_nodes):brake_ambient.add(eid)
            else:raise ValueError('Ambiguous convection face '+str(eid))
        assert len(drive_ambient)+len(brake_ambient)==len(ambient)
        scope=dpf.Scoping(ids=ambient+coolant,location='Elemental',server=server)
        fc=dpf.operators.result.smisc(data_sources=model.metadata.data_sources,mesh_scoping=scope,time_scoping=sets,item_index=2,server=server).outputs.fields_container()
        boundary=[]
        for f in fc:
            ids=np.array(f.scoping.ids);data=np.array(f.data,copy=True).ravel()
            boundary.append((data[np.isin(ids,list(drive_ambient))].sum(),data[np.isin(ids,list(brake_ambient))].sum(),data[np.isin(ids,coolant)].sum()))
        prop=mesh.property_field('apdl_element_type');radids=[int(i) for i,t in zip(prop.scoping.ids,prop.data) if int(t)==252]
        rs=dpf.Scoping(ids=radids,location='Elemental',server=server)
        def misc(index,which):return dpf.operators.result.nmisc(data_sources=model.metadata.data_sources,mesh_scoping=rs,time_scoping=which,item_index=index,server=server).outputs.fields_container()
        area_fc=misc(4,[1]);area_f=area_fc[0];areas=dict(zip(map(int,area_f.scoping.ids),np.array(area_f.data,copy=True).ravel()))
        eps_fc=misc(6,[1]);eps_f=eps_fc[0];eps=dict(zip(map(int,eps_f.scoping.ids),np.array(eps_f.data,copy=True).ravel()))
        assert all(min(abs(v-.7),abs(v-.8))<1e-6 for v in eps.values())
        radfc=misc(7,sets);rad=[]
        for f in radfc:
            data=np.array(f.data,copy=True).ravel()
            rad.append(tuple(sum(areas[int(i)]*v for i,v in zip(f.scoping.ids,data) if abs(eps[int(i)]-e)<1e-6) for e in [.7,.8]))
        source=[]
        if (folder/'source_intervals.csv').exists():source=list(csv.DictReader((folder/'source_intervals.csv').open()))
        rows=[]
        for j,t in enumerate(times):
            def q(name):
                r=next(r for r in contacts if r['interface']=='S3_'+name and abs(float(r['time_s'])-t)<1e-8)
                assert r['source_to_target_W']!='';return float(r['source_to_target_W'])
            stored=sum(float(r['stored_energy_above_25C_J']) for r in hist if r['part'] not in BRAKE and abs(float(r['time_s'])-t)<1e-8)
            generated=next((float(r['internal_applied_W']) for r in source if abs(float(r['time_s'])-t)<1e-7),0.)
            shaft=q('hub_removable_sleeve_to_output_shaft');bracket=-q('gear_case_rear_to_caliper_reaction_bracket')
            rows.append(dict(time_s=float(t),shaft_cut_into_drive_W=shaft,bracket_cut_into_drive_W=bracket,
                bearing2_serial_shaft_to_bearing_W=q('output_shaft_to_output_bearing_2'),
                bearing2_serial_bearing_to_case_W=q('output_bearing_2_to_gear_case_rear'),
                solid_cut_into_drive_W=shaft+bracket,radiation_net_into_case_W=float(-rad[j][0]),
                radiation_disc_net_out_W=float(rad[j][1]),ambient_drive_out_W=float(boundary[j][0]),
                ambient_brake_out_W=float(boundary[j][1]),coolant_out_W=float(boundary[j][2]),internal_source_W=generated,drive_stored_J=stored))
        integral={};previous=0
        paths=['shaft_cut_into_drive','bracket_cut_into_drive','solid_cut_into_drive','radiation_net_into_case','ambient_drive_out','ambient_brake_out','coolant_out','internal_source']
        for r in rows:
            dt=r['time_s']-previous;previous=r['time_s']
            for path in paths:
                for mode,power in [('net',r[path+'_W']),('positive',max(r[path+'_W'],0))]:
                    key=path+'_'+mode+'_J';integral[key]=integral.get(key,0)+dt*power;r[key]=integral[key]
            r['drive_balance_residual_J']=r['internal_source_net_J']+r['solid_cut_into_drive_net_J']+r['radiation_net_into_case_net_J']-r['ambient_drive_out_net_J']-r['coolant_out_net_J']-r['drive_stored_J']
        with (out/'signed_heat_paths.csv').open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        scale=max(1.,sum(abs(rows[-1][k+'_net_J']) for k in ['internal_source','solid_cut_into_drive','radiation_net_into_case']))
        error=max(abs(r['drive_balance_residual_J']) for r in rows)/scale
        receipt=dict(status='PASS_DRIVE_SUBASSEMBLY_DISCRETE_BALANCE' if error<.005 else 'BLOCKED_DRIVE_SUBASSEMBLY_BALANCE',
            relative_residual=error,tolerance=.005,final=rows[-1],ambient_face_counts=dict(drive=len(drive_ambient),brake=len(brake_ambient)),
            cut_definition='Sleeve/shaft plus bracket/case only. Bearing sections are serial diagnostic flows, never added as extra inputs.',
            radiation='Net into case includes the open enclosure; not pure disc-to-case mutual exchange.',
            hot_air_path='NOT MODELLED; not a physical zero',classification='S3_ACTUAL_ANSYS_NOT_CALIBRATED')
        (out/'heat_path_checks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    finally:server.shutdown()

if __name__=='__main__':main()
