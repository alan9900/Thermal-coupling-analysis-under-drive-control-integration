"""Cosine-weighted ray intersections with revised STEP B-rep occluders.
Only disc back exposed annulus -> case plane x160; NOT full radiosity.
"""
import math,json
import numpy as np
import cadquery as cq
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Lin,gp_Pnt,gp_Dir
from review_cad import ROOT,box
from analyze_geometry import rays
from cad_model import config
from run_geometry import csvout,writejson
OUT=ROOT/'results/m3_review';CAD=ROOT/'cad/m3_review'

def main():
    receiver=cq.importers.importStep(str(CAD/'revised_parts/gear_case_rear.step')).val()
    area=sum(f.Area()*1e-6 for f in receiver.Faces() if abs(f.Center().x-160)<1e-6 and f.normalAt().x>.99)
    result=[];n=8192;o,d=rays(config(),n)
    for case in ['Case0','CaseA','CaseB','CaseC']:
        print('BREP RAYS',case,flush=True)
        shape=cq.importers.importStep(str(CAD/f'{case}_d50_full.step')).val()
        # Include caps, keys, supports, caliper, hat, hub and duct. Exclude only
        # the emitter plane at205 and case receiver plane at160 themselves.
        occluder=shape.intersect(box(160.0001,204.9999,-500,500,-400,400))
        inter=IntCurvesFace_ShapeIntersector();inter.Load(occluder.wrapped,1e-7)
        hits=[]
        for origin,direction in zip(o,d):
            t=(160-origin[0])/direction[0];pt=origin+t*direction
            target=receiver.isInside(cq.Vector(159.999,pt[1],pt[2]),1e-7)
            if target:
                inter.Perform(gp_Lin(gp_Pnt(*origin),gp_Dir(*direction)),.00001,float(t)-.0002)
                target=inter.NbPnt()==0
            hits.append(target)
        F=float(np.mean(hits));coarse=float(np.mean(hits[:2048]));se=math.sqrt(F*(1-F)/n)
        assert abs(F-coarse)<.06
        result.append(dict(case=case,samples=n,coarse_samples=2048,F_direct=F,F_coarse=coarse,refinement_difference=abs(F-coarse),sampling_standard_error=se,
            disc_exposed_emitter_area_m2=math.pi*(140**2-88**2)*1e-6,receiver_plane_area_m2=area,AF_m2=F*math.pi*(140**2-88**2)*1e-6,
            classification='GEOMETRIC_PREDICTION_S3_NOT_THERMAL_COOLING_RESULT'))
        csvout(OUT/'radiation_geometry.csv',result)
    # Analytic equal coaxial disks: validates cosine emission / length units.
    rng=np.random.default_rng(15);q=rng.random((131072,4));rr=100*np.sqrt(q[:,0]);a=2*np.pi*q[:,1];t=50/np.sqrt(1-q[:,2]);y=rr*np.cos(a)+t*np.sqrt(q[:,2])*np.cos(2*np.pi*q[:,3]);z=rr*np.sin(a)+t*np.sqrt(q[:,2])*np.sin(2*np.pi*q[:,3]);obs=float(np.mean(y*y+z*z<=100**2));S=2.25;exact=(S-math.sqrt(S*S-4))/2
    assert abs(obs-exact)<.005
    writejson(OUT/'radiation_checks.json',dict(status='PASS_SELECTED_FACE_GEOMETRY_ONLY',disk_exact=exact,disk_sampled=obs,disk_error=abs(obs-exact),case_count=4,
        method='Actual revised STEP B-rep obstruction intersections, seeded uniform area/cosine hemisphere rays, selected receiver plane x160 only',
        excluded_physics=['case side faces as receivers','multiple reflections/re-emission','emissivity and temperature dependence','convection / air direction'],
        legacy_M3_F_not_reused=True,thermal_prediction='NOT EXECUTED'))
    print('View factors',[x['F_direct'] for x in result],flush=True)

if __name__=='__main__':main()
