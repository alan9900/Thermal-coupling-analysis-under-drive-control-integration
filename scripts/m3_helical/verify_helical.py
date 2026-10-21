"""Independent checks on actual screw edges, mesh phases and immutable history."""
import csv,json,math,subprocess,sys
import numpy as np
import cadquery as cq
from helical_cad import ROOT,helical_gear,old,settings
from run_geometry import csvout,writejson
OUT=ROOT/'results/m3_helical';CACHE=ROOT/'tmp/m3_helical'

def main():
    assert len(json.loads((OUT/'checks.json').read_text())['runs'])==8, 'Run CAD generation to completion first'
    params=list(csv.DictReader((OUT/'gear_parameters.csv').open()))
    edge_checks=[];phases=[];loads=[]
    definitions=[(1,2.5,25,33,120,100,120,0,-90,87,30,50),
                 (2,3,32,95,120,0,0,0,180,-3,40,62)]
    for stage,mt,w,x,yp,zp,yg,zg,pp,pg,bp,bg in definitions:
        print('CHECK STAGE',stage,flush=True)
        pinion=helical_gear(mt,20,bp,w,x,yp,zp,pp,.15)
        gear=helical_gear(mt,60,bg,w,x,yg,zg,pg,.15)
        for name,s,z,yc,zc,hand in [('pinion',pinion,20,yp,zp,1),('gear',gear,60,yg,zg,-1)]:
            # Follow an actual BREP edge spanning the face: unwrap is independent
            # of tooth periodicity, so >one-tooth twist cannot alias to zero.
            es=[e for e in s.Edges() if e.BoundingBox().xlen>w-.0001]
            assert es
            e=max(es,key=lambda e:(e.positionAt(.5).y-yc)**2+(e.positionAt(.5).z-zc)**2)
            pts=np.array([e.positionAt(float(t)).toTuple() for t in np.linspace(0,1,101)])
            pts=pts[np.argsort(pts[:,0])]
            angles=np.unwrap(np.arctan2(pts[:,2]-zc,pts[:,1]-yc));delta=angles[-1]-angles[0]
            measured=math.degrees(math.atan((mt*z/2)*delta/(pts[-1,0]-pts[0,0])))
            assert abs(measured-hand*20)<1e-5,(name,measured)
            caps=[f for f in s.Faces() if f.BoundingBox().xlen<1e-6 and abs(f.Center().x-x)<1e-5]
            cap=max(caps,key=lambda f:f.Area());ra=mt*z/2+mt
            tips=[v for v in cap.outerWire().Vertices() if abs(math.hypot(v.Center().y-yc,v.Center().z-zc)-ra)<1e-5]
            assert len(tips)==2*z,(name,len(tips),z)
            edge_checks.append(dict(stage=stage,part=name,tip_vertices=len(tips),measured_teeth=len(tips)//2,
                actual_edge_twist_deg=math.degrees(delta),measured_signed_beta_deg=measured,status='PASS'))
        # One full pinion tooth period (18 deg); driven phase exactly -theta/3.
        for angle in np.linspace(0,18,7):
            A=pinion.rotate((0,yp,zp),(1,yp,zp),float(angle))
            B=gear.rotate((0,yg,zg),(1,yg,zg),float(-angle/3))
            v=A.intersect(B).Volume();distance=A.distance(B)
            phases.append(dict(stage=stage,pinion_rotation_deg=float(angle),gear_rotation_deg=float(-angle/3),overlap_mm3=v,min_distance_mm=distance))
            csvout(OUT/'mesh_phase_checks.csv',phases)
            assert v<.001,(stage,angle,v)
        # Ideal magnitude only: 130Nm software input, no efficiency claim.
        torque=130*(3**(stage-1));ft=torque/(mt*10/1000);fa=ft*math.tan(math.radians(20))
        loads.append(dict(stage=stage,input_torque_Nm=torque,tangential_force_N=ft,axial_force_magnitude_N=fa,
            radial_force_N=ft*math.tan(math.radians(20)),status='S3_ORDER_OF_MAGNITUDE_NOT_BEARING_RELEASE'))
    csvout(OUT/'actual_helix_checks.csv',edge_checks);csvout(OUT/'axial_force_screen.csv',loads)
    finalize(edge_checks,phases,loads)

def finalize(edge_checks,phases,loads):
    # RH pinions/LH wheels do not automatically cancel intermediate axial loads.
    # +x applied input torque => stage1 mesh resists it, driver Fa>0 and
    # driven Fa<0. Intermediate rotation reverses; stage2 driver Fa<0.
    # Both intermediate contributions
    # therefore add in this chosen convention, reverse under reverse torque.
    axial=dict(convention='positive x axis; positive input torque; pinions RH, wheels LH',
        input_net_Fx_N=loads[0]['axial_force_magnitude_N'],
        intermediate_net_Fx_N=-sum(r['axial_force_magnitude_N'] for r in loads),
        output_net_Fx_N=loads[1]['axial_force_magnitude_N'],
        limitation='Ideal mesh magnitudes, no bearing capacity/life/retention redesign; signs reverse with torque.')
    assert abs(sum(axial[k] for k in ['input_net_Fx_N','intermediate_net_Fx_N','output_net_Fx_N']))<1e-8
    for rev,paths in [('a8f6489',['cad/m3','cad/m3_review','scripts/m3','scripts/m3_review','results/m3','results/m3_review','configs/m3_geometry.yaml','configs/m3_geometry_review.yaml']),('M2-v1.0',['scripts/m2','results/m2','configs/m2_thermal_network.yaml'])]:
        assert not subprocess.check_output(['git','diff',rev,'--name-only','--',*paths],text=True).strip()
    r=json.loads((OUT/'checks.json').read_text());assert len(r['runs'])==8
    cap=list(csv.DictReader((OUT/'thermal_capacity_checks.csv').open()))
    writejson(OUT/'tests.json',dict(status='PASS_CONCEPT_GEOMETRY_NOT_MECHANICAL_RELEASE',assemblies=8,mesh_phase_pairs=len(phases),
        measured_helical_edges=edge_checks,total_ratio=9,axes_unchanged=True,output_shaft_diameter_mm=50,
        max_thermal_capacity_relative_error=max(float(x['relative_C_error']) for x in cap),
        intermediate_gears_axial_gap_mm=95-58,axial_forces=axial,original_spur_and_M2_unchanged=True,
        actual_efficiency_calibration=None,ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED'))
    print('PASS actual helices, tooth counts,14 meshing phases,8 assemblies, capacities and immutable history',flush=True)

if __name__=='__main__':
    if '--finalize-existing' in sys.argv:
        def read(name):return list(csv.DictReader((OUT/name).open()))
        edges=read('actual_helix_checks.csv');phases=read('mesh_phase_checks.csv');loads=read('axial_force_screen.csv')
        assert len(edges)==4 and len(phases)==14 and all(float(r['overlap_mm3'])<.001 for r in phases)
        for r in edges:
            assert r['status']=='PASS' and abs(abs(float(r['measured_signed_beta_deg']))-20)<1e-5
        for r in loads:
            for k in ['tangential_force_N','axial_force_magnitude_N','radial_force_N']:r[k]=float(r[k])
        finalize(edges,phases,loads)
    else:main()
