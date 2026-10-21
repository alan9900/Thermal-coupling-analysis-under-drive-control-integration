"""Fresh PCG study, preserving the SPARSE reference for actual comparison."""
import argparse,json,re,hashlib,shutil
from export_native_brake import RUN,ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('name');a=p.parse_args()
    base=RUN/'studies'/a.base;folder=RUN/'studies'/a.name;folder.mkdir(exist_ok=False)
    text=(base/'study.dat').read_text();assert not re.search(r'^eqslv',text,re.M|re.I)
    first=re.search(r'^solve\s*$',text,re.M|re.I);assert first
    text=text[:first.start()]+'! Independently verify PCG against preserved SPARSE reference\neqslv,pcg,1.e-10\n'+text[first.start():]
    (folder/'study.dat').write_text(text)
    for name in ['source_intervals.csv']:
        if (base/name).exists():shutil.copy2(base/name,folder/name)
    m=json.loads((base/'study_settings.json').read_text())
    m.update(equation_solver='PCG',iterative_linear_tolerance=1e-10,solver_reference=a.base,
      status='GENERATED_NOT_EXECUTED',capacity_weights=str(ROOT/'results/m4/studies'/a.name/'FE_capacity_weights.npz'),
      input_sha256=hashlib.sha256(text.encode()).hexdigest())
    (folder/'study_settings.json').write_text(json.dumps(m,indent=2)+'\n')
    print(folder)

if __name__=='__main__':main()
