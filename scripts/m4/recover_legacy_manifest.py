"""Add a missing archive index without rerunning or relabelling legacy results."""
import hashlib,json,re
from export_native_brake import RUN,ROOT

def main():
    name='B_face_scoped_full';folder=RUN/'studies'/name;out=ROOT/'results/m4/studies'/name
    proof=json.loads((out/'pilot_postprocessing.json').read_text(encoding='utf-8-sig'))
    meta=json.loads((out/'study_settings.json').read_text(encoding='utf-8-sig'))
    log=(folder/'study.out').read_text(encoding='utf-8-sig',errors='replace')
    assert 'RUN COMPLETED' in log and re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0',log)
    assert proof['time_points']==meta['expected_sets'] and abs(proof['last_time_s']-meta['duration_s'])<1e-7
    records={}
    for file in ['study.dat','study.rth','study.out']:
        path=folder/file
        with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        if file=='study.rth':assert h==proof['sha256'] and path.stat().st_size==proof['result_bytes']
        if file=='study.dat':
            original=json.loads((ROOT/'results/m4/model_input/input_manifest.json').read_text(encoding='utf-8-sig'))
            assert h==original['sha256_uncompressed']
        records[file]=dict(local_path=str(path),bytes=path.stat().st_size,sha256=h)
    (out/'native_archive_manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    (out/'legacy_index_recovery.json').write_text(json.dumps(dict(
        status='PASS_EXISTING_RESULTS_HASH_RECHECKED',new_solve=False,old_temperature_CSV_changed=False,
        qualification='Adds missing index only; prior coarse mesh/pad and subvolume BLOCKED limits remain.'),indent=2)+'\n',encoding='utf-8')
    print('Legacy archive index recovered, original data unchanged')

if __name__=='__main__':main()
