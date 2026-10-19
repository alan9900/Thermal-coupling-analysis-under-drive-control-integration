"""Optional primary-source retrieval receipt; do this BEFORE prepare_inputs."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[2]

def main():
    path=ROOT/'data/raw/m2/manifest.json';manifest=json.loads(path.read_text())
    for record in manifest['sources']:
        record['retrieved_utc']=datetime.now(timezone.utc).isoformat()
        try:
            r=requests.get(record['url'],timeout=35);r.raise_for_status()
            record.update(status='HTTP_OK',bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
            record.pop('error_type',None)
        except requests.RequestException as exc:
            record.update(status='DOWNLOAD_FAILED',error_type=type(exc).__name__)
    path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print({r['id']:r['status'] for r in manifest['sources']})

if __name__=='__main__':main()
