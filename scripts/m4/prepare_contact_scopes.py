"""Restrict finite contacts to CAD-derived interfaces, not every body face.

Original M3 topology/dimensions remain immutable. Missing mappings fail closed.
"""
import csv,json,sys,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4';RUN=Path('E:/ansys_runs/m4_case0_20261021')
sys.path.insert(0,str(ROOT/'scripts/m3_helical'))
from helical_cad import build
def main():
    native=json.loads((OUT/'face_regions_SI.json').read_text(encoding='utf-8-sig'));by={}
    for r in native:by.setdefault(r['body'],[]).append(r)
    raw=json.loads((RUN/'pilot_contacts.json').read_text(encoding='utf-8-sig'))
    cache=ROOT/'tmp/m3_helical'
    names={r[k] for r in raw for k in ['from','to']}
    if all((cache/f'{n}_thermal.brep').is_file() for n in names):
        parts={n:cq.Shape.importBrep(str(cache/f'{n}_thermal.brep')) for n in names}
    else:parts=build('Case0',True)['parts']
    rows=[];unmapped=[]
    def native_id(name,f):
        center=f.Center().toTuple();area=f.Area()*1e-6
        candidates=[]
        for r in by[name]:
            err=math.dist(center,r['centroid_mm']);rel=abs(area-r['area_m2'])/max(area,1e-12)
            if err<1 and rel<.03:candidates.append((err+rel*10,r['id']))
        if not candidates:
            unmapped.append(dict(body=name,centroid_mm=center,area_m2=area));return None
        return min(candidates)[1]
    for r in raw:
        a,b=r['from'],r['to'];A,B=parts[a],parts[b]
        scopes=[]
        mode='NOMINAL_CAD_CONTACT'
        gap=.3 if {a,b}=={'motor_stator','motor_winding'} else (.8 if {a,b}=={'motor_rotor_other','motor_stator'} else 1e-5)
        if gap>1e-4:mode='S3_GAP_EQUIVALENT_FINITE_H'
        for name,shape,other in [(a,A,B),(b,B,A)]:
            selected=[]
            for f in shape.Faces():
                if f.distance(other)>gap:continue
                if gap<1e-4 and f.intersect(other).Area()<1e-4:continue
                if {a,b}=={'motor_rotor_other','motor_stator'} and f.geomType()!='CYLINDER':continue
                ident=native_id(name,f)
                if ident is not None:selected.append(ident)
            scopes.append(sorted(set(selected)))
        if a=='oil_inventory' and b=='gear_case_rear':
            mode='S3_FINITE_FILM_ACROSS_2MM_INVENTORY_GAP'
            scopes=[[r['id'] for r in by[a] if abs(r['centroid_mm'][2]+102)<.01],
                    [r['id'] for r in by[b] if abs(r['centroid_mm'][2]+104)<.01]]
        rows.append(dict(source=a,target=b,source_face_ids=scopes[0],target_face_ids=scopes[1],h_W_m2K=r['h_W_m2K'],
            classification=mode,status='PASS_SCOPE_CANDIDATE' if all(scopes) else 'BLOCKED_EMPTY_SCOPE'))
    result=dict(status='BLOCKED' if unmapped or any(r['status'].startswith('BLOCKED') for r in rows) else 'PASS_SCOPE_CANDIDATES',
        contacts=rows,unmapped_faces=unmapped,limitation='Geometric face correspondence only; actual conductance and gap closure uncalibrated')
    for p in [OUT/'contact_scope_candidates.json',RUN/'contact_scope_candidates.json']:p.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],'contacts',len(rows),'unmapped faces',len(unmapped),'empty',[(r['source'],r['target']) for r in rows if r['status'].startswith('BLOCKED')])
if __name__=='__main__':main()
