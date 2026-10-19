"""Freeze M2-only inputs and verify the accepted M1 sources; never rewrite M0/M1."""
import hashlib,json,subprocess
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]

def sha(path): return hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()

def main():
    cfg=yaml.safe_load((ROOT/'configs/m2_thermal_network.yaml').read_text(encoding='utf-8'))
    tag=subprocess.check_output(['git','rev-parse','M1-v1.0^{}'],cwd=ROOT,text=True).strip()
    assert tag==cfg['metadata']['baseline_commit']=='9d545ab39a3efcce857573af74f7e325b74a2b15'
    assert all(v is None for v in cfg['unknown_actual'].values())
    old=json.loads((ROOT/'results/m1/engineering/independent_checks.json').read_text())
    for name,s in old['interface_and_parent_sha256'].items(): assert sha(ROOT/name)==s,name
    # Protect every accepted source/code/result, allowing only new-stage version-registry edits.
    protected=['configs/baseline_vehicle.yaml','configs/m1_heat_sources.yaml','configs/m1_source_partition.yaml','data/raw/m0','data/raw/m1','results/m0','results/m1','scripts/m0','scripts/m1']
    assert not subprocess.check_output(['git','diff','M1-v1.0','--name-only','--',*protected],cwd=ROOT,text=True).strip()
    files=['configs/m2_thermal_network.yaml','results/m1/inputs.json','data/raw/m2/manifest.json']
    files += [str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'scripts/m1').glob('*.m'))]
    files += ['results/m1/engineering/interface/short_drive_0_to_80_left.csv','results/m1/engineering/interface/short_drive_0_to_80_left.json']
    payload=dict(configuration=cfg,provenance=dict(baseline_tag='M1-v1.0',baseline_commit=tag,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        input_sha256={name:sha(ROOT/name) for name in files},hash_definition='UTF-8 text normalized LF',
        M0_tag_target=subprocess.check_output(['git','rev-parse','M0-v1.0^{}'],cwd=ROOT,text=True).strip(),
        classification='S3_CONCEPT_PREDICTION_NOT_CALIBRATED'))
    out=ROOT/'results/m2';out.mkdir(parents=True,exist_ok=True)
    (out/'inputs.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('M2 inputs frozen; immutable M1/M0 references verified.')

if __name__=='__main__': main()
