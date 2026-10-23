"""Audit actual exported fields and signed paths, without replacing FE validation."""
import csv,json
from pathlib import Path
import numpy as np
from summarize_studies import ROOT,OUT,STUDIES,load

def main():
    records=[]
    for proof in sorted(STUDIES.glob('*/native_archive_manifest.json')):
        folder=proof.parent;rows=load(folder.name)
        if rows is None:continue
        parts={r['part'] for r in rows};assert len(parts)==28
        times=sorted({float(r['time_s']) for r in rows});assert all(b>a for a,b in zip(times,times[1:]))
        for t in times:assert len([r for r in rows if float(r['time_s'])==t])==28
        for r in rows:
            v=np.array([float(r[k]) for k in ['minimum','maximum','capacity_weighted_mean','stored_energy_above_25C_J']])
            assert np.isfinite(v).all()
            assert v[0]-1e-8<=v[2]<=v[1]+1e-8
        minimum=min(rows,key=lambda r:float(r['minimum']))
        pathfile=folder/'signed_heat_paths.csv';pathchecked=False
        if pathfile.exists():
            paths=list(csv.DictReader(pathfile.open()));total={};previous=0
            for r in paths:
                dt=float(r['time_s'])-previous;assert dt>0;previous=float(r['time_s'])
                assert np.isclose(float(r['solid_cut_into_drive_W']),float(r['shaft_cut_into_drive_W'])+float(r['bracket_cut_into_drive_W']),atol=1e-10)
                for key in [k[:-2] for k in r if k.endswith('_W')]:
                    for kind in ['net','positive']:
                        dest=key+'_'+kind+'_J'
                        if dest not in r:continue
                        power=float(r[key+'_W']);value=power if kind=='net' else max(power,0)
                        total[dest]=total.get(dest,0)+dt*value
                        assert np.isclose(total[dest],float(r[dest]),rtol=1e-10,atol=1e-9)
                    if key+'_positive_J' in r:
                        assert float(r[key+'_positive_J'])>=max(0,float(r[key+'_net_J']))-1e-9
            pathchecked=True
        records.append(dict(study=folder.name,temperature_rows=len(rows),time_sets=len(times),
            field_checks='PASS_FINITE_COVERAGE_AND_WEIGHTED_MEAN_RANGE',signed_path_integral_checks='PASS' if pathchecked else 'NOT_IN_THIS_EXPORT',
            minimum_C=float(minimum['minimum']),minimum_part=minimum['part'],minimum_time_s=float(minimum['time_s']),
            undershoot_below_25C_K=max(0,25-float(minimum['minimum'])),
            undershoot_interpretation='Unclipped numerical diagnostic, not physical cooling or a discrete maximum-principle certificate.'))
    assert records
    result=dict(status='PASS_EXPORTED_RESULT_INVARIANTS_ONLY',studies=records,
        scope='Finite 28-region coverage; positive capacity mean within nodal range; signed/net/positive integration and no serial cut double count. Energy/convergence/physical calibration are separate.')
    (OUT/'result_invariant_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'],len(records),'actual completed studies')

if __name__=='__main__':main()
