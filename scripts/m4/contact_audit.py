"""Read native contact heat rates; never assume missing output means zero.

CONTA174 NMISC98 is CNFH [W], positive into the source contact surface.
DPF 7.1 generic miscellaneous units are retained separately from native units.
"""
import argparse,csv,json,os,re
from pathlib import Path
import numpy as np
from export_native_brake import ROOT,RUN

def contact_groups(path):
    text=path.read_text();starts=list(re.finditer(r'Create Contact "(S3_[^"]+)"',text));groups={}
    for j,m in enumerate(starts):
        part=text[m.end():starts[j+1].start() if j+1<len(starts) else len(text)]
        cid=int(re.search(r'\*set,cid,(\d+)',part)[1]);tid=int(re.search(r'\*set,tid,(\d+)',part)[1]);ids={};block=False
        for line in part.splitlines():
            if line.lower().startswith('eblock,10'):block=True;continue
            if block and line.strip()=='-1':block=False
            if block:
                values=line.split()
                if len(values)>=9 and all(v.lstrip('-').isdigit() for v in values):
                    v=list(map(int,values))
                    # Blank EBLOCK format: element, TYPE, REAL, MAT, ESYS, nodes.
                    # Program-controlled asymmetric contact can keep either
                    # branch. Reverse-side contact uses real=tid and its local
                    # positive heat flow is already into the original target.
                    if v[1]==cid:ids[v[0]]=(-1 if v[2]==cid else 1)
        assert ids,m[1];groups[m[1]]=dict(elements=ids,cid=cid,tid=tid)
    assert len(groups)==32;return groups

def main():
    p=argparse.ArgumentParser();p.add_argument('study');a=p.parse_args();folder=RUN/'studies'/a.study;out=ROOT/'results/m4/studies'/a.study
    log=(folder/'study.out').read_text(errors='replace');assert 'RUN COMPLETED' in log
    groups=contact_groups(folder/'study.dat');os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    try:
        model=dpf.Model(str(folder/'study.rth'),server=server);times=np.array(model.metadata.time_freq_support.time_frequencies.data)
        scope=dpf.Scoping(ids=[i for v in groups.values() for i in v['elements']],location='Elemental',server=server)
        def read(index,sets):
            return dpf.operators.result.nmisc(data_sources=model.metadata.data_sources,mesh_scoping=scope,
                time_scoping=sets,item_index=index,server=server).outputs.fields_container()
        area_fc=read(58,[1]);area_f=area_fc[0]
        area={int(i):float(v) for i,v in zip(area_f.scoping.ids,np.array(area_f.data,copy=True).ravel())}
        native_area={}
        for match in re.finditer(r'SUMMARY FOR CONTACT PAIR IDENTIFIED BY REAL CONSTANT SET\s+(\d+)([\s\S]*?)(?=SUMMARY FOR CONTACT PAIR|ELEMENT SOLUTION|SOLU|$)',log):
            value=re.search(r'Contacting area\s+([\d.Ee+\-]+)',match[2])
            if value:native_area[int(match[1])]=float(value[1].rstrip('.'))
        fc=read(98,list(range(1,len(times)+1)));records=[];coverage={}
        for j,f in enumerate(fc):
            ids=np.array(f.scoping.ids);data=np.array(f.data,copy=True).ravel()
            for name,definition in groups.items():
                wanted=definition['elements']
                mask=np.isin(ids,list(wanted));count=int(mask.sum())
                available=[int(i) for i in ids[mask]];branches=[s for s in [-1,1] if any(wanted[i]==s for i in available)]
                area_sum=sum(area.get(i,0) for i in available)
                real=definition['cid'] if branches==[-1] else definition['tid'] if branches==[1] else -1
                reference=native_area.get(real)
                error=abs(area_sum-reference)/reference if reference and reference>0 else None
                gap_film=name.startswith('S3_oil_inventory_to_')
                complete=len(branches)==1 and count>0 and all(i in area for i in available) and (
                    (gap_film and count==sum(s==branches[0] for s in wanted.values())) or
                    (error is not None and error<.001))
                q=float(sum(v*wanted[int(i)] for i,v in zip(ids[mask],data[mask])))
                coverage[name]=dict(expected_both_branches=len(wanted),reported_active_branch=count,
                    active_branch=('original_source' if branches==[-1] else 'original_target' if branches==[1] else 'unresolved'),
                    active_contact_area_m2=area_sum,native_log_area_m2=reference,area_relative_error=error,
                    interface_model='S3_PROJECTED_GAP_FILM; no closed-contact-area claim' if gap_film else 'S3_FINITE_SOLID_CONTACT',
                    complete_active_area_check=complete)
                records.append(dict(time_s=float(times[j]),interface=name,reported_elements=count,
                    expected_both_branches=len(wanted),source_to_target_W=q if complete else None,
                    available_subset_W=q,classification='S3_NATIVE_ASYMMETRIC_CONTACT_OUTPUT'))
        with (out/'contact_path_heat_rates.csv').open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
        oil_stored={float(r['time_s']):float(r['stored_energy_above_25C_J']) for r in csv.DictReader((out/'pilot_temperature_history.csv').open()) if r['part']=='M4_OIL_INVENTORY'}
        sources={}
        if (folder/'source_intervals.csv').exists():sources={float(r['time_s']):float(r['gear_other']) for r in csv.DictReader((folder/'source_intervals.csv').open())}
        oil_residual=[];integral=0.;prior=0.;throughput=0.
        for t in times:
            q=-sum(r['available_subset_W'] for r in records if r['time_s']==float(t) and r['interface'].startswith('S3_oil_inventory_to_'))
            generation=next((v for time,v in sources.items() if abs(time-t)<1e-7),0.)
            integral+=(q+generation)*(t-prior);throughput+=(abs(q)+abs(generation))*(t-prior);prior=t
            U=next(v for time,v in oil_stored.items() if abs(time-t)<1e-7);oil_residual.append(float(integral-U))
        oil_relative=max(abs(np.array(oil_residual)))/max(1.,throughput)
        passed=all(v['complete_active_area_check'] for v in coverage.values()) and oil_relative<.005
        status='PASS_NUMERICAL_CONTACT_CONNECTIVITY_NOT_CALIBRATION' if passed else 'BLOCKED_CONTACT_OUTPUT_OR_OIL_BALANCE'
        receipt=dict(status=status,coverage=coverage,native_quantity='CONTA174 CNFH NMISC98 W; sign reversed for source-to-target',
            generic_metadata_units=[f.unit for f in fc],missing_policy='null if active branch incomplete; no missing-to-zero substitution',
            oil_local_balance=dict(max_residual_J=max(abs(np.array(oil_residual))),relative_to_max_1J_or_throughput=oil_relative,tolerance=.005,
                definition='Oil FE storage equals internal source plus the two signed gap-film inputs; no ideal oil mixing or calibrated film claimed'),
            asymmetric_definition='KEYOPT(8)=2 program-controlled asymmetric. One branch is deactivated; some candidate facets are outside active overlap. Require reported CNFH facets to cover the native solver contacting area (0.1% tolerance), not all candidate facets. Reverse orientation for target-side branch.')
        (out/'contact_output_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
    finally:server.shutdown()

if __name__=='__main__':main()
