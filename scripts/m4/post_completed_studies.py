"""Archive and postprocess ONLY terminal, error-free native calculations.

Each result gets fresh capacity weights: Mechanical contact regeneration can
renumber nodes even when the solid mesh looks unchanged. Never read a live RTH.
"""
import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path('E:/ansys_runs/m4_case0_20261021/studies')

def process(name):
    assert re.fullmatch('[A-Za-z0-9_]+', name)
    folder = RUN / name
    log = (folder / 'study.out').read_text(encoding='utf-8-sig', errors='replace')
    if 'RUN COMPLETED' not in log or not re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0', log):
        raise RuntimeError('Incomplete or failed native calculation: ' + name)
    out = ROOT / 'results/m4/studies' / name
    out.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((folder / 'study_settings.json').read_text(encoding='utf-8-sig'))
    metadata['capacity_weights'] = str(out / 'FE_capacity_weights.npz')
    metadata['execution_status'] = 'NATIVE_RUN_COMPLETED_ZERO_ERRORS'
    if metadata.get('status') == 'GENERATED_NOT_EXECUTED':
        metadata['generation_status'] = metadata['status']
        metadata['status'] = 'ACTUAL_NATIVE_COMPLETED_NOT_MECHANICAL_TREE_SOLVED'
    with (folder/'study.dat').open('rb') as stream:
        metadata['actual_native_input_sha256'] = hashlib.file_digest(stream,'sha256').hexdigest()
    # Do not relabel an external solve as a Mechanical tree Solve state.
    (folder / 'study_settings.json').write_text(json.dumps(metadata, indent=2) + '\n')
    for file in ['study_settings.json', 'source_intervals.csv', 'study.out', 'study.mntr']:
        if (folder / file).is_file():
            shutil.copy2(folder / file, out / file)
    for script, args in [
        ('prepare_fe_capacity.py', [str(folder / 'study.rth'), '--out', str(out)]),
        ('postprocess_pilot.py', ['--study', str(folder)]),
        ('energy_pilot.py', ['--study', str(folder)]),
        ('plot_pilot.py', ['--study', name]),
    ]:
        with (out / (script + '.log')).open('w', encoding='utf-8') as stream:
            interpreter = str(ROOT / 'tmp/m3_cad/Scripts/python.exe') if script == 'plot_pilot.py' else sys.executable
            subprocess.run([interpreter, str(ROOT / 'scripts/m4' / script), *args],
                           cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
        print(name, script, 'completed', flush=True)
    manifest = {}
    for file in ['study.dat', 'study.rth', 'study.out']:
        path = folder / file
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        manifest[file] = dict(local_path=str(path), bytes=path.stat().st_size, sha256=digest)
    (out / 'native_archive_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cases', nargs='+')
    for case in parser.parse_args().cases:
        process(case)
