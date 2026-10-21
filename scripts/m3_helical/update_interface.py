"""Regenerate final per-body checks and an independent helical heat-source map."""
import csv,json,math
import cadquery as cq
from helical_cad import ROOT,old
from run_geometry import csvout,writejson
OUT=ROOT/'results/m3_helical';CACHE=ROOT/'tmp/m3_helical'

def main():
    rows=list(csv.DictReader((OUT/'volume_mass_capacity.csv').open()));checks=[]
    for case in ['Case0','CaseA','CaseB','CaseC']:
        bodies={(r['variant'],r['part']):r for r in rows if r['case']==case}
        for variant,name in bodies:
            if variant!='full':continue
            f=bodies['full',name];t=bodies['thermal',name]
            error=abs(float(f['new_C_J_K'])-float(t['new_C_J_K']))/float(f['new_C_J_K'])
            assert error<1e-7
            checks.append(dict(case=case,part=name,full_volume_mm3=float(f['new_volume_mm3']),thermal_volume_mm3=float(t['new_volume_mm3']),relative_C_error=error))
    csvout(OUT/'thermal_capacity_checks.csv',checks)
    mass=[];regions={}
    for name,x0,x1 in [('input_shaft',33,58),('intermediate_shaft',95,127),('stage1_gear',33,58),('stage2_gear',95,127)]:
        sh=cq.Shape.importBrep(str(CACHE/f'{name}_full.brep'))
        before=cq.importers.importStep(str(ROOT/'cad/m3_review/revised_parts'/f'{name}.step')).val()
        slab=old.box(x0,x1,-500,500,-500,500)
        a=before.intersect(slab);b=sh.intersect(slab);regions[name]=b.Volume()*1e-9
        mass.append(dict(region=name+('_integral_pinion' if 'shaft' in name else ''),x0_mm=x0,x1_mm=x1,
            old_volume_mm3=a.Volume(),new_volume_mm3=b.Volume(),old_mass_kg=a.Volume()*7.8e-6,new_mass_kg=b.Volume()*7.8e-6,
            old_C_J_K=a.Volume()*7.8e-6*460,new_C_J_K=b.Volume()*7.8e-6*460,relative_volume_change=(b.Volume()-a.Volume())/a.Volume()))
    csvout(OUT/'gear_region_mass_capacity.csv',mass)
    mapping=json.loads((ROOT/'configs/M3_to_M4_mapping.json').read_text(encoding='utf-8'))
    mapping.update(version='M3-helical-1.0-draft',status='CONCEPT_ONLY_PRIOR_MECHANICAL_BLOCKERS_REMAIN',
        independent_revision_of='configs/M3_to_M4_mapping.json',geometry_folder='cad/m3_helical',
        loss_model='M1 unchanged; helical efficiency/temperature feedback NOT RECALIBRATED',
        simplification='Driven wheels equal-volume smooth; integral helical pinions retained on shafts')
    gearrows=mapping['sources']['reducer_gear'];total=sum(regions.values())
    for row in gearrows:row.update(volume_m3=regions[row['body']],fraction=regions[row['body']]/total)
    for source,items in mapping['sources'].items():assert abs(sum(r['fraction'] for r in items)-1)<1e-12,source
    assert mapping['actual_verified_contacts'] is None and mapping['actual_cooling'] is None
    writejson(ROOT/'configs/M3_helical_to_M4_mapping.json',mapping)
    # Check unchanged Case0 bodies using actual positions/bounds, not volume alone.
    same=[]
    for f in rows:
        name=f['part']
        if f['case']!='Case0' or f['variant']!='full' or name in ['input_shaft','intermediate_shaft','stage1_gear','stage2_gear','oil_inventory']:continue
        a=cq.importers.importStep(str(ROOT/'cad/m3_review/revised_parts'/f'{name}.step')).val()
        b=cq.Shape.importBrep(str(CACHE/f'{name}_full.brep'));aa=a.BoundingBox();bb=b.BoundingBox()
        err=max(abs(getattr(aa,k)-getattr(bb,k)) for k in ['xmin','xmax','ymin','ymax','zmin','zmax'])
        assert err<1e-6 and (a.Center()-b.Center()).Length<1e-6,(name,err)
        same.append(dict(part=name,max_bound_difference_mm=err,centroid_difference_mm=(a.Center()-b.Center()).Length,status='PASS_UNCHANGED'))
    csvout(OUT/'unchanged_component_positions.csv',same)
    print('PASS',len(checks),'full/thermal C comparisons;',len(same),'unchanged component positions; normalized independent source map')

if __name__=='__main__':main()
