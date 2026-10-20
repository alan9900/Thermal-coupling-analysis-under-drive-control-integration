"""Supplemental named contacts from exported refined CAD; no solver run."""
import csv
import cadquery as cq
from review_cad import ROOT
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
    print('Supplemental CAD contact checks',len(rows),'; unknown laws retained.')
if __name__=='__main__':main()
