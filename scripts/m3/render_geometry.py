"""Scientific CAD tessellation previews and dimension/path diagrams (no AI image)."""
import json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from cad_model import ROOT,config,build
OUT=ROOT/'results/m3'
COLORS={'steel':'#637d97','aluminium':'#9bb4c6','copper':'#d17c34','cast_iron':'#515965','stainless':'#d4ab40','pad':'#36323c'}

def preview(ax,m):
    for name,sh in m['parts'].items():
        if m['roles'][name]=='fluid' or 'bolt' in name:continue
        verts,tris=sh.tessellate(2,.2);v=np.array([a.toTuple() for a in verts]);t=np.array(tris)
        alpha=.08 if name in ['motor_case','gear_case'] else .92
        ax.add_collection3d(Poly3DCollection(v[t],facecolor=COLORS[m['materials'][name]],alpha=alpha,edgecolor='none',rasterized=True))
    ax.set(xlim=(-170,290),ylim=(-210,290),zlim=(-170,280),xlabel='Axial x (mm)',ylabel='y (mm)',zlabel='z (mm)')
    ax.view_init(elev=20,azim=-55);ax.set_box_aspect((460,500,450));ax.tick_params(labelsize=7);ax.set_title(m['case']+'  |  S3 concept, transparent casings',fontsize=10)

def main():
    p=config();models=[build(p,c) for c in ['Case0','CaseA','CaseB','CaseC']]
    fig=plt.figure(figsize=(14,11),layout='constrained')
    for i,m in enumerate(models):preview(fig.add_subplot(2,2,i+1,projection='3d'),m)
    fig.suptitle('CAD-EXECUTED geometry comparison | no temperature / strength validation',fontsize=15)
    fig.savefig(OUT/'structure_comparison.png',dpi=170);fig.savefig(OUT/'structure_comparison.pdf');plt.close(fig)
    fig=plt.figure(figsize=(11,8),layout='constrained');ax=fig.add_subplot(111,projection='3d');preview(ax,models[0])
    for name in ['output_shaft','brake_disc_hat','caliper','motor_stator','stage2_gear']:
        c=models[0]['parts'][name].Center();ax.text(c.x,c.y,c.z+15,name.replace('_',' '),fontsize=8)
    fig.savefig(OUT/'assembly_cutaway.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    ax=axes[0];m=models[0]
    for center,radius,label in [((120,100),25,'input, m2.5 z20'),((120,0),75,'stage1 gear z60'),((120,0),30,'stage2 pinion z20'),((0,0),90,'output gear z60')]:
        ax.add_patch(plt.Circle(center,radius,fill=False,lw=1.5));ax.plot(*center,'o');ax.annotate(label,center,xytext=(center[0]+10,center[1]+10),fontsize=8)
    ax.add_patch(plt.Circle((120,100),151,fill=False,color='#bc7a3f',ls='--'));ax.set(xlim=(-125,290),ylim=(-130,275),aspect='equal',xlabel='y (mm)',ylabel='z (mm)',title='End view: pitch circles; ratio 3 x 3 = 9')
    ax=axes[1]
    for x0,x1,r0,r1,label,col in [(-161,0,0,151,'Motor envelope','#9bb4c6'),(0,160,0,180,'Reducer envelope','#637d97'),(205,227,85,140,'Disc','#515965'),(185,205,34,88,'Disc hat','#777')]:
        ax.add_patch(plt.Rectangle((x0,r0),x1-x0,r1-r0,fc=col,alpha=.4));ax.text((x0+x1)/2,r1+4,label,ha='center',fontsize=8)
    ax.axvline(193.5,color='#c99f33',label='A/C shield');ax.axvspan(182,183.5,color='#c99f33',alpha=.5,label='B additional layer')
    ax.annotate('',xy=(160,75),xytext=(205,75),arrowprops=dict(arrowstyle='<->'));ax.text(182.5,78,'45mm disc-case gap',ha='center',fontsize=8)
    ax.set(xlim=(-180,270),ylim=(0,210),xlabel='Axial x (mm)',ylabel='Illustrative radial extent (mm)',title='Axial packaging, schematic radial alignment');ax.legend(fontsize=8)
    fig.suptitle('S3 selected dimensions; motor302 x 161 and disc280 x 22 reference envelopes retained')
    fig.savefig(OUT/'dimensions_layout.png',dpi=180);fig.savefig(OUT/'dimensions_layout.svg');plt.close(fig)
    rows=json.loads((OUT/'analysis_checks.json').read_text());import csv
    with (OUT/'radiation_geometry.csv').open() as f:data=list(csv.DictReader(f))
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    axes[0].bar([x['case'] for x in data],[float(x['case_direct']) for x in data],color=['#637d97','#d4ab40','#aa8a40','#527e82']);axes[0].set(ylabel='Direct geometric view factor (dimensionless)',title='Disc exposed rear face -> selected case end face')
    # Avoid pandas dependency: CSV reads suffice for compact screening plot.
    with (OUT/'shaft_screening.csv').open() as f:stress=list(csv.DictReader(f))
    for key in ['propulsion','braking']:
        rr=[x for x in stress if x['load_case']==key];axes[1].plot([float(x['diameter_mm']) for x in rr],[float(x['von_Mises_screen_MPa']) for x in rr],'o-',label=key)
    axes[1].axhline(180,ls='--',color='#b54c42',label='S3 screen limit');axes[1].set(xlabel='Output shaft diameter (mm)',ylabel='Static equivalent stress with S3 notch factor (MPa)',title='Elementary screen; fatigue/life not verified');axes[1].legend()
    fig.suptitle('S3 geometric/stress candidates: no cooling-performance claim')
    fig.savefig(OUT/'geometry_sensitivity.png',dpi=180);fig.savefig(OUT/'geometry_sensitivity.svg');plt.close(fig)
    print('CAD-derived previews and scientific layout figures saved.')

if __name__=='__main__':main()
