"""Repair path-only metadata using independently verified archived source hashes.

Native solver input and results are never edited. Old mojibake strings remain
in the audit so this is not a silent rewrite of provenance.
"""
import hashlib, json
from export_native_brake import RUN, ROOT

def main():
    records = []
    for folder in sorted((RUN/'studies').iterdir()):
        path = folder/'study_settings.json'
        if not path.exists():
            continue
        m = json.loads(path.read_text(encoding='utf-8-sig'))
        old = m.get('archived_forcing')
        if old:
            candidate = ROOT/'results/m2/cases'/old.replace('\\', '/').split('/')[-1]
            assert candidate.is_file(), candidate
            actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
            assert actual == m['forcing_sha256'], (folder.name, actual)
            if old != str(candidate):
                m.setdefault('metadata_encoding_repairs', []).append(dict(
                    field='archived_forcing', previous=old, verified_file=str(candidate),
                    verified_sha256=actual,
                    reason='Windows PowerShell UTF-8 JSON read as ANSI; source bytes verified unchanged.'))
                m['archived_forcing'] = str(candidate)
                records.append(dict(study=folder.name, field='archived_forcing',
                                    original_preserved=True, source_sha256=actual))
        # ASCII JSON is compatible with Windows PowerShell 5.1's legacy default
        # reader in already-running queues. New runners explicitly read UTF-8.
        path.write_text(json.dumps(m, indent=2)+'\n', encoding='utf-8')
        dest = ROOT/'results/m4/studies'/folder.name/'study_settings.json'
        if dest.exists():
            dest.write_text(json.dumps(m, indent=2)+'\n', encoding='utf-8')
    out=ROOT/'results/m4/metadata_encoding_checks.json'
    out.write_text(json.dumps(dict(status='PASS_SOURCE_BYTES_VERIFIED', repairs=records,
        scope='Metadata only. Native study.dat, RTH, powers and source files unchanged.'), indent=2)+'\n', encoding='utf-8')
    print('Verified metadata paths repaired:', len(records))

if __name__=='__main__':main()
