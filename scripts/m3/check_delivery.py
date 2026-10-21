"""Read-only independent archive checks; does not rerun or relabel CAD/physics."""
import csv,hashlib,json,subprocess
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m3'
def readj(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def digest(p):
    raw=p.read_bytes()
    if p.suffix in ['.py','.yaml','.md','.csv','.json','.txt','.svg']:raw=raw.decode('utf-8-sig').replace('\r\n','\n').encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
def main():
    cfg=yaml.safe_load((ROOT/'configs/m3_geometry.yaml').read_text(encoding='utf-8'))
    assert all(x is None for x in cfg['unknown_actual'].values())
    g=readj(OUT/'geometry_checks.json');t=readj(OUT/'tests.json');a=readj(OUT/'analysis_checks.json');d=readj(OUT/'document_checks.json')
    assert all(x['status']=='PASS' for x in [g,t,a,d]) and d['visual_inspection']=='PASS'
    assert g['cad_executed'] and g['case_count']==4 and t['test_group_count']==8 and t['gear_phase_samples']==18
    manifest=readj(OUT/'step_manifest.json');assert manifest['count']==56
    for name,record in manifest['files'].items():
        p=ROOT/name;assert p.stat().st_size==record['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],name
    for name,s in d['document_sha256'].items():assert hashlib.sha256((ROOT/'reports'/name).read_bytes()).hexdigest()==s,name
    overlaps=rows(OUT/'interference_checks.csv');assert len(overlaps)==283
    assert all(float(x['common_volume_mm3'])<.001 and x['status']=='PASS' for x in overlaps)
    masses=rows(OUT/'mass_heat_capacity.csv');assert len(masses)==144
    for x in masses:
        m=cfg['materials'][x['material']];mass=float(x['volume_mm3'])*1e-9*m['rho_kg_m3']
        assert abs(mass-float(x['mass_kg']))<1e-9
        assert abs(mass*m['cp_J_kgK']-float(x['heat_capacity_J_K']))<1e-7
    for x in rows(OUT/'thermal_resistance_candidates.csv'):
        assert not x['R_contact_K_W']
        expected=float(x['length_m'])/float(x['k_W_mK'])/float(x['area_m2']);assert abs(expected-float(x['R_bulk_K_W']))<1e-10
    span=rows(OUT/'geometry_range_checks.csv');assert len(span)==2187 and sum(x['status']=='REJECT_GEOMETRY' for x in span)==729
    assert len(rows(OUT/'gear_phase_checks.csv'))==18
    for x in rows(OUT/'radiation_geometry.csv'):
        assert abs(sum(float(x[k]) for k in ['escape','case_direct','shield_1','shield_2','other_fixed'])-1)<1e-12
        assert abs(float(x['emitter_exposed_area_m2'])*float(x['case_direct'])-float(x['direct_AF_m2']))<1e-12
        assert float(x['refinement_difference'])<.01
    protected=['configs/baseline_vehicle.yaml','configs/m1_heat_sources.yaml','configs/m1_source_partition.yaml','configs/m2_thermal_network.yaml','data/raw/m0','data/raw/m1','data/raw/m2','scripts/m0','scripts/m1','scripts/m2','results/m0','results/m1','results/m2','reports/M0_report.md','reports/M1_report.md','reports/M2_report.md','reports/M2_report.docx','reports/M2_report.pdf']
    assert not subprocess.check_output(['git','diff','M2-v1.0','--name-only','--',*protected],text=True).strip()
    assert subprocess.check_output(['git','rev-parse','M2-v1.0^{}'],text=True).strip()==cfg['metadata']['baseline_commit']
    source=[ROOT/'configs/m3_geometry.yaml',ROOT/'data/raw/m3/manifest.json']+sorted((ROOT/'scripts/m3').glob('*'))
    output=[p for p in OUT.rglob('*') if p.is_file() and p.name!='delivery_checks.json']+list((ROOT/'cad/m3').rglob('*.step'))+list((ROOT/'reports').glob('M3*'))
    record=dict(status='PASS',review_date='2026-10-20',model_commit=g['source_commit'],archive_preparation_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_and_script_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in source if p.is_file()},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(output)},hash_definition='UTF-8 text normalized LF without BOM; STEP and other binaries exact bytes',
        M0_M1_M2_protected_unchanged=True,M3_approval='PENDING',M3_tag='NOT CREATED',M4='NOT STARTED',
        limits='Concept geometry/elementary screens only; actual installability, fatigue, bearing life, contact/cooling and temperature calibration unverified.')
    (OUT/'delivery_checks.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Independent delivery PASS:',manifest['count'],'STEP, 144 mass rows, 283 pair checks, 2187 range rows, original M2 protected.')
if __name__=='__main__':main()
