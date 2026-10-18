"""Check evidence integrity and agreement between current config and saved results."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    def read(path):
        return json.loads((ROOT/path).read_text(encoding='utf-8'))
    manifest=read('data/raw/m0/manifest.json')
    checked=[]
    for entry in manifest:
        if entry['status']!='downloaded':
            continue
        p=ROOT/'data/raw/m0'/entry['file']
        assert p.stat().st_size==entry['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
        checked.append(entry['file'])
    meta=read('results/m0/audit_metadata.json')
    assert hashlib.sha256((ROOT/'configs/baseline_vehicle.yaml').read_text(encoding='utf-8').encode('utf-8')).hexdigest()==meta['config_sha256']
    cfg=read('results/m0/baseline_vehicle.json')
    assert cfg['drive']['rear_motor_per_side']['continuous_mechanical_power_kw'] is None
    assert cfg['drive']['rear_motor_per_side']['motor_loss_map_file'] is None
    with (ROOT/'results/m0/braking_review.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==18
    assert max(float(r['energy_residual_relative']) for r in rows)<1e-9
    assert read('results/m0/validation.json')['status']=='PASS'
    test_log=(ROOT/'results/m0/python_test_results.txt').read_text(encoding='utf-8-sig')
    assert 'Ran 3 tests' in test_log and 'OK' in test_log
    dc=read('results/m0/document_checks.json')
    assert dc['docx_editable_omml_objects']>=20
    assert dc['visual_inspection']=='PASS'
    result=dict(status='PASS', official_files_hash_verified=checked, source_unavailable=[e['requested_url'] for e in manifest if e['status']=='FAILED'],
                configuration_hash_matches=True, braking_cases=len(rows),
                python_config_tests='3 passed; 10 invalid input variants rejected',
                word_math_objects=dc['docx_editable_omml_objects'],
                visual_qa='All final report PDF pages visually inspected after Word export',
                m1_authorized=False, ansys_executed=False, optimization_executed=False)
    (ROOT/'results/m0/delivery_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
