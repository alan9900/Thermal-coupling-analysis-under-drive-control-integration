"""Plot saved MATLAB OAT runs; all outputs are engineering predictions."""
from pathlib import Path
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/m1/engineering'


def main():
    with (OUT/'sensitivity_energies.csv').open(newline='',encoding='utf-8') as f: data=list(csv.DictReader(f))
    cases=list(dict.fromkeys(r['case_id'] for r in data)); rows=[]
    for case in cases:
        by={r['scenario']:r for r in data if r['case_id']==case}; nominal=by['nominal']
        params=[name.removesuffix('_endpoint1') for name in by if name.endswith('_endpoint1')]
        for name in params:
            row=dict(case_id=case,parameter=name)
            for source in ['copper','gear_mesh','disc']:
                base=float(nominal[source+'_kJ'])
                for endpoint in [1,3]:
                    row[f'{source}_delta_endpoint{endpoint}_kJ']=float(by[f'{name}_endpoint{endpoint}'][source+'_kJ'])-base
            rows.append(row)
    with (OUT/'oat_sensitivity.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
    for ax,(case,source) in zip(axes.flat,[(cases[0],'copper'),(cases[1],'copper'),(cases[0],'gear_mesh'),(cases[0],'disc')]):
        r=[r for r in rows if r['case_id']==case]
        r.sort(key=lambda r:max(abs(r[f'{source}_delta_endpoint1_kJ']),abs(r[f'{source}_delta_endpoint3_kJ'])),reverse=True)
        r=[x for x in r[:7] if max(abs(x[f'{source}_delta_endpoint1_kJ']),abs(x[f'{source}_delta_endpoint3_kJ']))>1e-10]
        y=np.arange(len(r))
        ax.barh(y-.16,[x[f'{source}_delta_endpoint1_kJ'] for x in r],height=.3,color='#307ab0',label='Parameter lower endpoint')
        ax.barh(y+.16,[x[f'{source}_delta_endpoint3_kJ'] for x in r],height=.3,color='#dd8a38',label='Parameter upper endpoint')
        ax.set_yticks(y,[x['parameter'].replace('_',' ') for x in r],fontsize=8); ax.invert_yaxis()
        ax.axvline(0,color='#555555',lw=.7); ax.grid(axis='x',alpha=.2)
        ax.set_xlabel('Change from nominal, single-side energy (kJ)')
        ax.set_title(f'S3 ENGINEERING OAT: {source}\n{case}',fontsize=10)
    axes[0,0].legend(fontsize=8,loc='lower right')
    fig.savefig(OUT/'oat_sensitivity.png',dpi=180)
    fig.savefig(OUT/'oat_sensitivity.svg'); plt.close(fig)
    print('OAT sensitivity: 16 parameters x 2 cases; PNG/SVG and deltas saved.')


if __name__=='__main__': main()
