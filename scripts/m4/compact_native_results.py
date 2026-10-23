"""Lossless NTFS storage compression for terminal results, with byte hashes."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from export_native_brake import ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('studies',nargs='+');a=p.parse_args()
    out=ROOT/'results/m4/ntfs_storage_checks.json'
    records=json.loads(out.read_text(encoding='utf-8-sig')) if out.exists() else {}
    for name in a.studies:
        proof=json.loads((ROOT/'results/m4/studies'/name/'native_archive_manifest.json').read_text(encoding='utf-8-sig'))
        info=proof['study.rth'];path=Path(info['local_path'])
        result=subprocess.run(['compact.exe','/C','/EXE:XPRESS4K',str(path)],capture_output=True)
        assert result.returncode==0,result.stderr
        with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        assert h==info['sha256'] and path.stat().st_size==info['bytes']
        records[name]=dict(status='PASS_IDENTICAL_LOGICAL_RESULT_BYTES',bytes=info['bytes'],sha256=h,
            method='NTFS XPRESS4K storage flag only; no solver input or logical result byte changed.',
            native_output=result.stdout.decode('gbk',errors='replace'))
        out.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        print(name,'logical SHA256 unchanged',flush=True)

if __name__=='__main__':main()
