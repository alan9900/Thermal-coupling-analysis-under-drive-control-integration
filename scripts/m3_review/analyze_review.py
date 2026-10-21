"""Traceable preliminary statics / geometry thermal mapping, not FE analysis."""
import json,math,sys
import numpy as np
import yaml
from review_cad import ROOT,review_config,config
from run_geometry import csvout,writejson
OUT=ROOT/'results/m3_review'

def vm(T,M,d,K):return K*math.sqrt((32*M/(math.pi*(d/1000)**3))**2+3*(16*T/(math.pi*(d/1000)**3))**2)/1e6
def bending(x,loads,a,b):
    RB=sum(F*(pos-a)/(b-a) for pos,F in loads);RA=sum(F for pos,F in loads)-RB
    return RA*max(x-a,0)+RB*max(x-b,0)-sum(F*max(x-pos,0) for pos,F in loads)

def main():
    q=review_config();r=q['design'];v=yaml.safe_load((ROOT/'configs/baseline_vehicle.yaml').read_text(encoding='utf-8'))['vehicle'];p=config()
    reff=float(np.mean(np.hypot(np.linspace(95,132,301)[:,None],np.linspace(-24,24,301)[None,:])))/1000
    brake=[];bolts=[];shaft=[];keys=[];driveT=130*9*.96
    for ag in [.6,.8]:
        frac=v['static_rear_axle_fraction']-ag*v['cg_height_m']/v['wheelbase_m']
        T=v['mass_kg']*ag*v['gravity_m_s2']*frac*v['wheel_effective_rolling_radius_m']/2
        F=T/reff;N=F/(2*r['pad_friction_mu']);e=.160-reff;couple=F*e/.080
        boltF=math.hypot(F/2,couple);stress=boltF/84.3
        # A cantilever root envelope only; actual C bracket is a 3D load path.
        bracketM=F*.027;Z=.030*.120**2/6;bracketstress=bracketM/Z/1e6
        # Al boss thread stripping: conditional engagement12mm, shear perimeter.
        stripping=boltF/(math.pi*.010*.012)/1e6
        row=dict(deceleration_g=ag,rear_dynamic_fraction=frac,disc_torque_Nm=T,pad_effective_radius_m=reff,tangential_force_N=F,normal_force_each_pad_N=N,
            bolt_group_moment_Nm=F*e,bolt_force_N=boltF,M12_nominal_root_area_mm2=84.3,bolt_shear_screen_MPa=stress,
            bracket_nominal_bending_screen_MPa=bracketstress,boss_thread_shear_screen_MPa=stripping,
            shear_status='PASS_SCREEN_ONLY' if stress<120 else 'BLOCKED',
            housing_local_bending_and_joint_opening='BLOCKED_REQUIRES_MATERIAL_PRELOAD_AND_FE',certification=False)
        brake.append(row)
        for mu in r['joint_friction_scan']:
            for preload in r['bolt_preload_scan_N']:
                # Translation + overturning both have to be supported.
                demand=2*boltF;cap=2*mu*preload
                bolts.append(dict(joint='caliper_bracket',deceleration_g=ag,mu=mu,preload_per_bolt_N=preload,demand_N=demand,friction_capacity_N=cap,status='CONDITIONAL_SCREEN' if cap>=demand else 'BLOCKED_SLIP'))
    for d in [45,50]:
        B=19 if d==45 else 20;a=B/2/1000;b=(160-B/2)/1000
        # Include notch roots and steps explicitly. Gear-seat root >= journal.
        sections=[(x,d) for x in np.linspace(a,b,101)]
        sections += [(x,d) for x in np.linspace(b,.268,101)]
        for case,T,F,pos,loadlabel in [('drive',driveT,2*driveT/.180/math.cos(math.radians(20)),.111,'gear'),
             *[(f'brake_{x["deceleration_g"]}g',x['disc_torque_Nm'],x['tangential_force_N'],.216,'disc') for x in brake]]:
            for K in r['shaft_notch_factors']:
                values=[]
                for x,D in sections:
                    mm=x*1000
                    if 90<=mm<95:D=d+16
                    if 95<=mm<=127:D=d+12-(11 if d==50 else 10)
                    # Removable sleeves carry external keys; the base journal
                    # has no key cut. Do not add sleeve stiffness to shaft stress.
                    transmitted=T if (.111<=x<=.264 if case=='drive' else .195<=x<=.264) else 0
                    M=bending(x,[(pos,F)],a,b);values.append((vm(transmitted,M,D,K),mm,D,M,transmitted))
                peak=max(values)
                shaft.append(dict(shaft='output',diameter_mm=d,load_case=case,notch_factor=K,peak_von_Mises_MPa=peak[0],critical_x_mm=peak[1],critical_root_diameter_mm=peak[2],bending_Nm=peak[3],local_torque_Nm=peak[4],assumed_limit_MPa=180,status='PASS_SCREEN_ONLY' if peak[0]<=180 else 'BLOCKED'))
        for name,seat,h,L,T in [('output_gear',d+12,11 if d==50 else 10,30,driveT),('disc_hub',d+12,8,35,max(x['disc_torque_Nm'] for x in brake)),('halfshaft',d+12,8,42,driveT)]:
            for share in [.5,1.0]:
                n=2;F=2*T/(seat/1000)/(n*share);w=18 if name=='output_gear' and d==50 else 16 if name=='output_gear' else 12
                shear=F/(w*L);bearing=F/(h/2*L)
                keys.append(dict(interface=name,diameter_mm=d,effective_load_share=share,key_shear_MPa=shear,key_bearing_MPa=bearing,assumed_shear_limit_MPa=120,assumed_bearing_limit_MPa=240,status='PASS_SCREEN_ONLY' if shear<120 and bearing<240 else 'BLOCKED'))
    # Input shaft keyed-coupling roots remain a real unresolved issue.
    for K in r['shaft_notch_factors']:
        val=vm(130,0,25,K);shaft.append(dict(shaft='input_coupling_root',diameter_mm=30,load_case='drive',notch_factor=K,peak_von_Mises_MPa=val,critical_x_mm=-20,critical_root_diameter_mm=25,bending_Nm=0,local_torque_Nm=130,assumed_limit_MPa=180,status='PASS_SCREEN_ONLY' if val<=180 else 'BLOCKED'))
        a=.008;b=.152;F=2*130/.050/math.cos(math.radians(20));M=F*(.0455-a)*(b-.0455)/(b-a)
        val=vm(130,M,30,K);shaft.append(dict(shaft='input_pinion_section',diameter_mm=30,load_case='drive',notch_factor=K,peak_von_Mises_MPa=val,critical_x_mm=45.5,critical_root_diameter_mm=30,bending_Nm=M,local_torque_Nm=130,assumed_limit_MPa=180,status='PASS_SCREEN_ONLY' if val<=180 else 'BLOCKED'))
    for share in [.5,1.0]:
        F=2*130/.030/(2*share);shear=F/(8*16);bearing=F/(2.5*16)
        keys.append(dict(interface='motor_input_coupling',diameter_mm=30,effective_load_share=share,key_shear_MPa=shear,key_bearing_MPa=bearing,assumed_shear_limit_MPa=120,assumed_bearing_limit_MPa=240,status='PASS_SCREEN_ONLY' if shear<120 and bearing<240 else 'BLOCKED'))
    # Intermediate orthogonal mesh forces; exact torques depend on per-stage eta.
    a=.009;b=.151;Ti=130*3*.98
    for K in r['shaft_notch_factors']:
        vals=[]
        for x in np.linspace(a,b,1001):
            Ft1=2*Ti/.150;Ft2=2*Ti/.060;tan=math.tan(math.radians(20))
            My=bending(x,[(.0455,Ft1),(.111,Ft2*tan)],a,b)
            Mz=bending(x,[(.0455,Ft1*tan),(.111,Ft2)],a,b)
            T=Ti if .0455<=x<=.111 else 0;D=41 if .033<=x<=.058 else 40
            vals.append((vm(T,math.hypot(My,Mz),D,K),x*1000,D,math.hypot(My,Mz),T))
        vpeak=max(vals);shaft.append(dict(shaft='intermediate',diameter_mm=40,load_case='drive',notch_factor=K,peak_von_Mises_MPa=vpeak[0],critical_x_mm=vpeak[1],critical_root_diameter_mm=vpeak[2],bending_Nm=vpeak[3],local_torque_Nm=vpeak[4],assumed_limit_MPa=180,status='PASS_SCREEN_ONLY' if vpeak[0]<=180 else 'BLOCKED'))
    csvout(OUT/'brake_loads.csv',brake);csvout(OUT/'joint_slip_scan.csv',bolts);csvout(OUT/'shaft_screening.csv',shaft);csvout(OUT/'key_screening.csv',keys)
    # Expansion and displacement budget are checks, not computed operating T.
    expansion=[]
    for delta in [200,400,600]:
        dr=140*11e-6*delta;dx=22/2*11e-6*delta
        for runout in [.1,.3,1.0]:
            gap=.5-dx-runout-.1
            expansion.append(dict(disc_delta_K=delta,runout_budget_mm=runout,radial_growth_mm=dr,half_thickness_growth_mm=dx,pad_residual_gap_mm=gap,radial_caliper_residual_mm=5-1-dr,
                status='PASS_BUDGET_ONLY' if gap>0 and 5-1-dr>0 else 'BLOCKED',load_deflection_mm=None))
    csvout(OUT/'expansion_clearances.csv',expansion)
    floatchecks=[]
    for Ts in [100,300,600]:
        for Tc in [0,100,300]:
            mismatch=.140*(12e-6*Ts-23e-6*Tc)*1000
            floatchecks.append(dict(shaft_rise_K=Ts,case_rise_K=Tc,relative_growth_mm=mismatch,available_each_direction_mm=.5,status='PASS_BUDGET_ONLY' if abs(mismatch)<=.5 else 'BLOCKED_END_FLOAT_EXCEEDED'))
    csvout(OUT/'bearing_axial_expansion.csv',floatchecks)
    shields=[]
    for Ts in [100,300,500]:
        for Tc in [0,100,300]:
            mismatch=145*(17e-6*Ts-23e-6*Tc)
            shields.append(dict(shield_rise_K=Ts,case_rise_K=Tc,anchor_radius_mm=145,relative_radial_growth_mm=mismatch,bolt_hole_radial_clearance_mm=.2,
                status='PASS_FREE_EXPANSION_BUDGET_ONLY' if abs(mismatch)<=.2 else 'BLOCKED_REQUIRES_SLIDING_MOUNT',actual_constrained_stress=None))
    csvout(OUT/'shield_mount_expansion.csv',shields)
    halfshaft=[]
    for mu in r['joint_friction_scan']:
        for preload in r['bolt_preload_scan_N']:
            cap=8*mu*preload*.045
            halfshaft.append(dict(mu=mu,preload_per_M10_N=preload,friction_only_torque_Nm=cap,drive_demand_Nm=driveT,status='PASS_FRICTION_SCREEN_ONLY' if cap>=driveT else 'BLOCKED_FRICTION_ONLY',
                fitted_dowels_effective_count=2,dowel_shear_candidate_MPa=driveT/(2*.045)/(math.pi*12**2/4),dowel_fit_verified=False))
    csvout(OUT/'halfshaft_joint_scan.csv',halfshaft)
    sleeves=[]
    for d in [45,50]:
        for name,L,T in [('hub',.040,max(x['disc_torque_Nm'] for x in brake)),('halfshaft',.048,driveT)]:
            for mu in r['joint_friction_scan']:
                for pressure in r['removable_sleeve_pressure_scan_MPa']:
                    cap=mu*pressure*1e6*math.pi*(d/1000)**2*L/2
                    # Thick-cylinder hoop estimate at bore for isolated sleeve.
                    ri=d/2;ro=(d+12)/2;hoop=pressure*(ro*ro+ri*ri)/(ro*ro-ri*ri)
                    sleeves.append(dict(interface=name,diameter_mm=d,contact_length_m=L,assumed_mu=mu,assumed_pressure_MPa=pressure,torque_capacity_Nm=cap,demand_Nm=T,
                        isolated_sleeve_hoop_MPa=hoop,assumed_limit_MPa=180,status='PASS_SCREEN_ONLY' if cap>=T and hoop<=180 else 'BLOCKED',
                        caveat='Keycuts, elastic compound hub constraint, thermal loosening and fatigue not solved; pressure is not calibrated'))
    csvout(OUT/'removable_sleeve_scan.csv',sleeves)
    # Aggregate CAD capacities; no double-counting integral pinions in gears.
    mass=list(csv.DictReader((OUT/'mass_heat_capacity.csv').open(encoding='utf-8')))
    rows=[x for x in mass if x['case']=='Case0' and x['diameter_mm']=='50' and x['variant']=='full']
    ids={'disc':['brake_disc_hat'],'pad_caliper':['caliper','pad_near','pad_far'], 'output_shaft':['output_shaft'],
        'gears':['stage1_gear','stage2_gear'],'gear_case':['gear_case_front','gear_case_rear'],'motor_case':['motor_case'],
        'stator':['motor_stator'],'winding':['motor_winding'],'rotor_other':['motor_rotor_other','motor_rotor_shaft'],'oil':['oil_inventory']}
    m2=yaml.safe_load((ROOT/'configs/m2_thermal_network.yaml').read_text(encoding='utf-8'));comparison=[]
    for n in m2['nodes']:
        found=[x for x in rows if x['part'] in ids.get(n['id'],[])]
        C=sum(float(x['geometric_solid_C_candidate_J_K']) for x in found) if found else None
        comparison.append(dict(node=n['id'],M2_C_J_K=n['mass_kg']*n['cp_J_kgK'],M3_geometry_candidate_C_J_K=C,ratio=C/(n['mass_kg']*n['cp_J_kgK']) if C is not None else None,
            basis='GEOMETRY_VOLUME_AND_S3_PROPERTIES' if found else 'UNRESOLVED_OR_CASE_DEPENDENT',difference_explanation='Integral pinions stay with shaft regions; not direct original aggregate comparison' if n['id']=='gears' else 'CAD volume / assumed material; not a calibrated installed mass'))
    csvout(OUT/'M2_capacity_comparison.csv',comparison)
    contacts=list(csv.DictReader((OUT/'contact_pairs.csv').open(encoding='utf-8')));contactscan=[]
    for c in contacts:
        if c['case']!='Case0' or c['diameter_mm']!='50' or c['variant']!='full':continue
        A=float(c['nominal_contact_area_m2'])
        if A>0:
            for h in r['contact_h_scan_W_m2K']:contactscan.append(dict(a=c['a'],b=c['b'],nominal_A_m2=A,assumed_h_W_m2K=h,R_contact_candidate_K_W=1/(h*A),classification='S3_RANGE_NOT_MEASURED'))
    csvout(OUT/'contact_R_scan.csv',contactscan)
    bulk=[]
    # Axial path through the stepped 50mm shaft from hub to rear bearing.
    for d in [45,50]:
        lengths=[(.195-.150,math.pi*(d/1000)**2/4)]
        Rbulk=sum(L/(45*A) for L,A in lengths)
        bulk.append(dict(path=f'hub_to_rear_bearing_d{d}',length_m=.045,area_m2=None,k_W_mK=45,R_bulk_K_W=Rbulk,M2_equivalent_R_K_W=1.5,
            meaning='Bulk only; spreading, key interfaces, race/rolling/lubrication contacts absent'))
    bulk += [dict(path='hat_radial_40_to_88',length_m=.048,area_m2=None,k_W_mK=45,R_bulk_K_W=math.log(88/40)/(2*math.pi*45*.005),M2_equivalent_R_K_W=2,
        meaning='Annular radial body resistance; not disc-hub-shaft total'),dict(path='bracket_axial_envelope',length_m=.027,area_m2=.030*.120,k_W_mK=45,R_bulk_K_W=.027/(45*.030*.120),M2_equivalent_R_K_W=8,
        meaning='Uniform body lower bound only; C bracket spreading, bolts, contact unknown')]
    csvout(OUT/'bulk_R_comparison.csv',bulk)
    # Heat sources must partition, not duplicate. Volume-normalized integrated W.
    byname={x['part']:x for x in rows};sources={
        'winding_copper':['motor_winding'],'motor_iron':['motor_stator'],'rotor_other':['motor_rotor_other'],
        'reducer_gear':['input_shaft','intermediate_shaft','stage1_gear','stage2_gear'],
        'reducer_bearing':['input_bearing_1','input_bearing_2','intermediate_bearing_1','intermediate_bearing_2','output_bearing_1','output_bearing_2'],
        'reducer_other':['oil_inventory'],'brake_disc':['brake_disc_hat'],'brake_pad':['pad_near','pad_far']}
    mapping={}
    regionfile=OUT/'source_regions.csv'
    regionrows={x['body']:x for x in csv.DictReader(regionfile.open(encoding='utf-8'))} if regionfile.exists() else {}
    for source,names in sources.items():
        def vol(n):return float(regionrows[n]['volume_m3']) if source=='reducer_gear' and n in regionrows else float(byname[n]['volume_m3'])
        V=sum(vol(n) for n in names)
        mapping[source]=[dict(body=n,volume_m3=vol(n),fraction=vol(n)/V,
            region=regionrows[n]['region'] if source=='reducer_gear' and n in regionrows else 'whole_body',
            application='q_i_W_m3 = Q_source_W / sum(V_selected)') for n in names]
    newnodes=['disc_hub','removable_hub_and_halfshaft_sleeves','bracket','input_shaft_integral_pinion','intermediate_shaft_integral_pinion','adapter','front_output_bearing','rear_output_bearing','front_rear_case','individual_shields','seals','halfshaft_interface']
    writejson(ROOT/'configs/M3_to_M4_mapping.json',dict(version='M3-review-1.0',status='PARTIAL_PREPARATION_NOT_SOLVER_RELEASE',M2_baseline='M2-v1.0',units=dict(length='m',heat='W',qvol='W/m3',temperature='K'),
        actual_verified_contacts=None,actual_cooling=None,measured_internal_masses=None,engineering_contact_h_scan_W_m2K=r['contact_h_scan_W_m2K'],sources=mapping,
        source_allocation_caveat='Uniform volume weighting is S3, especially integral pinions and bearing dissipation. Resolved tooth/race local flux is unknown.',
        inverter='EXTERNAL_NOT_LOADED',total_motor_and_reducer_losses='VALIDATION_ONLY_NEVER_LOAD_AGAIN',rotor_other='NOT_ALL_PERMANENT_MAGNET_HEAT',
        added_network_nodes=newnodes,bearing_mass='CAD annulus is envelope. Use verified catalogue/prototype mass or explicit effective rho, never solid steel annulus mass.',
        contacts_csv=['results/m3_review/contact_pairs.csv','results/m3_review/supplemental_contact_pairs.csv'],boundary_status=dict(coolant_ports='BLOCKED_NO_HYDRAULIC_CONNECTION',liquid_film='UNKNOWN_REQUIRES_RANGE',sleeves='BLOCKED_PRESS_FIT_RETENTION_AND_THERMAL_LOOSENING',winding_insulation='BLOCKED_ENDRING_CORE_NOMINAL_TOUCH_REQUIRES_CONTACT_R_NOT_BONDED',pad_contact='RUNNING_GAP_REQUIRES_TRANSIENT_CONTACT_OR_HEAT_FLUX',external_air='LOCAL_CONNECTED_DOMAIN_NOT_FAR_FIELD_VALIDATED'),
        geometry_import='OCCT_ROUNDTRIP_TESTED_ANSYS_NOT_EXECUTED'))
    writejson(OUT/'analysis_checks.json',dict(status='PARTIAL_WITH_EXPLICIT_BLOCKERS',braking_zero_regen_cases=brake,output_drive_torque_Nm=driveT,
        mechanical_certification='NOT EXECUTED',M4='NOT EXECUTED',M2_overwritten=False,shaft_blocked=[x for x in shaft if x['status']=='BLOCKED'],key_blocked=[x for x in keys if x['status']=='BLOCKED'],
        required_release_items=['shaft/key fatigue and certified materials','bearing fits, rings/collar retention, cap screw preload and life','motor coupling alignment, fitted-key load sharing and fatigue','caliper joint slip and housing compliance','pad piston travel and hot runout','axial location end float / tolerances','actual CV interface and vehicle package','measured contact laws and coolant geometry']))
    print('Analysis completed; blockers preserved. Brake torques',[x['disc_torque_Nm'] for x in brake],flush=True)

if __name__=='__main__':
    import csv
    main()
