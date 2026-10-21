"""Actual STEP tessellation/sections plus labelled S3 engineering audit plots."""
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cadquery as cq
from review_cad import ROOT,box
OUT=ROOT/'results/m3_review';CAD=ROOT/'cad/m3_review'
COL={'steel':'#66849a','aluminium':'#a1bbcc','copper':'#d18b47','cast_iron':'#5b6068','pad':'#3b3e44','seal_equivalent':'#ad7070','stainless':'#cba752','oil':'#dfb868','water_equivalent':'#91ccd0'}
def save(fig,name):fig.savefig(OUT/(name+'.png'),dpi=165);plt.close(fig)
def mesh(s):
    vertices,tris=s.tessellate(1.5,.2)
    return np.array([v.toTuple() for v in vertices])[np.array(tris)]
def section(ax,parts,y,colors=None):
    slab=box(-250,335,y-.15,y+.15,-180,285)
    for n,s in parts.items():
        bb=s.BoundingBox()
        if bb.ymin>y+.15 or bb.ymax<y-.15:continue
        sh=s.intersect(slab)
        if sh.Volume()<1e-5:continue
        triangles=mesh(sh)[:,:,[0,2]]
        ax.add_collection(PolyCollection(triangles,facecolors=(colors or {}).get(n,'#8d9da8'),edgecolors='none',alpha=.8,rasterized=True))
    ax.set(xlim=(-235,330),ylim=(-170,280),xlabel='x (mm)',ylabel='z (mm)',aspect='equal')

