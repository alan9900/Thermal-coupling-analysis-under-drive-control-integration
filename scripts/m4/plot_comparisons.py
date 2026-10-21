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
    plt.rcParams.update({'font.size':14})
    # Keep source-mask comparison on the same original solid mesh.
    choices={'A':choose('A_internal_only_dt1'),'B':choose('B_face_scoped_full'),
      'C':choose('C_combined_dt1_retry1'),'D':choose('D_preheat_braking_dt1')}
    rows=[];fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for ax,(part,label) in zip(axes.flat,PARTS):
        if part=='M4_PAD_NEAR':
            ax.axis('off');ax.text(.05,.7,'Pad peak excluded',transform=ax.transAxes,fontsize=16)
            ax.text(.05,.3,'Same original mesh for all curves.\nOne-layer pad peak rejected.\nRefined pad reported separately.',transform=ax.transAxes,fontsize=14)
            continue
        for case,name in choices.items():
            if not name:continue
            data=load(name);t,T=series(data,part,'maximum')
            meta=json.loads((STUDIES/name/'study_settings.json').read_text(encoding='utf-8-sig'))
            offset=0.
            source=STUDIES/name/'source_intervals.csv'
            if source.exists():
                s=list(csv.DictReader(source.open()))
                heats=[r for r in s if float(r['disc'])>0]
                if heats:offset=float(heats[0]['time_s'])-float(heats[0]['dt_s'])
                elif case=='A':offset=15.101748027406
            ax.plot(t-offset,T,label={'A':'A Internal losses','B':'B Friction','C':'C Combined','D':'D Preheat + brake'}[case],lw=1.2)
            peak=int(np.argmax(T))
            rows.append(dict(scenario=case,study=name,part=part,peak_C=float(T[peak]),
               peak_time_from_brake_s=float(t[peak]-offset),classification='ACTUAL_ANSYS_S3_CONCEPT; mesh/time qualification separate'))
        ax.set(title=label,xlabel='Brake-relative time [s]',ylabel='Maximum [degC]')
        ax.grid(alpha=.2);ax.axvline(0,color='.4',ls=':',lw=.8)
    handles,labels=axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',fontsize=15,ncols=2)
    fig.suptitle('Actual ANSYS | S3 assumptions | same original diagnostic mesh\nSource masks aligned at first brake onset; rejected pad peak excluded',fontsize=16)
    fig.savefig(OUT/'source_scenario_comparison.png');plt.close(fig);write_csv(OUT/'source_scenario_peak_summary.csv',rows)

def sensitivities():
    plt.rcParams.update({'font.size':14})
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
    h,l=axes.flat[0].get_legend_handles_labels();fig.legend(h,l,loc='outside lower center',ncols=3,fontsize=14)
    fig.suptitle('Actual ANSYS | S3 parameter sensitivity | identical sources / mesh\nMounting TCC / cooling varied; motor internal and oil-film links held fixed',fontsize=16)
    fig.savefig(OUT/'contact_cooling_sensitivity.png');plt.close(fig);write_csv(OUT/'sensitivity_temperature_summary.csv',rows)


