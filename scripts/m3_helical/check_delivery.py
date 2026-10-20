"""Byte manifest and Git blob verification of the bounded helical package."""
import csv,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m3_helical'
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    if '--verify-git' in sys.argv:
        sha=sys.argv[sys.argv.index('--verify-git')+1];m=json.loads((OUT/'delivery_manifest.json').read_text())
        for p,h in m['sha256'].items():
            b=subprocess.check_output(['git','show',f'{sha}:{p}'],cwd=ROOT)
            assert digest(b)==h,p
        r=dict(status='PASS',commit=sha,verified_git_blobs=len(m['sha256']))
        (OUT/'git_blob_checks.json').write_text(json.dumps(r,indent=2)+'\n');print(r);return
    t=json.loads((OUT/'tests.json').read_text());g=json.loads((OUT/'checks.json').read_text());d=json.loads((OUT/'document_checks.json').read_text())
    assert t['assemblies']==8 and t['mesh_phase_pairs']==14 and len(g['runs'])==8
    assert d['visual_inspection']=='PASS' and d['editable_math_objects']==5 and d['figures']==5
    capacity=list(csv.DictReader((OUT/'thermal_capacity_checks.csv').open()))
    same=list(csv.DictReader((OUT/'unchanged_component_positions.csv').open()))
    assert len(capacity)==541 and len(same)==124
    for rev,paths in [('a8f6489',['cad/m3','cad/m3_review','scripts/m3','scripts/m3_review','results/m3','results/m3_review','configs/m3_geometry.yaml','configs/m3_geometry_review.yaml','configs/M3_to_M4_mapping.json','reports/M3_geometry_review.md','reports/M3_geometry_review.docx','reports/M3_geometry_review.pdf']),('M2-v1.0',['cad/m2','scripts/m2','results/m2','configs/m2_thermal_network.yaml','reports/M2_report.md','reports/M2_report.docx','reports/M2_report.pdf'])]:
        assert not subprocess.check_output(['git','diff',rev,'--name-only','--',*paths],cwd=ROOT,text=True).strip()
    files=list((ROOT/'cad/m3_helical').rglob('*'))+list((ROOT/'scripts/m3_helical').glob('*.py'))+list((ROOT/'data/raw/m3_helical').glob('*'))
    files+=list(OUT.glob('*'))+[ROOT/'configs/m3_helical.yaml',ROOT/'configs/M3_helical_to_M4_mapping.json',ROOT/'scripts/m3_helical/README.md']
    files+=list((ROOT/'reports').glob('M3_helical_revision.*'))+[ROOT/'reports/M3_HELICAL_CHECKLIST.md']
    ignored={'delivery_manifest.json','git_blob_checks.json'}
    files=[p for p in files if p.is_file() and p.name not in ignored and '__pycache__' not in p.parts]
    assert len([p for p in files if p.suffix=='.step'])==18
    assert max(p.stat().st_size for p in files)<100_000_000
    result=dict(status='PASS_BOUNDED_CONCEPT_DELIVERY',files=len(files),step_files=18,capacity_checks=541,unchanged_positions=124,
        code_commit_at_check=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        old_spur_and_archived_M2_preserved=True,mechanical_release='BLOCKED',ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED',
        sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(set(files))})
    (OUT/'delivery_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items() if k!='sha256'})
if __name__=='__main__':main()
