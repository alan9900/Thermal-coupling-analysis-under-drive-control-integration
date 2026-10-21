"""Finite compressed exact native inputs; large result fields stay checksummed."""
import argparse,gzip,hashlib,json,shutil
from export_native_brake import RUN,ROOT
def main():
    p=argparse.ArgumentParser();p.add_argument('studies',nargs='+');a=p.parse_args()
    out=ROOT/'results/m4/model_input';out.mkdir(exist_ok=True)
    manifest=out/'native_input_packages.json';records=json.loads(manifest.read_text(encoding='utf-8-sig')) if manifest.exists() else {}
    for name in a.studies:
        folder=RUN/'studies'/name;receipt=ROOT/'results/m4/studies'/name/'native_archive_manifest.json'
        assert receipt.exists(),'Only completed actual inputs enter the completed-model package'
        proof=json.loads(receipt.read_text(encoding='utf-8-sig'));path=folder/'study.dat';dest=out/(name+'.dat.gz')
        with path.open('rb') as f:rawsha=hashlib.file_digest(f,'sha256').hexdigest()
        assert rawsha==proof['study.dat']['sha256']
        with path.open('rb') as src,dest.open('wb') as target:
            with gzip.GzipFile(filename='',mode='wb',fileobj=target,mtime=0,compresslevel=6) as z:shutil.copyfileobj(src,z)
        with gzip.open(dest,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==rawsha
        records[name]=dict(file=dest.name,raw_sha256=rawsha,raw_bytes=path.stat().st_size,gzip_bytes=dest.stat().st_size,
             gzip_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),qualification='Exact executed native input; numerical acceptance is separate')
        print(name,dest.stat().st_size,flush=True)
    manifest.write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':main()
