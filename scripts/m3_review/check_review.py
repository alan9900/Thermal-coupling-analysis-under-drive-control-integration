"""Regression of refined geometry and strict separation of unknown inputs."""
import csv,json,math,subprocess
import numpy as np
import cadquery as cq
from review_cad import *
from run_geometry import csvout,writejson
OUT=ROOT/'results/m3_review'

def main():
    q=review_config();p=config();tests=[];phase=[]
    g=json.loads((OUT/'geometry_checks.json').read_text());assert len(g['runs'])==10 and all(x['interferences']==0 for x in g['runs']);tests.append('10 full/thermal STEP assemblies valid and zero positive overlaps')
    assert all(x['roundtrip_relative_volume_error']<1e-6 for x in g['runs']);tests.append('STEP roundtrip and mm scale')
    m=build_review();P=m['parts'];assert not any(n.startswith('shield') for n in P);tests.append('True Case0 has no shield or new supports')
    assert P['motor_case'].BoundingBox().xlen==161 and p['motor_reference']['casing_diameter_mm']==302;tests.append('Reference motor preserved, 60mm adapter translates rather than scales')
    for n in ['input','intermediate','output']:
        assert n+'_front_retaining_ring' in P and n+'_rear_clamp_collar' in P and n+'_front_seal' in P
        be=m['bearings'][n];_,_,zz=P[n+'_rear_outer_retainer'].Center().toTuple()
        assert abs(P[n+'_rear_outer_retainer'].BoundingBox().xmin-160.5)<1e-6
    tests.append('Three supported shafts include shoulders, retaining parts, seals and rear0.5mm nominal end float')
    # Right bearing can pass from the right while removable seats are absent.
    # Gear/collar first, then bearing, seals and sleeves. Actual fits remain null.
    out=P['output_shaft'];rear_start=140
    swept=out.intersect(box(rear_start+.01,268.01,-100,100,-100,100))
    assert swept.BoundingBox().ylen<=50.00001 and swept.BoundingBox().zlen<=50.00001
    assert len(P['hub_removable_sleeve'].Solids())==1 and len(P['halfshaft_removable_sleeve'].Solids())==1
    tests.append('Rear bearing installation envelope passes after seats become removable sleeves; fit qualification remains BLOCKED')
    for n1,n2,ax1,ax2,small in [('input_shaft','stage1_gear','input','intermediate',None),('intermediate_shaft','stage2_gear','intermediate','output',None)]:
        y,z=m['axes'][ax1];y2,z2=m['axes'][ax2]
        for a in np.linspace(0,18,9):
            sh1=P[n1].rotate((0,y,z),(1,y,z),a);sh2=P[n2].rotate((0,y2,z2),(1,y2,z2),-a/3)
            V=sh1.intersect(sh2).Volume();assert V<.001,(n1,a,V);phase.append(dict(pair=n1+'-'+n2,phase_deg=a,overlap_mm3=V))
    csvout(OUT/'gear_phase_checks.csv',phase);tests.append('18 phases of revised integral-pinion/gear meshes have no tooth overlap')
    for a in [0,15,30,45,60,90]:
        disc=P['brake_disc_hat'].rotate((0,0,0),(1,0,0),a)
        for name in ['caliper','pad_near','pad_far','caliper_reaction_bracket']:
            assert disc.intersect(P[name]).Volume()<.001
    tests.append('24 brake rotation / fixed-caliper pair checks')
    # A deliberately enlarged caliper must trigger a collision.
    assert P['brake_disc_hat'].intersect(box(205,227,-150,-80,-50,50)).Volume()>.001;tests.append('Bad caliper collision is rejected, not filtered out')
    assert not subprocess.check_output(['git','diff','79c6a4f','--name-only','--','cad/m3','scripts/m3','results/m3','configs/m3_geometry.yaml','reports/M3_report.md','reports/M3_report.docx','reports/M3_report.pdf'],cwd=ROOT,text=True).strip()
    tests.append('Original M3 concept models/results/reports unchanged')
    assert not subprocess.check_output(['git','diff','M2-v1.0','--name-only','--','scripts/m2','results/m2','configs/m2_thermal_network.yaml','reports/M2_report.md','reports/M2_report.docx','reports/M2_report.pdf'],cwd=ROOT,text=True).strip()
    tests.append('Archived M2 unchanged')
    mapdata=json.loads((ROOT/'configs/M3_to_M4_mapping.json').read_text());assert mapdata['actual_verified_contacts'] is None
    for rows in mapdata['sources'].values():assert abs(sum(x['fraction'] for x in rows)-1)<1e-12
    names=[x['body'] for rows in mapdata['sources'].values() for x in rows];assert len(names)==len(set(names));tests.append('Source weights sum to1, no duplicated bodies, actual contacts remain null')
    mass=list(csv.DictReader((OUT/'mass_heat_capacity.csv').open(encoding='utf-8')))
    full={x['part']:float(x['volume_m3']) for x in mass if x['case']=='Case0' and x['diameter_mm']=='50' and x['variant']=='full'}
    simp={x['part']:float(x['volume_m3']) for x in mass if x['case']=='Case0' and x['diameter_mm']=='50' and x['variant']=='thermal'}
    assert set(P)==set(full)
    assert max(abs(P[n].Volume()*1e-9-v)/v for n,v in full.items())<1e-8
    tests.append('Current editable source reproduces every exported50mm baseline body volume')
    error=max(abs(simp[n]-v)/v for n,v in full.items());assert error<1e-6,error
    assert all(not x['installed_mass_kg'] for x in mass if '_bearing_' in x['part']);tests.append('Thermal simplification conserves per-body volume; bearing envelope mass not asserted as installed mass')
    a=json.loads((OUT/'analysis_checks.json').read_text());T=a['braking_zero_regen_cases'];assert abs(T[0]['disc_torque_Nm']-752.83909)<.001 and 910<T[1]['disc_torque_Nm']<912
    assert any(x['diameter_mm']==45 for x in a['shaft_blocked']);tests.append('Rear axle load transfer and45mm failures remain explicit')
    # Gap network: winding slots are not bonded by CAD; do not automatically
    # heal or merge all touching parts into one multi-material solid.
    thermal=build_review(50,'Case0',True);assert len(thermal['parts']['motor_winding'].Solids())==1
    # End rings nominally touch the core face; only active slots have a gap.
    core=P['motor_stator'];bb=core.BoundingBox()
    active=P['motor_winding'].intersect(box(bb.xmin+.01,bb.xmax-.01,-500,500,-500,500))
    assert active.distance(core)>.19
    assert P['motor_winding'].distance(core)<1e-5
    tests.append('Active-slot0.2mm gap preserved; end-ring nominal touch detected, insulation/contact law remains BLOCKED')
    writejson(OUT/'tests.json',dict(status='PASS_AUDIT_NOT_DESIGN_RELEASE',test_group_count=len(tests),groups=tests,mesh_phase_samples=len(phase),brake_rotation_pairs=24,
        max_thermal_per_body_volume_error=error,blocked_engineering_items_are_not_test_passes=True,ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED'))
    print('Audit tests PASS:',len(tests),'groups; unresolved mechanics remain BLOCKED.')

if __name__=='__main__':main()