def contact_graph():
    fig,ax=plt.subplots(figsize=(12,5.5),layout='constrained');ax.axis('off')
    nodes={'Disc':(.045,.7),'Hub':(.20,.7),'Removable\nsleeve':(.36,.7),'Output\nshaft':(.53,.7),'Rear\nbearing':(.71,.7),'Case / oil':(.91,.7),'Pads / caliper':(.12,.25),'Bracket':(.43,.25),'Adapter':(.72,.25),'Motor case':(.91,.25)}
    for label,(x,y) in nodes.items():ax.text(x,y,label,ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#edf1f3',ec='#7293a6'),transform=ax.transAxes,fontsize=11)
    pairs=[('Disc','Hub'),('Hub','Removable\nsleeve'),('Removable\nsleeve','Output\nshaft'),('Output\nshaft','Rear\nbearing'),('Rear\nbearing','Case / oil'),('Disc','Pads / caliper'),('Pads / caliper','Bracket'),('Bracket','Case / oil'),('Case / oil','Adapter'),('Adapter','Motor case')]
    for a,b in pairs:ax.annotate('',xy=nodes[b],xytext=nodes[a],xycoords='axes fraction',arrowprops=dict(arrowstyle='<->',color='#ac6651',shrinkA=35,shrinkB=40))
    ax.text(.5,.03,'Bulk R candidates only; red interfaces require contact / film laws.\nSleeve pressure / thermal retention unknown. Bolts, seals and keys add parallel paths.',ha='center',transform=ax.transAxes,fontsize=11)
    ax.set_title('Revised thermal path / node graph | S3 engineering hypothesis, not solved network');save(fig,'contact_network')

def main():
    print('LOAD REVISED PART STEP',flush=True)
    mass=list(csv.DictReader((OUT/'mass_heat_capacity.csv').open(encoding='utf-8')))
    rows=[r for r in mass if r['case']=='Case0' and r['diameter_mm']=='50' and r['variant']=='full'];materials={r['part']:r['material'] for r in rows}
    parts={f.stem:cq.importers.importStep(str(f)).val() for f in (CAD/'revised_parts').glob('*.step')}
    colors={n:COL[materials[n]] for n in parts}
    fig=plt.figure(figsize=(12,8),layout='constrained');ax=fig.add_subplot(111,projection='3d')
    for n,s in parts.items():
        if 'bolt' in n or materials[n] in ['oil','water_equivalent']:continue
        alpha=.07 if n in ['motor_case','gear_case_front','gear_case_rear','motor_gear_adapter'] else .95
        ax.add_collection3d(Poly3DCollection(mesh(s),facecolor=colors[n],edgecolor='none',alpha=alpha,rasterized=True))
    ax.set(xlim=(-230,335),ylim=(-210,330),zlim=(-160,285),xlabel='Axial x (mm)',ylabel='y (mm)',zlabel='z (mm)');ax.set_box_aspect((565,540,445));ax.view_init(20,-55)
    ax.set_title('Revised50mm assembly | actual STEP tessellation | S3, not released')
    for n in ['motor_input_coupling','output_halfshaft_flange','disc_hub','intermediate_shaft']:
        c=parts[n].Center();ax.text(c.x,c.y,c.z+20,n.replace('_',' '),fontsize=7)
    save(fig,'assembly_cutaway')
    fig,axes=plt.subplots(3,1,figsize=(12,13),layout='constrained')
    for ax,y,title in zip(axes,[120,0,-120],['Input / intermediate shaft plane','Output shaft / disc plane','Caliper / pad / bracket plane']):
        section(ax,parts,y,colors);ax.set_title(title+f' | actual 0.3mm CAD slice at y={y}mm',fontsize=10)
    fig.suptitle('Mechanical sections: S3 dimensions, no stress or displacement solution');save(fig,'shaft_sections')
    print('THERMAL COMPARISON',flush=True)
    thermal=cq.importers.importStep(str(CAD/'Case0_d50_thermal.step')).val();solids=thermal.Solids()
    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    sh=parts['stage2_gear'];target=sh.Center()
    eq=min(solids,key=lambda s:(s.Center()-target).Length)
    for ax,s,title in zip(axes,[sh,eq],['Full concept: involute teeth and keyed bore','Thermal: equal-volume smooth region + swept clearance']):
        triangles=mesh(s)[:,:,[1,2]];ax.add_collection(PolyCollection(triangles,facecolor='#6d8a9b',edgecolor='none',alpha=.75))
        ax.set(xlim=(-100,100),ylim=(-100,100),aspect='equal',xlabel='y (mm)',ylabel='z (mm)',title=title)
    fig.suptitle('S3 thermal geometry | gear-mesh heat conductance remains unknown');save(fig,'cad_simplification')
    comp=list(csv.DictReader((OUT/'M2_capacity_comparison.csv').open(encoding='utf-8')));valid=[r for r in comp if r['M3_geometry_candidate_C_J_K']]
    fig,ax=plt.subplots(figsize=(11,4.8),layout='constrained');x=np.arange(len(valid))
    ax.bar(x-.18,[float(r['M2_C_J_K']) for r in valid],.36,label='M2 assumed lump');ax.bar(x+.18,[float(r['M3_geometry_candidate_C_J_K']) for r in valid],.36,label='M3 CAD volume x S3 rho cp')
    ax.set_xticks(x,[r['node'] for r in valid],rotation=25,ha='right');ax.set(ylabel='Heat capacity (J/K)',title='Engineering candidates; pinions retained on separate shaft nodes');ax.legend();save(fig,'capacity_comparison')
    contact_graph()
    fig,axes=plt.subplots(2,2,figsize=(11,9),layout='constrained')
    for case,ax in zip(['Case0','CaseA','CaseB','CaseC'],axes.flat):
        print('SECTION',case,flush=True)
        sh=cq.importers.importStep(str(CAD/f'{case}_d50_full.step')).val().intersect(box(150,280,-.15,.15,-160,250))
        triangles=mesh(sh)[:,:,[0,2]];ax.add_collection(PolyCollection(triangles,facecolor='#8b9fab',edgecolor='none',alpha=.8))
        ax.set(xlim=(150,280),ylim=(-160,250),aspect='equal',xlabel='x (mm)',ylabel='z (mm)',title=case+' actual STEP section y=0')
        if case=='CaseC':ax.annotate('open outlet\nflow direction unknown',xy=(241.5,215),xytext=(255,175),fontsize=8,arrowprops=dict(arrowstyle='->'))
    fig.suptitle('Same base assembly; geometric openings do not prove ventilation / cooling');save(fig,'cases_space')
    shaft=list(csv.DictReader((OUT/'shaft_screening.csv').open(encoding='utf-8')));fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for case in ['drive','brake_0.6g','brake_0.8g']:
        a=[x for x in shaft if x['shaft']=='output' and x['load_case']==case and x['notch_factor']=='2.0'];axes[0].plot([float(x['diameter_mm']) for x in a],[float(x['peak_von_Mises_MPa']) for x in a],'o-',label=case)
    axes[0].axhline(180,ls='--',color='#b15b48',label='S3 limit180MPa');axes[0].set(xlabel='Output journal diameter (mm)',ylabel='Screen peak stress (MPa)',title='Local roots, Kt2.0; no fatigue certification');axes[0].legend(fontsize=8)
    rad=list(csv.DictReader((OUT/'radiation_geometry.csv').open(encoding='utf-8')));axes[1].bar([x['case'] for x in rad],[float(x['F_direct']) for x in rad],yerr=[2*float(x['sampling_standard_error']) for x in rad],color='#be9b55')
    axes[1].set(ylabel='Direct view factor F',title='Revised B-rep rays, selected case end face only')
    fig.suptitle('Engineering / geometry predictions; no measured or solved temperatures');save(fig,'mechanical_sensitivity')
    print('Seven actual-CAD / engineering review figures saved.',flush=True)

if __name__=='__main__':main()
