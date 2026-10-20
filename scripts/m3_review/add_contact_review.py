"""Supplemental named contacts from exported refined CAD; no solver run."""
import csv
import cadquery as cq
from review_cad import ROOT,box
from run_geometry import csvout
OUT=ROOT/'results/m3_review';CAD=ROOT/'cad/m3_review/revised_parts'
def main():
    pairs=[('motor_winding','motor_stator','BLOCKED_ENDRING_INSULATION_CONTACT_LAW'),('hub_removable_sleeve','output_shaft','BLOCKED_PRESS_FIT_THERMAL_CONTACT'),
        ('hub_removable_sleeve','disc_hub','KEYED_JOINT_CONTACT_UNKNOWN'),('halfshaft_removable_sleeve','output_shaft','BLOCKED_PRESS_FIT_THERMAL_CONTACT'),
        ('halfshaft_removable_sleeve','output_halfshaft_flange','KEYED_JOINT_CONTACT_UNKNOWN'),('disc_hub','hub_front_axial_collar','CLAMP_RETENTION_UNKNOWN'),
        ('disc_hub','hub_rear_axial_collar','CLAMP_RETENTION_UNKNOWN'),('pad_near','brake_disc_hat','RUNNING_GAP_0_5MM_TRANSIENT_CONTACT_UNKNOWN'),
        ('pad_far','brake_disc_hat','RUNNING_GAP_0_5MM_TRANSIENT_CONTACT_UNKNOWN'),('motor_water_jacket','motor_case','BLOCKED_NO_FLOW_PORTS_FILM_UNKNOWN')]
    for ax in ['input','intermediate','output']:
        for end in ['front','rear']:
            pairs += [(ax+'_'+end+'_seal',ax+'_'+end+'_outer_retainer','SEAL_CARRIER_CONTACT_UNKNOWN'),(ax+'_'+end+'_seal',ax+'_shaft','ROTATING_LIP_DRAG_AND_CONTACT_UNKNOWN')]
    parts={};rows=[]
    for a,b,status in pairs:
        for n in [a,b]:
            if n not in parts:parts[n]=cq.importers.importStep(str(CAD/(n+'.step'))).val()
        A=parts[a];B=parts[b];dist=A.distance(B);area=sum(f.intersect(B).Area() for f in A.Faces())*1e-6 if dist<1e-5 else 0
        rows.append(dict(case='Case0',diameter_mm=50,variant='full',a=a,b=b,distance_mm=dist,nominal_contact_area_m2=area,measured_contact_h_W_m2K=None,status=status))
    csvout(OUT/'supplemental_contact_pairs.csv',rows)
    regions=[]
    for name,x0,x1 in [('input_shaft',33,58),('intermediate_shaft',95,127)]:
        sh=cq.importers.importStep(str(CAD/(name+'.step'))).val();zone=sh.intersect(box(x0,x1,-500,500,-500,500))
        regions.append(dict(body=name,region=name+'_integral_pinion',x_min_mm=x0,x_max_mm=x1,volume_m3=zone.Volume()*1e-9,classification='S3_SOURCE_ZONE_REQUIRES_SOLVER_BODY_PARTITION'))
    csvout(OUT/'source_regions.csv',regions)
    boundaries=[]
    for name,predicate in [('brake_disc_hat','friction near: x=205, nx<0, r>=88mm; far: x=227, nx>0, r>=85mm'),
        ('motor_water_jacket','wet boundary = contact to motor_case; no flow ports; apply bulk-film hypothesis only'),
        ('gear_case_rear','radiation receiver SELECTED exterior plane x=160, nx>0; internal surfaces excluded'),
        ('pad_near','moving friction face x=204.5, gap0.5 to disc; actual hydraulic closure unknown'),
        ('pad_far','moving friction face x=227.5, gap0.5 to disc; actual hydraulic closure unknown')]:
        boundaries.append(dict(body=name,predicate_mm=predicate,actual_boundary_parameter=None,status='NAMED_SELECTION_PLAN_ANSYS_NOT_EXECUTED'))
    csvout(OUT/'boundary_selection_plan.csv',boundaries)
    print('Supplemental CAD contact checks',len(rows),'; unknown laws retained.')
if __name__=='__main__':main()
