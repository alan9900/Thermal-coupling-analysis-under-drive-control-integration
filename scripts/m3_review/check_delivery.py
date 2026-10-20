"""Verify bounded deliverables/hashes and old-version protection before push."""
import csv,hashlib,json,subprocess
from pathlib import Path
from review_cad import ROOT
from run_geometry import writejson
OUT=ROOT/'results/m3_review'
def main():
    g=json.loads((OUT/'geometry_checks.json').read_text());tests=json.loads((OUT/'tests.json').read_text());doc=json.loads((OUT/'document_checks.json').read_text());mapping=json.loads((ROOT/'configs/M3_to_M4_mapping.json').read_text())
    assert g['status']=='PASS_GEOMETRY_ONLY' and len(g['runs'])==10
    assert tests['test_group_count']==16 and tests['status'].startswith('PASS')
    assert doc['visual_inspection']=='PASS' and doc['editable_math_objects']==8 and doc['figures']==7
    manifest=json.loads((OUT/'step_manifest.json').read_text());total=0
    for name,row in manifest['files'].items():
        path=ROOT/name;assert path.stat().st_size==row['bytes'] and row['bytes']<100_000_000
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],name
        total+=row['bytes']
    assert total==manifest['total_bytes'] and len(manifest['files'])==144
    source=json.loads((ROOT/'data/raw/m3_review/manifest.json').read_text());snapshots=0
    for r in source:
        if r.get('file'):
            assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256'];snapshots+=1
    assert snapshots==3
    for ext,h in doc['document_sha256'].items():assert hashlib.sha256((ROOT/'reports'/f'M3_geometry_review.{ext}').read_bytes()).hexdigest()==h
    assert mapping['actual_verified_contacts'] is None and mapping['actual_cooling'] is None
    for rows in mapping['sources'].values():assert abs(sum(r['fraction'] for r in rows)-1)<1e-12
    for baseline,paths in [('79c6a4f',['cad/m3','scripts/m3','results/m3','configs/m3_geometry.yaml','reports/M3_report.md','reports/M3_report.docx','reports/M3_report.pdf']),('M2-v1.0',['scripts/m2','results/m2','configs/m2_thermal_network.yaml','reports/M2_report.md','reports/M2_report.docx','reports/M2_report.pdf'])]:
        assert not subprocess.check_output(['git','diff',baseline,'--name-only','--',*paths],cwd=ROOT,text=True).strip()
    # Fix ambiguous legacy provenance metadata without pretending to rerun CAD.
    # Original generator captured HEAD each time it wrote a result; launch is
    # evidenced by the command immediately after commit700edf0, not later HEAD.
    if 'source_commit' in g:
        g['source_commit_at_result_write_legacy']=g.pop('source_commit')
        g['source_commit_at_launch']=subprocess.check_output(['git','rev-parse','700edf0'],cwd=ROOT,text=True).strip()
        g['provenance_correction']='Metadata only: legacy generator sampled HEAD at each result write. CAD process launched700edf0; subsequent changes added assertions/metadata and audit scripts. Current source vs exported baseline volume regression PASS. No CAD rerun is implied.'
        writejson(OUT/'geometry_checks.json',g)
    paths=[]
    for folder in [ROOT/'scripts/m3_review',ROOT/'cad/m3_review',ROOT/'data/raw/m3_review',OUT]:
        paths += [p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name not in ['delivery_checks.json','delivery_manifest.json']]
    paths += [ROOT/'configs/m3_geometry_review.yaml',ROOT/'configs/M3_to_M4_mapping.json',ROOT/'reports/M3_GEOMETRY_REVIEW_CHECKLIST.md']+[ROOT/'reports'/f'M3_geometry_review.{ext}' for ext in ['md','docx','pdf']]
    writejson(OUT/'delivery_manifest.json',{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    writejson(OUT/'delivery_checks.json',dict(status='PASS_DELIVERY_WITH_ENGINEERING_BLOCKERS',file_count=len(paths),step_files=len(manifest['files']),step_bytes=total,source_snapshots=snapshots,
        geometry_regression_groups=tests['test_group_count'],archived_M2_and_original_M3_unchanged=True,document_pages=doc['pdf_pages'],editable_math=8,
        mechanical_release='BLOCKED',calibrated_thermal_release='BLOCKED',ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED',M3_tag='NOT CREATED',
        checked_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
    print('Delivery checks PASS:',len(paths),'files;',len(manifest['files']),'STEP;',tests['test_group_count'],'audit groups. Engineering blockers retained.')
if __name__=='__main__':main()
