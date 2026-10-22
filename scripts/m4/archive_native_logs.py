"""Byte-preserving gzip for completed large log copies; retain native originals.

Avoid multi-million-line PR diffs. Never touch an executing log or its native
canonical file. The finite repository copy is replaced only after two exact
hash checks and a round-trip decompression check.
"""
import gzip,hashlib,json,shutil
from export_native_brake import ROOT,RUN

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    out=ROOT/'results/m4';manifest=out/'native_log_packages.json'
    records=json.loads(manifest.read_text(encoding='utf-8-sig')) if manifest.exists() else {}
    candidates=[]
    for proof in (out/'studies').glob('*/native_archive_manifest.json'):
        raw=proof.parent/'study.out'
        if not raw.exists():continue
        data=json.loads(proof.read_text(encoding='utf-8-sig'))['study.out']
        candidates.append((raw,__import__('pathlib').Path(data['local_path']),data['sha256']))
    for raw in (out/'meshes').glob('native_shape_*.out'):
        mesh=raw.stem.replace('native_shape_','');native=RUN/'shape_checks'/mesh/'audit.out'
        candidates.append((raw,native,digest(native)))
    for raw,native,expected in candidates:
        if raw.stat().st_size<1_000_000:continue
        assert raw.resolve().is_relative_to(out.resolve()) and native.resolve().is_relative_to(RUN.resolve())
        assert raw.resolve()!=native.resolve() and digest(raw)==digest(native)==expected
        zpath=raw.with_suffix(raw.suffix+'.gz')
        with raw.open('rb') as src,zpath.open('wb') as target:
            with gzip.GzipFile(filename='',mode='wb',fileobj=target,mtime=0,compresslevel=6) as z:shutil.copyfileobj(src,z)
        with gzip.open(zpath,'rb') as z:assert hashlib.file_digest(z,'sha256').hexdigest()==expected
        key=str(zpath.relative_to(ROOT)).replace('\\','/')
        records[key]=dict(raw_bytes=raw.stat().st_size,raw_sha256=expected,gzip_bytes=zpath.stat().st_size,
            gzip_sha256=digest(zpath),native_original=str(native),verification='Native original matches; gzip round-trip identical; only redundant repository plaintext copy replaced.')
        manifest.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        raw.unlink()
        print(key,records[key]['raw_bytes'],'to',records[key]['gzip_bytes'])
    manifest.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
