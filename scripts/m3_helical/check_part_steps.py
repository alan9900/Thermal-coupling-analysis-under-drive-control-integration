"""Roundtrip the ten separately exported changed-part STEP files as well."""
import csv,hashlib,json
import cadquery as cq
from helical_cad import ROOT
from run_geometry import csvout
OUT=ROOT/'results/m3_helical'
def main():
    rows=[];manifest=json.loads((OUT/'step_manifest.json').read_text())
    for f in sorted((ROOT/'cad/m3_helical/parts').glob('*.step')):
        a=cq.Shape.importBrep(str(ROOT/'tmp/m3_helical'/f.with_suffix('.brep').name))
        b=cq.importers.importStep(str(f)).val();error=abs(b.Volume()-a.Volume())/a.Volume()
        assert b.isValid() and len(b.Solids())==len(a.Solids()) and error<1e-7
        expected=next(r for r in manifest['files'] if r['path']==f.relative_to(ROOT).as_posix())
        assert hashlib.sha256(f.read_bytes()).hexdigest()==expected['sha256']
        rows.append(dict(part=f.stem,valid=True,solid_count=len(b.Solids()),roundtrip_volume_relative_error=error,status='PASS'))
    assert len(rows)==10;csvout(OUT/'part_step_checks.csv',rows)
    print('PASS 10 individual STEP roundtrips; max relative volume error',max(r['roundtrip_volume_relative_error'] for r in rows))
if __name__=='__main__':main()
