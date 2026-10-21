"""Audit actual input bytes; preserve legacy normalized-text digests explicitly."""
import hashlib,json
from export_native_brake import RUN,ROOT
def main():
    rows=[]
    for folder in sorted((RUN/'studies').iterdir()):
        path=folder/'study.dat';meta=folder/'study_settings.json'
        if not path.exists() or not meta.exists():continue
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        m=json.loads(meta.read_text(encoding='utf-8-sig'));previous=m.get('actual_native_input_sha256')
        # Source/parent/normalized digests must never be called an exact-byte
        # self digest. Retain them as legacy history, not silently discard them.
        legacy={}
        for key in ['input_sha256','derived_input_sha256']:
            if key in m and m[key]!=actual:
                legacy[key]=m[key];m[key]=actual
        if legacy:
            m.setdefault('legacy_input_hash_records',[]).append(dict(values=legacy,
                reason='Earlier generator used normalized text or retained a pre-edit digest; corrected to immutable current native input bytes.'))
        m['actual_native_input_sha256']=actual
        m['input_hash_basis']='SHA256 of actual native study.dat bytes, including real line endings'
        meta.write_text(json.dumps(m,indent=2)+'\n')
        output=ROOT/'results/m4/studies'/folder.name/'study_settings.json'
        if output.exists():output.write_text(json.dumps(m,indent=2)+'\n')
        rows.append(dict(study=folder.name,sha256=actual,legacy_records_retained=bool(legacy),bytes=path.stat().st_size))
    out=ROOT/'results/m4/input_hash_audit.json'
    out.write_text(json.dumps(dict(status='PASS_ACTUAL_INPUT_BYTES_RECORDED',inputs=rows,
        note='No native input or solver result changed; old digests retained as historical metadata. Native archive manifests independently used actual-byte hashes.'),indent=2)+'\n')
    print('Actual-byte input hashes audited:',len(rows))
if __name__=='__main__':main()
