"""Prepare a standalone, cache-independent native input in a fresh ASCII folder.

Exact executed bytes are retained separately. Removing only VFOPT,READ asks
ANSYS to recompute the same view factors. Preparation is not proof of a new solve.
"""
import argparse, gzip, hashlib, json, re, shutil
from export_native_brake import ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('study');p.add_argument('--out',required=True)
    a=p.parse_args();out=__import__('pathlib').Path(a.out).resolve()
    assert str(out).isascii(), 'Use an ASCII native run folder'
    records=json.loads((ROOT/'results/m4/model_input/native_input_packages.json').read_text(encoding='utf-8-sig'))
    record=records[a.study];package=ROOT/'results/m4/model_input'/record['file']
    assert hashlib.sha256(package.read_bytes()).hexdigest()==record['gzip_sha256']
    raw=gzip.decompress(package.read_bytes())
    assert len(raw)==record['raw_bytes'] and hashlib.sha256(raw).hexdigest()==record['raw_sha256']
    out.mkdir(parents=True,exist_ok=False)
    (out/'executed_original.dat').write_bytes(raw)
    text=raw.decode('ascii')
    pattern=r'(?im)^vfopt\s*,\s*read\s*,[^\r\n]*'
    portable,n=re.subn(pattern,'! Reproduction: recompute native view factors; no external binary cache',text)
    assert n in [0,1]
    derived=portable.encode('ascii');(out/'study.dat').write_bytes(derived)
    source=ROOT/'results/m4/studies'/a.study
    meta=json.loads((source/'study_settings.json').read_text(encoding='utf-8-sig'))
    meta['reproduction_source_study']=a.study
    meta['reproduction_source_input_sha256']=record['raw_sha256']
    meta['input_sha256']=meta['actual_native_input_sha256']=hashlib.sha256(derived).hexdigest()
    meta.pop('viewfactor_reuse_from',None);meta.pop('viewfactor_sha256',None)
    meta.pop('execution_status',None)
    meta['status']='PREPARED_NOT_EXECUTED'
    meta['capacity_weights']=str(ROOT/'results/m4/studies'/out.name/'FE_capacity_weights.npz')
    meta['reproduction_change']='Only remove VFOPT,READ cache dependency. FE model, heat tables, material/contact/BC/load steps unchanged.'
    (out/'study_settings.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    if (source/'source_intervals.csv').exists():shutil.copy2(source/'source_intervals.csv',out/'source_intervals.csv')
    receipt=dict(status='PASS_PREPARATION_ONLY_NOT_EXECUTED',study=a.study,output=str(out),
        removed_external_cache_reads=n,executed_original_sha256=record['raw_sha256'],
        prepared_input_sha256=meta['actual_native_input_sha256'],
        note='Run ANSYS and recheck expected time sets, energy and convergence. A prepared file is not a completed solution.')
    (out/'preparation_checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
