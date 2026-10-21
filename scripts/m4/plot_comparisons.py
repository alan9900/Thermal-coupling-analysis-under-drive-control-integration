"""Actual scenario/sensitivity/path plots; never synthesize missing studies."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from summarize_studies import ROOT,OUT,STUDIES,load,series,write_csv

PARTS=[('M4_BRAKE_DISC_HAT','Disc'),('M4_OUTPUT_BEARING_2','Output bearing rear'),
       ('M4_GEAR_CASE_REAR','Gear case rear'),('M4_OIL_INVENTORY','Oil'),
       ('M4_MOTOR_WINDING','Winding'),('M4_PAD_NEAR','Near pad')]
def choose(*names):return next((n for n in names if load(n)),None)

def scenarios():
    # Keep source-mask comparison on the same original solid mesh.
    choices={'A':choose('A_internal_only_dt1'),'B':choose('B_face_scoped_full'),
      'C':choose('C_combined_dt1_retry1'),'D':choose('D_preheat_braking_dt1')}
    rows=[];fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for ax,(part,label) in zip(axes.flat,PARTS):
        if part=='M4_PAD_NEAR':
            ax.axis('off');ax.text(.08,.65,'Pad peak excluded from this comparison',transform=ax.transAxes,fontsize=11)
            ax.text(.08,.35,'All curves here use the same original mesh.\nIts one-layer pad peak was rejected.\nRefined pad results are reported separately.',transform=ax.transAxes,fontsize=10)
            continue
        for case,name in choices.items():
            if not name:continue
            data=load(name);t,T=series(data,part,'maximum')
            meta=json.loads((STUDIES/name/'study_settings.json').read_text())
            offset=0.
            source=STUDIES/name/'source_intervals.csv'
            if source.exists():
                s=list(csv.DictReader(source.open()))
                heats=[r for r in s if float(r['disc'])>0]
                if heats:offset=float(heats[0]['time_s'])-float(heats[0]['dt_s'])
                elif case=='A':offset=15.101748027406
            ax.plot(t-offset,T,label=case+': '+name.replace('_dt1','').replace('_retry1',''),lw=1.2)
            peak=int(np.argmax(T))
            rows.append(dict(scenario=case,study=name,part=part,peak_C=float(T[peak]),
               peak_time_from_brake_s=float(t[peak]-offset),classification='ACTUAL_ANSYS_S3_CONCEPT; mesh/time qualification separate'))
        ax.set(title=label,xlabel='Time relative to first brake onset [s]',ylabel='Local maximum [degC]')
        ax.grid(alpha=.2);ax.axvline(0,color='.4',ls=':',lw=.8)
    handles,labels=axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',fontsize=7,ncols=2)
    fig.suptitle('Actual ANSYS | S3 engineering assumptions | SAME original diagnostic mesh\nA internal only, B friction only, C combined, D preheat + brake; aligned at brake onset; not converged pad predictions',fontsize=10)
    fig.savefig(OUT/'source_scenario_comparison.png');plt.close(fig);write_csv(OUT/'source_scenario_peak_summary.csv',rows)

def sensitivities():
    names=['C_normal12_rd95_dt1',*['C_normal12_rd95_'+x for x in ['contact_low','contact_high','cooling_low','cooling_high']]]
    available=[n for n in names if load(n)]
    receipt={'status':'ACTUAL_SERIES_COMPLETE' if len(available)==len(names) else 'PENDING',
      'required':names,'available':available,'classification':'S3 single-factor scenarios; not measured confidence intervals'}
    (OUT/'sensitivity_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if len(available)<len(names):return
    fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained');rows=[]
    baseline=load(names[0])
    for ax,(part,label) in zip(axes.flat,PARTS):
        ref=max(float(r['maximum']) for r in baseline if r['part']==part)
        for name in names:
            data=load(name);t,T=series(data,part,'maximum')
            short='baseline' if name==names[0] else name.replace('C_normal12_rd95_','')
            ax.plot(t,T,label=short,lw=1.1)
            rows.append(dict(study=name,part=part,peak_C=float(T.max()),delta_from_baseline_K=float(T.max()-ref),
              classification='Actual ANSYS S3; mounting TCC 100/10000; cooling (5,100)/(40,800); not statistical bounds'))
        ax.set(title=label,xlabel='Controlled-cycle time [s]',ylabel='Local maximum [degC]');ax.grid(alpha=.2)
    h,l=axes.flat[0].get_legend_handles_labels();fig.legend(h,l,loc='outside lower center',ncols=5,fontsize=8)
    fig.suptitle('Actual ANSYS parameter sensitivity | S3 assumptions | identical sources and mesh\nMounting contacts varied; motor internal gap links / oil film remain separate unresolved parameters',fontsize=10)
    fig.savefig(OUT/'contact_cooling_sensitivity.png');plt.close(fig);write_csv(OUT/'sensitivity_temperature_summary.csv',rows)

def paths():
    for folder in STUDIES.iterdir():
        p=folder/'signed_heat_paths.csv'
        if not p.exists():continue
        rows=list(csv.DictReader(p.open()));check=json.loads((folder/'heat_path_checks.json').read_text())
        t=np.r_[0,[float(r['time_s']) for r in rows]]
        fig,axes=plt.subplots(1,3,figsize=(13,3.8),layout='constrained')
        for key,label in [('solid_cut_into_drive','Solid brake/drive cut'),('radiation_net_into_case','Case net radiation'),('ambient_drive_out','Drive ambient out'),('coolant_out','Coolant out')]:
            axes[0].plot(t,np.r_[0,[float(r[key+'_W']) for r in rows]],label=label)
            for axis,kind in zip(axes[1:],['net','positive']):
                axis.plot(t,np.r_[0,[float(r[key+'_'+kind+'_J']) for r in rows]],label=label)
        for ax,title,unit in zip(axes,['Signed instantaneous rate','Signed net integral','Positive-only integral'],['W','J','J']):
            ax.set(title=title,xlabel='Study time [s]',ylabel=unit);ax.grid(alpha=.2);ax.legend(fontsize=6)
        fig.suptitle('Actual ANSYS S3 | '+folder.name+' | '+check['status']+'\nNet radiation includes open environment; hot-air ingress NOT MODELLED; serial bearing sections are not added',fontsize=9)
        fig.savefig(folder/'signed_heat_paths.png');plt.close(fig)

if __name__=='__main__':
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'figure.dpi':150})
    scenarios();sensitivities();paths()
