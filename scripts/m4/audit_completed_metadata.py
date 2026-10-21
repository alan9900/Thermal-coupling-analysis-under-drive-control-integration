"""Align generation/execution labels only when terminal native evidence exists."""
import json,re
from export_native_brake import RUN,ROOT

def main():
    rows=[]
    for proof in sorted((ROOT/'results/m4/studies').glob('*/native_archive_manifest.json')):
        out=proof.parent;folder=RUN/'studies'/out.name
        path=folder/'study_settings.json'
        if not path.exists():continue
        log=folder/'study.out'
        with log.open('rb') as f:
            f.seek(max(0,log.stat().st_size-16000));tail=f.read().decode('ascii',errors='replace')
        assert 'RUN COMPLETED' in tail and re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0',tail)
        m=json.loads(path.read_text(encoding='utf-8-sig'))
        if m.get('status')=='GENERATED_NOT_EXECUTED':
            m['generation_status']=m['status']
            m['status']='ACTUAL_NATIVE_COMPLETED_NOT_MECHANICAL_TREE_SOLVED'
        m['execution_status']='NATIVE_RUN_COMPLETED_ZERO_ERRORS'
        for p in [path,out/'study_settings.json']:
            p.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
        rows.append(dict(study=out.name,native_complete=True,Mechanical_state=m.get('Mechanical_state','EXTERNAL_NATIVE_NOT_MECHANICAL_TREE_SOLVED')))
    (ROOT/'results/m4/completed_metadata_checks.json').write_text(json.dumps(dict(
        status='PASS_NATIVE_EXECUTION_LABELS',studies=rows,
        scope='Preserve generation status separately; no change to native inputs, results or numerical acceptance.'),indent=2)+'\n',encoding='utf-8')
    print('Terminal metadata audited:',len(rows))

if __name__=='__main__':main()
