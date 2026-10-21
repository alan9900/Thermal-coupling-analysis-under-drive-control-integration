"""SI import audit; native IGeoData stays mm even when UI is MKS."""
import csv,json,math,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4';RUN=Path('E:/ansys_runs/m4_case0_20261021')
def main():
    native=json.loads((RUN/'body_mesh_audit.json').read_text());groups=collections.defaultdict(list)
    for r in native:groups[r['name']].append(r)
    expected=list(csv.DictReader((ROOT/'results/m3_helical/volume_mass_capacity.csv').open()))
    expected={r['part']:float(r['new_volume_mm3'])*1e-9 for r in expected if r['case']=='Case0' and r['variant']=='thermal'}
    assert len(native)==131 and len(groups)==129
    rows=[]
    for name,bodies in groups.items():
        v=sum(float(r['geo_Volume'])*1e-9 for r in bodies)
        shown=sum(float(r['volume'].split()[0]) for r in bodies)
        assert abs(v-shown)<1e-11, 'mm3/m3 conversion failed'
        rows.append(dict(part=name,native_solids=len(bodies),CAD_volume_m3=expected[name],Mechanical_reported_volume_m3=v,
            relative_difference=(v-expected[name])/expected[name],status='COMPARE_REPORTED_GEOMETRY_VOLUME_NOT_MESH_INTEGRAL'))
    with (OUT/'import_volume_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Preserve first failed attempt; write a corrected SI interface separately.
    faces=json.loads((RUN/'face_audit.json').read_text())
    for r in faces:
        if 'centroid' in r:
            r['centroid_mm']=r.pop('centroid');r['area_m2']*=1e-6
        r['geometry_database_length_unit']='mm'
    (OUT/'face_regions_SI.json').write_text(json.dumps(faces,indent=2)+'\n')
    annuli={}
    for label,x in [('near',205),('far',227)]:
        selected=[r for r in faces if r['body']=='brake_disc_hat' and r['surface_type']=='GeoSurfacePlane'
            and abs(r['centroid_mm'][0]-x)<.001 and r['area_m2']>.02]
        assert len(selected)==1,(label,selected)
        annuli[label]=dict(face_id=selected[0]['id'],area_m2=selected[0]['area_m2'],disc_power_fraction=.5)
    (OUT/'brake_friction_faces.json').write_text(json.dumps(annuli,indent=2)+'\n')
    result=dict(status='PASS_UNIT_AND_BODY_COUNT_AUDIT',parts=129,solids=131,oil_solids=3,
        native_geometry_unit='mm/mm2/mm3',source_unit='W',SI_conversion_explicit=True,
        max_relative_reported_volume_difference=max(abs(r['relative_difference']) for r in rows),
        reported_volume_warning='ANSYS geometry property differs from OCCT; do not silently equate to exact FE integrated volume. Mesh integral audit still required.',
        friction_faces=annuli)
    (OUT/'import_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
