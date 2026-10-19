"""Readable paired endpoint temperature sensitivities from saved MATLAB output."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m2'

def main():
    with (OUT/'sensitivity_summary.csv').open() as f:rows=list(csv.DictReader(f))
    with (OUT/'case_summary.csv').open() as f:nom=next(r for r in csv.DictReader(f) if r['case_id']=='C_combined')
    names=list(dict.fromkeys(r['parameter'] for r in rows if r['parameter']!='coherent_M1_allocation'))
    labels=['Heat capacity','Contact R','Convection','Coolant conductance','Radiative exchange','Motor total loss','Gear total loss','Coolant temperature']
    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for ax,metric in zip(axes,['peak_gear_case_C','peak_winding_C']):
        delta=[]
        for name in names:
            pair=[r for r in rows if r['parameter']==name]
            delta.append([float(r[metric])-float(nom[metric]) for r in pair])
        delta=np.array(delta);y=np.arange(len(names))
        ax.barh(y-.17,delta[:,0],height=.3,label='Lower endpoint',color='#397fa9')
        ax.barh(y+.17,delta[:,1],height=.3,label='Upper endpoint',color='#d78938')
        ax.set_yticks(y,labels);ax.invert_yaxis();ax.axvline(0,color='#555',lw=.8);ax.grid(axis='x',alpha=.2)
        ax.set_xlabel('Peak temperature change relative to C (K)')
        ax.set_title('S3 CONCEPT: '+metric.replace('_',' '),fontsize=11)
    axes[0].legend(fontsize=8,loc='lower left')
    fig.savefig(OUT/'parameter_sensitivity.png',dpi=180);fig.savefig(OUT/'parameter_sensitivity.svg');plt.close(fig)

if __name__=='__main__':main()
