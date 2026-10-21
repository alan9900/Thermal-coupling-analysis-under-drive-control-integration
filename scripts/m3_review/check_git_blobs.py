"""Verify committed evidence bytes against the saved pre-commit manifest."""
import hashlib,json,subprocess,sys
from review_cad import ROOT
from run_geometry import writejson
def main():
    rev=sys.argv[1] if len(sys.argv)>1 else 'HEAD'
    commit=subprocess.check_output(['git','rev-parse',rev],cwd=ROOT,text=True).strip()
    manifest=json.loads(subprocess.check_output(['git','show',commit+':results/m3_review/delivery_manifest.json'],cwd=ROOT))
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for path,expected in manifest.items():
            proc.stdin.write((commit+':'+path+'\n').encode('utf-8'));proc.stdin.flush()
            header=proc.stdout.readline().split();assert len(header)==3 and header[1]==b'blob',(path,header)
            n=int(header[2]);data=proc.stdout.read(n);assert len(data)==n and proc.stdout.read(1)==b'\n'
            assert hashlib.sha256(data).hexdigest()==expected,path
    finally:
        proc.stdin.close();proc.wait()
    writejson(ROOT/'results/m3_review/git_blob_checks.json',dict(status='PASS',evidence_commit=commit,verified_blob_count=len(manifest),method='Read actual committed Git blobs and compare SHA256 to pre-commit delivery_manifest; no newline normalization hidden.'))
    print('Committed Git blob verification PASS:',len(manifest),'files;',commit)
if __name__=='__main__':main()
