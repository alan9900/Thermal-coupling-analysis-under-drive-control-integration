"""Summaries from actual CSVs and receipts; pending runs never count as passes."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4';STUDIES=OUT/'studies'

def load(name):
    path=STUDIES/name/'pilot_temperature_history.csv'
    if not path.exists():return None
    rows=list(csv.DictReader(path.open()));receipt=STUDIES/name/'pilot_postprocessing.json'
    if not receipt.exists():return None
    expected=json.loads((STUDIES/name/'study_settings.json').read_text())
    assert len(set(r['time_s'] for r in rows))==expected['expected_sets']
    return rows

def series(rows,part,key):
    r=[x for x in rows if x['part']==part]
    return np.r_[0,[float(x['time_s']) for x in r]],np.r_[25,[float(x[key]) for x in r]]

def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','figure.dpi':150,'font.size':9})
    summaries=[]
    for folder in sorted(STUDIES.iterdir()):
        rows=load(folder.name)
        if rows is None:continue
        for name in sorted(set(r['part'] for r in rows)):
            r=[x for x in rows if x['part']==name];peak=max(r,key=lambda x:float(x['maximum']))
            summaries.append(dict(study=folder.name,part=name,peak_C=float(peak['maximum']),peak_time_s=float(peak['time_s']),
                peak_capacity_mean_C=max(float(x['capacity_weighted_mean']) for x in r),
                final_local_max_C=float(r[-1]['maximum']),final_capacity_mean_C=float(r[-1]['capacity_weighted_mean']),
                classification='ACTUAL_ANSYS_S3_CONCEPT; convergence in separate receipt'))
    write_csv(OUT/'all_study_temperature_summary.csv',summaries)
    groups={'mesh':['B_normal6_dt1','B_normal12_dt1_retry1','B_normal24_rd95h_dt1'],
            'time':['B_normal12_rd95h_dt1','B_normal12_rd95h_dt2','B_normal12_rd95h_dt4']}
    policy=json.loads((ROOT/'configs/M4_validation_policy.json').read_text());checks={}
    for label,names in groups.items():
        data=[load(name) for name in names]
        if any(r is None for r in data):
            checks[label]=dict(status='PENDING',required=names,available=[n for n,r in zip(names,data) if r is not None]);continue
        comparison=[]
        for part in sorted(set(r['part'] for r in data[-1])):
            for key,setting in [('maximum','peak_temperature_difference'),('capacity_weighted_mean','capacity_mean_temperature_difference')]:
                values=[max(float(r[key]) for r in rows if r['part']==part) for rows in data]
                limit=max(policy[setting]['absolute_floor_K'],policy[setting]['fraction_of_reference_rise']*abs(values[-1]-25))
                delta=abs(values[-1]-values[-2]);comparison.append(dict(part=part,metric=key,coarse_C=values[0],medium_C=values[1],fine_C=values[2],delta_K=delta,limit_K=limit,passed=delta<=limit))
        checks[label]=dict(status='PASS_ENGINEERING_THRESHOLD' if all(r['passed'] for r in comparison) else 'BLOCKED_CONVERGENCE',comparison=comparison,definition=policy['rule'])
    # RDEC changes the radiation discretization, independently of solid FE
    # refinement. Do not hide that change inside a mesh-convergence claim.
    for label,names in {
        'radiation_facets_fine':['B_normal24_rd90h_dt1','B_normal24_rd95h_dt1'],
        'radiation_facets_medium':['B_normal12_dt1_retry1','B_normal12_rd95h_dt1'],
        'radiation_facets_combined':['C_normal12_dt1','C_normal12_rd95_dt1'],
    }.items():
        data=[load(name) for name in names]
        if any(r is None for r in data):
            checks[label]=dict(status='PENDING',required=names);continue
        comparison=[]
        for part in sorted(set(r['part'] for r in data[-1])):
            for key,setting in [('maximum','peak_temperature_difference'),('capacity_weighted_mean','capacity_mean_temperature_difference')]:
                values=[max(float(r[key]) for r in rows if r['part']==part) for rows in data]
                limit=max(policy[setting]['absolute_floor_K'],policy[setting]['fraction_of_reference_rise']*abs(values[-1]-25))
                comparison.append(dict(part=part,metric=key,reference_C=values[0],reduced_C=values[1],delta_K=abs(values[1]-values[0]),limit_K=limit,passed=abs(values[1]-values[0])<=limit))
        # Integrated radiation must also be checked, even when tiny temperature
        # differences would mask a poor view-factor approximation.
        energy=[list(csv.DictReader((STUDIES/n/'pilot_FE_energy_balance.csv').open())) for n in names]
        rad=[]
        for rows in energy:
            candidates=[k for k in rows[-1] if 'rad' in k.lower() and k.endswith('_J')]
            assert len(candidates)==1,candidates
            rad.append(float(rows[-1][candidates[0]]))
        rad_limit=max(.1,.05*abs(rad[0]))
        comparison.append(dict(metric='final_net_radiation_J',reference_J=rad[0],reduced_J=rad[1],delta_J=abs(rad[1]-rad[0]),limit_J=rad_limit,passed=abs(rad[1]-rad[0])<=rad_limit))
        checks[label]=dict(status='PASS_ENGINEERING_THRESHOLD' if all(r['passed'] for r in comparison) else 'BLOCKED_RADIATION_REDUCTION',comparison=comparison,definition='Temperature policy plus net-radiation energy difference <= max(0.1 J, 5% reference). Engineering screen, not calibrated error.')
    (OUT/'convergence_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    parts=[('M4_BRAKE_DISC_HAT','Disc'),('M4_PAD_NEAR','Near pad')]
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for ax,(part,label) in zip(axes,parts):
        for name in ['B_face_scoped_full',*groups['mesh']]:
            data=load(name)
            if data:
                t,T=series(data,part,'maximum');mask=t<=3.77543701;ax.plot(t[mask],T[mask],label=name.replace('B_','').replace('_retry1',''))
        ax.set(xlabel='Time after brake onset [s]',ylabel='Local maximum [degC]',title=label);ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('Actual ANSYS | S3 concept | normal pad layers and disc face refinement\nOne-layer pad diagnostic is a rejected reference, not a validated peak',fontsize=10)
    fig.savefig(OUT/'mesh_refinement_actual.png');plt.close(fig)
    capacity_comparison()
    compare_M2()
    print('Actual summaries written; convergence:',{k:v['status'] for k,v in checks.items()})

def write_csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def capacity_comparison():
    c=json.loads((OUT/'face_scoped/FE_capacity_checks.json').read_text())['body_C_J_K']
    reference={r['id']:float(r['C_J_K']) for r in csv.DictReader((ROOT/'results/m2/parameter_source_table.csv').open())}
    mapping={'disc':['BRAKE_DISC_HAT'],'pad_caliper':['PAD_NEAR','PAD_FAR','CALIPER','CALIPER_REACTION_BRACKET'],
        'output_shaft':['OUTPUT_SHAFT'],'output_bearing':['OUTPUT_BEARING_1','OUTPUT_BEARING_2'],
        'gears':['STAGE1_GEAR','STAGE2_GEAR'],'oil':['OIL_INVENTORY'],'gear_case':['GEAR_CASE_FRONT','GEAR_CASE_REAR'],
        'motor_case':['MOTOR_CASE','MOTOR_GEAR_ADAPTER'],'stator':['MOTOR_STATOR'],'winding':['MOTOR_WINDING'],
        'rotor_other':['MOTOR_ROTOR_OTHER','MOTOR_ROTOR_SHAFT']}
    rows=[dict(M2_node=node,M2_C_J_K=reference[node],M4_C_J_K=sum(c['M4_'+part] for part in parts),
        M4_parts=';'.join(parts),difference_percent=100*(sum(c['M4_'+part] for part in parts)/reference[node]-1),
        basis='Actual FE volume times S3 rho cp; grouping equivalence is approximate') for node,parts in mapping.items()]
    write_csv(OUT/'M2_M4_capacity_comparison.csv',rows)

def compare_M2():
    # Same first-brake energy, align the archived M2 clock to brake onset.
    forcing=list(csv.DictReader((ROOT/'results/m2/cases/B_brake_only_forcing.csv').open()))
    onset=min(float(r['start_s']) for r in forcing if int(r['segment_id'])==2)
    reference=list(csv.DictReader((ROOT/'results/m2/cases/B_brake_only.csv').open()))
    tm=np.array([float(r['time_s'])-onset for r in reference])
    choice=next((n for n in ['B_normal12_rd95h_dt4','B_normal12_rd95h_dt2','B_normal24_rd95h_dt1','B_normal12_dt1_retry1','B_normal6_dt1'] if load(n)),None)
    if not choice:return
    actual=load(choice);rows=[]
    fig,ax=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for axis,part,node in [(ax[0],'M4_BRAKE_DISC_HAT','disc'),(ax[1],'M4_OUTPUT_BEARING_2','output_bearing')]:
        t,T=series(actual,part,'capacity_weighted_mean');_,Tmax=series(actual,part,'maximum')
        old=np.interp(t,tm,[float(r[node+'_K'])-273.15 for r in reference])
        offset=25 if node=='output_bearing' else 0
        axis.plot(t,T-offset,label='M4 FE capacity mean');axis.plot(t,Tmax-offset,label='M4 FE local max');axis.plot(t,old-offset,'--',label='Archived M2 lumped')
        axis.set(xlabel='Time after first brake onset [s]',ylabel='Temperature rise [K]' if offset else 'Temperature [degC]',title=node);axis.grid(alpha=.2);axis.legend(fontsize=8)
        if offset:axis.text(.03,.52,'Tiny predicted coupling signal;\nnot a calibrated temperature precision',transform=axis.transAxes,fontsize=7)
        rows.extend(dict(time_s=float(time),node=node,M4_mean_C=float(mean),M4_max_C=float(peak),M2_lumped_C=float(oldT),
            M4_study=choice,warning='Different C/contact/boundaries; M2 includes shield/hot air, M4 Case0 has neither. Not validation against measurements.') for time,mean,peak,oldT in zip(t,T,Tmax,old))
    fig.suptitle('Model comparison, not experimental validation | both S3 engineering concepts\nM3 geometry changed heat capacity; M2 shield / hot-air boundary differs',fontsize=10)
    fig.savefig(OUT/'M2_M4_first_brake_comparison.png');plt.close(fig);write_csv(OUT/'M2_M4_first_brake_comparison.csv',rows)

if __name__=='__main__':main()