def refined_scenarios():
    names={'A':'A_normal12_rd95_dt1','B':'B_normal12_rd95h_dt1',
           'C':'C_normal12_rd95_dt1','D':'D_normal12_rd95_dt1'}
    ready={k:load(n) for k,n in names.items()}
    if any(v is None for v in ready.values()):return
    meta={k:json.loads((STUDIES/n/'study_settings.json').read_text(encoding='utf-8-sig')) for k,n in names.items()}
    assert len({m['original_sha256'] for m in meta.values()})==1
    assert all(m['radiation_reduction']==.95 and m['case_radiation_reduction']==0 for m in meta.values())
    # A and C differ only by disc/pad heat. Verify this before interpreting C-A.
    sources={k:list(csv.DictReader((STUDIES/names[k]/'source_intervals.csv').open())) for k in ['A','C']}
    keys=['time_s','dt_s','copper','iron','rotor_other','gear_mesh','gear_bearing','gear_other','internal_applied_W']
    assert len(sources['A'])==len(sources['C'])
    for a,c in zip(sources['A'],sources['C']):
        assert all(np.isclose(float(a[k]),float(c[k]),rtol=1e-12,atol=1e-10) for k in keys)
        assert float(a['disc'])==float(a['pad'])==0
    plt.rcParams.update({'font.size':14})
    fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for ax,(part,label) in zip(axes.flat,PARTS):
        for case,name in names.items():
            t,T=series(ready[case],part,'maximum');offset=0
            source=STUDIES/name/'source_intervals.csv'
            if source.exists():
                s=list(csv.DictReader(source.open()));brake=[r for r in s if float(r['disc'])>0]
                offset=float(brake[0]['time_s'])-float(brake[0]['dt_s']) if brake else 15.101748027406
            ax.plot(t-offset,T,label={'A':'A Internal','B':'B Friction','C':'C Combined','D':'D Preheat'}[case])
        ax.set(title=label,xlabel='Time from brake onset [s]',ylabel='Local maximum [degC]');ax.grid(alpha=.2)
    h,l=axes.flat[0].get_legend_handles_labels();fig.legend(h,l,loc='outside lower center',ncols=4,fontsize=14)
    fig.suptitle('Actual ANSYS | S3 | common 12-layer solid mesh / disc-only RDEC 95%\nSource histories differ; not a measured temperature comparison',fontsize=16)
    fig.savefig(OUT/'refined_source_scenarios.png');plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained');rows=[]
    for ax,(part,label) in zip(axes.flat,PARTS):
        ta,ma=series(ready['A'],part,'capacity_weighted_mean');tc,mc=series(ready['C'],part,'capacity_weighted_mean')
        tx,xa=series(ready['A'],part,'maximum');ty,xc=series(ready['C'],part,'maximum')
        assert np.allclose(ta,tc) and np.allclose(tx,ty)
        mean=mc-ma;maxima=xc-xa
        ax.plot(tc,mean,label='Capacity-mean difference')
        ax.plot(tc,maxima,'--',label='Regional-max difference')
        ax.set(title=label,xlabel='Common cycle time [s]',ylabel='C minus A [K]');ax.grid(alpha=.2)
        rows.extend(dict(part=part,time_s=float(t),C_minus_A_mean_K=float(m),C_minus_A_regional_max_K=float(x),
            classification='Matched S3 source-mask comparison. Difference of regional maxima is not maximum pointwise field difference.') for t,m,x in zip(tc,mean,maxima))
    h,l=axes.flat[0].get_legend_handles_labels();fig.legend(h,l,loc='outside lower center',ncols=2,fontsize=13)
    fig.suptitle('Actual ANSYS | added friction response C minus A\nIdentical mesh, internal sources and boundaries; nonlinear radiation retained',fontsize=16)
    fig.savefig(OUT/'added_brake_response.png');plt.close(fig);write_csv(OUT/'added_brake_response.csv',rows)
    (OUT/'source_mask_comparison_checks.json').write_text(json.dumps(dict(status='PASS_MATCHED_SOURCE_MASK_INPUTS',
        studies=names,mesh_sha256=meta['A']['original_sha256'],
        interpretation='C-A compares identical clocks/internal powers. Regional maxima differences are not pointwise temperature differences. Small K signals do not establish physical accuracy.'),indent=2)+'\n',encoding='utf-8')

def paths():
    plt.rcParams.update({'font.size':14})
    for folder in STUDIES.iterdir():
        p=folder/'signed_heat_paths.csv'
        if not p.exists():continue
        rows=list(csv.DictReader(p.open()));check=json.loads((folder/'heat_path_checks.json').read_text(encoding='utf-8-sig'))
        t=np.r_[0,[float(r['time_s']) for r in rows]]
        fig,axes=plt.subplots(1,3,figsize=(13,4.5),layout='constrained')
        for key,label in [('solid_cut_into_drive','Solid cut'),('radiation_net_into_case','Case net rad.'),('ambient_drive_out','Air out'),('coolant_out','Coolant out')]:
            axes[0].plot(t,np.r_[0,[float(r[key+'_W']) for r in rows]],label=label)
            for axis,kind in zip(axes[1:],['net','positive']):
                axis.plot(t,np.r_[0,[float(r[key+'_'+kind+'_J']) for r in rows]],label=label)
        for ax,title,unit in zip(axes,['Signed instantaneous rate','Signed net integral','Positive-only integral'],['W','J','J']):
            ax.set(title=title,xlabel='Time [s]',ylabel=unit);ax.grid(alpha=.2);ax.legend(fontsize=12)
        state='PASS subvolume balance' if check['status'].startswith('PASS') else 'BLOCKED subvolume balance'
        fig.suptitle('Actual ANSYS S3 | '+folder.name+' | '+state+'\nNet radiation includes environment; hot air NOT MODELLED; serial sections not added',fontsize=16)
        fig.savefig(folder/'signed_heat_paths.png');plt.close(fig)

if __name__=='__main__':
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'figure.dpi':150})
    scenarios();refined_scenarios();sensitivities();paths()
