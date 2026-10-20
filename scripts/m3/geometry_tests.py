"""Independent geometry/regression tests, not manufacturing certification."""
import copy,hashlib,json,subprocess
import cadquery as cq
from cad_model import ROOT,config,build,box
from run_geometry import overlaps,writejson,OUT,csvout

def main():
    p=config();base=build(p,'Case0');groups=[]
    assert not any('shield' in name for name in base['parts']);groups.append('True Case0 contains no shield, duct or added shield supports')
    r=p['reducer'];assert (r['teeth_gear']/r['teeth_pinion'])**2==9
    assert p['motor_reference']['casing_diameter_mm']==302 and p['motor_reference']['casing_length_mm']==161
    assert p['brake_reference']['outer_diameter_mm']==280 and p['brake_reference']['thickness_mm']==22
    groups.append('Source reference envelopes and both stage ratios are preserved')
    phase=[]
    for small,big,axis_a,axis_b in [('stage1_pinion','stage1_gear','input','intermediate'),('stage2_pinion','stage2_gear','intermediate','output')]:
        ya,za=base['axes'][axis_a];yb,zb=base['axes'][axis_b]
        for angle in [0,2.25,4.5,6.75,9,11.25,13.5,15.75,18]:
            a=base['parts'][small].rotate((0,ya,za),(1,ya,za),angle);b=base['parts'][big].rotate((0,yb,zb),(1,yb,zb),-angle/3)
            common=a.intersect(b).Volume();assert common<.001,(small,angle,common)
            phase.append(dict(pair=small+'_'+big,pinion_rotation_deg=angle,common_mm3=common))
    csvout(OUT/'gear_phase_checks.csv',phase);groups.append('18 sampled mesh phases have no positive tooth interference; no root fillet/contact stress validation')
    common=[]
    for case in ['CaseA','CaseB','CaseC']:
        model=build(p,case)
        for name,sh in base['parts'].items():
            other=model['parts'][name];assert abs(other.Volume()-sh.Volume())<1e-6,name
            assert (other.Center()-sh.Center()).Length<1e-8
        assert all(len(sh.Solids())==1 for name,sh in model['parts'].items() if name.startswith('shield_layer'))
        common.append(case)
    groups.append('All 32 base bodies identical across cases; each shield has one connected B-rep solid')
    bad=copy.deepcopy(p);bad['brake_design']['near_face_x_mm']=185
    rejected=[q for q in overlaps(build(bad,'Case0')) if q['status']=='INTERFERENCE']
    assert rejected;writejson(OUT/'rejected_close_packaging.json',dict(gap_mm=25,interferences=rejected))
    groups.append('25mm tight packaging correctly rejected by actual B-rep interference')
    # Read accepted M2 only, and compare the saved regression record.
    assert not subprocess.check_output(['git','diff','M2-v1.0','--name-only','--','configs/m2_thermal_network.yaml','scripts/m2','results/m2','reports/M2_report.md','reports/M2_report.docx','reports/M2_report.pdf'],text=True).strip()
    groups.append('M2-v1.0 model, sources, numerical outputs and report remain unchanged')
    shape=cq.importers.importStep(str(ROOT/'cad/m3/Case0_assembly.step')).val();assert shape.isValid()
    bb=shape.BoundingBox();assert bb.xlen>400 and bb.ylen>400
    groups.append('STEP roundtrip retains valid solids and millimetre assembly scale')
    # M2 candidates map explicitly; bearing thermal mass must not use solid
    # envelope mass as real rolling-bearing mass.
    rows=[];cfg2=json.loads((ROOT/'results/m2/inputs.json').read_text(encoding='utf-8'))['configuration']
    old={q['id']:q['mass_kg']*q['cp_J_kgK'] for q in cfg2['nodes']}
    mapping={'disc':['brake_disc_hat'],'pad_caliper':['caliper','pad_near','pad_far'],'output_shaft':['output_shaft'],'gears':['stage1_pinion','stage1_gear','stage2_pinion','stage2_gear'],
        'oil':['oil_inventory'],'gear_case':['gear_case'],'motor_case':['motor_case'],'stator':['motor_stator'],'winding':['motor_winding'],'rotor_other':['motor_rotor_other']}
    for node,names in mapping.items():
        mass=C=0
        for name in names:
            mat=p['materials'][base['materials'][name]];m=base['parts'][name].Volume()*1e-9*mat['rho_kg_m3'];mass+=m;C+=m*mat['cp_J_kgK']
        if node=='rotor_other':
            shaft=base['parts']['input_rotor_shaft'].intersect(box(-200,0,-1000,1000,-1000,1000));m=shaft.Volume()*1e-9*7800;mass+=m;C+=m*460
        rows.append(dict(M2_node=node,M2_C_J_K=old[node],M3_mass_candidate_kg=mass,M3_C_candidate_J_K=C,ratio_to_M2=C/old[node],classification='S3_CANDIDATE_NOT_APPLIED',mapping_note='Only motor-side shaft included; remaining gearbox input shaft requires separate node' if node=='rotor_other' else 'Geometry material equivalent; no temperature recalculation'))
    rows.append(dict(M2_node='output_bearing',M2_C_J_K=old['output_bearing'],M3_mass_candidate_kg=.404*2,M3_C_candidate_J_K=.404*2*460,ratio_to_M2=.404*2*460/old['output_bearing'],classification='REFERENCE_MASS_CANDIDATE_NOT_APPLIED',mapping_note='Two SKF6209 catalogue masses0.404kg each; solid annular CAD envelope is not true bearing mass or radial conductance'))
    csvout(OUT/'M2_revision_candidates.csv',rows)
    # Selected case end-face area, excluding bores. All-face areas in mass CSV
    # include internal faces and MUST NOT be loaded as external convection area.
    area=0
    for face in base['parts']['gear_case'].Faces():
        if abs(face.Center().x-160)<1e-6 and face.normalAt().x>.99:area+=face.Area()*1e-6
    p2=p['shield_design'];A=3.141592653589793*(.15**2-.095**2)*(1-80/360)
    shieldrows=[]
    for case in ['CaseA','CaseB','CaseC']:
        m=build(p,case);sh=m['parts']['shield_layer_1'];shmass=sum(shape.Volume()*1e-9*7800 for name,shape in m['parts'].items() if name.startswith('shield'))
        shieldrows.append(dict(case=case,shield_and_support_mass_kg=shmass,thickness_mm=1.5,disc_gap_mm=10,double_air_gap_mm=10 if case=='CaseB' else 0,vent_open_fraction_available=.15,caliper_cutout_fraction=80/360,vent_port_area_m2=A*.15,duct_inlet_area_m2=(.040-.003)*(.070-.003) if case=='CaseC' else 0,outlet_angle_deg=20 if case=='CaseC' else 0))
    csvout(OUT/'case_parameters.csv',shieldrows)
    writejson(OUT/'M2_geometry_interface.json',dict(classification='S3_GEOMETRY_CANDIDATES_NOT_APPLIED_TO_M2',length_units='m in candidate tables, mm in STEP/YAML',
        selected_gear_case_front_radiation_area_m2=area,disc_exposed_case_facing_area_m2=3.141592653589793*(.140**2-.088**2),
        motor_case_outer_area_ideal_envelope_m2=2*3.141592653589793*.151*.161+2*3.141592653589793*(.151**2-.0152**2),
        motor_jacket_inner_wet_area_m2=2*3.141592653589793*.137*.105,water_equivalent_inventory_kg=base['parts']['motor_water_jacket'].Volume()*1e-6,
        M2_coolant_G_W_K=25,actual_coolant_h_W_m2K=None,actual_coolant_flow_kg_s=None,thermal_contact_resistances=None,
        extra_nodes_recommended=['disc_hub','caliper_reaction_bracket','gearbox_input_and_intermediate_shafts','two output bearings','coolant if finite thermal capacity'],
        Case0_removes_M2_shield_node=True,M2_cases_are_heat_loading_cases_not_M3_design_cases=True,
        warning='Selected case front face F is not full casing view factor; shield supports/re-emission and air flow remain. No independent source upper-bound combination, no inverter heat in motor, no rotor-other-to-magnet relabeling.'))
    groups.append('Geometry candidates include explicit masses/heat capacities/areas and null contact/cooling parameters, without overwriting M2')
    writejson(OUT/'tests.json',dict(status='PASS',groups=groups,test_group_count=len(groups),gear_phase_samples=len(phase),nominal_cases=4,M4='NOT STARTED'))
    print('M3 geometry tests PASS:',len(groups),'groups and',len(phase),'mesh phases.')

if __name__=='__main__':main()
