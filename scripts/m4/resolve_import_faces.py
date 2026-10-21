"""Explicitly audit small B-spline import-area discrepancies, not empty scopes.

Only the oil/second-wheel cut interface is eligible for the wider documented
tolerance. Native imported areas, not original CAD areas, enter the FE model.
This is an S3 film geometry approximation, not a calibrated contact result.
"""
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/m4'
def main():
    original=json.loads((OUT/'contact_scope_candidates.json').read_text())
    native=json.loads((OUT/'face_regions_SI.json').read_text())
    records=[];remaining=[]
    for f in original['unmapped_faces']:
        name=f['body'];choices=[]
        for n in native:
            if n['body']!=name or name not in ['oil_inventory','stage2_gear']:continue
            distance=math.dist(f['centroid_mm'],n['centroid_mm'])
            rel=abs(f['area_m2']-n['area_m2'])/f['area_m2']
            if distance<1 and rel<.10:choices.append((distance+10*rel,n,distance,rel))
        choices.sort(key=lambda t:t[0])
        if len(choices)!=1:
            remaining.append(dict(face=f,eligible_candidates=len(choices)));continue
        _,n,d,a=choices[0]
        records.append(dict(body=name,native_face_id=n['id'],centroid_distance_mm=d,
            relative_area_difference=a,CAD_area_m2=f['area_m2'],native_area_m2=n['area_m2'],
            classification='S3_IMPORTED_SMALL_WET_FACE_APPROXIMATION'))
    resolved=json.loads(json.dumps(original))
    for c in resolved['contacts']:
        if {c['source'],c['target']}=={'oil_inventory','stage2_gear'}:
            for side,body in [('source',c['source']),('target',c['target'])]:
                c[side+'_face_ids']=sorted(set(c[side+'_face_ids']+[r['native_face_id'] for r in records if r['body']==body]))
            c['classification']='S3_FINITE_OIL_FILM_NATIVE_IMPORTED_FACE_AREAS'
    resolved['unmapped_faces']=remaining;resolved['import_mapping_audit']=records
    resolved['status']='BLOCKED' if remaining else 'PASS_GEOMETRIC_SCOPES_ONLY'
    resolved['mapping_tolerance']=dict(primary_centroid_mm=1,primary_area_relative=.03,
        small_wet_cut_only_centroid_mm=1,small_wet_cut_only_area_relative=.10,
        require_unique_candidate=True,note='Native curved-face area is approximate; preserve discrepancy, do not overwrite CAD mass.')
    for p in [OUT/'contact_scope_resolved.json',Path('E:/ansys_runs/m4_case0_20261021/contact_scope_resolved.json')]:
        p.write_text(json.dumps(resolved,indent=2)+'\n')
    print(resolved['status'],'resolved',len(records),'still unmapped',len(remaining))
if __name__=='__main__':main()
