"""Focused STEP cold-clearance audit after the user's visual concern.

Full360 swept cylinder bounds all possible tooth phases; no geometry is edited.
"""
import csv,hashlib,json,math,sys
from pathlib import Path
import cadquery as cq
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/m3_review/output_gear_clearance';CAD=ROOT/'cad/m3_review/revised_parts'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    shapes={n:cq.importers.importStep(str(CAD/(n+'.step'))).val() for n in ['stage2_gear','gear_case_front','gear_case_rear']}
    gear=shapes['stage2_gear'];sweep=cq.Solid.makeCylinder(93,32,cq.Vector(95,0,0),cq.Vector(1,0,0))
    rows=[]
    for n in ['gear_case_front','gear_case_rear']:
        shell=shapes[n]
        for label,sh in [('as_exported',gear),('full360_swept_envelope',sweep)]:
            v=sh.intersect(shell).Volume();distance=sh.distance(shell)
            rows.append(dict(case='Case0_d50_full_common_base_all_cases',gear=label,housing=n,overlap_mm3=v,min_distance_mm=distance,status='PASS_COLD_CLEARANCE' if v<.001 and distance>0 else 'BLOCKED'))
            assert v<.001 and distance>0,(n,label,v,distance)
    phase=[]
    #60teeth: one6-degree period covers all orientations relative to housing.
    for angle in np.linspace(0,6,13):
        g=gear.rotate((0,0,0),(1,0,0),float(angle))
        for n in ['gear_case_front','gear_case_rear']:
            v=g.intersect(shapes[n]).Volume();distance=g.distance(shapes[n])
            phase.append(dict(angle_deg=float(angle),housing=n,overlap_mm3=v,min_distance_mm=distance));assert v<.001
    for name,data in [('checks.csv',rows),('phase_checks.csv',phase)]:
        with (OUT/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    result=dict(status='PASS_COLD_GEOMETRY_ONLY',model='Case0_d50_full',CAD_edited=False,checks=rows,phase_pairs=len(phase),
        swept_radius_mm=93,gear_pitch_diameter_mm=180,gear_axial_limits_mm=[95,127],housing_inner_bottom_mm=-104,housing_outer_bottom_mm=-110,
        minimum_swept_radial_bottom_clearance_mm=11,rear_bearing_boss_front_x_mm=137,minimum_axial_boss_gap_mm=10,
        source_files={n:hashlib.sha256((CAD/(n+'.step')).read_bytes()).hexdigest() for n in shapes},
        limitation='Nominal cold geometry only; tolerances, deflection, bearing play, thermal differential and oil churning not certified. No ANSYS/Fluent solve.')
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    plt.rcParams['font.sans-serif']=['Microsoft YaHei','DejaVu Sans'];plt.rcParams['axes.unicode_minus']=False
    fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained')
    def draw(ax,s,projection,color):
        if s.Volume()<1e-8:return
        vs,ts=s.tessellate(.3,.15);v=np.array([a.toTuple() for a in vs]);tri=v[np.array(ts)][:,:,projection]
        ax.add_collection(PolyCollection(tri,facecolor=color,edgecolor='none',alpha=.85))
    def block(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
    slab=block(110.9,111.1,-200,350,-200,300)
    for n,color in [('gear_case_rear','#d2a35e'),('stage2_gear','#527c9a')]:draw(axes[0],shapes[n].intersect(slab),[1,2],color)
    ax=axes[0];ax.set(xlim=(-125,115),ylim=(-120,110),aspect='equal',xlabel='y / mm',ylabel='z / mm',title='实际CAD横截面 x=111 mm')
    ax.add_patch(plt.Circle((0,0),93,fill=False,ls='--',color='#40556b',lw=.8))
    ax.annotate('全旋转包络：半径93 mm',xy=(-65,66),xytext=(-115,102),fontsize=9,arrowprops=dict(arrowstyle='->'))
    ax.annotate('',xy=(0,-93),xytext=(0,-104),arrowprops=dict(arrowstyle='<->',color='#b64036'))
    ax.annotate('齿顶扫掠包络至内底壁：11 mm',xy=(0,-98.5),xytext=(-105,-65),fontsize=9,color='#a43a33',arrowprops=dict(arrowstyle='->'))
    slab=block(70,165,-.1,.1,-120,110)
    for n,color in [('gear_case_rear','#d2a35e'),('stage2_gear','#527c9a')]:draw(axes[1],shapes[n].intersect(slab),[0,2],color)
    ax=axes[1];ax.set(xlim=(75,165),ylim=(-115,105),aspect='equal',xlabel='x / mm',ylabel='z / mm',title='实际CAD轴向截面 y=0 mm')
    ax.annotate('',xy=(127,50),xytext=(137,50),arrowprops=dict(arrowstyle='<->',color='#b64036'))
    ax.annotate('大齿轮端面至轴承座凸台：10 mm',xy=(132,50),xytext=(77,100),fontsize=8,color='#a43a33',arrowprops=dict(arrowstyle='->'))
    ax.text(97,-25,'齿轮\nx=95–127',fontsize=8);ax.text(146,-80,'后端壁',fontsize=8,rotation=90)
    fig.suptitle('输出大齿轮—壳体复核：蓝=齿轮，黄=壳体；名义冷态CAD，无实体交叠',fontsize=13)
    fig.savefig(OUT/'dimensioned_sections.png',dpi=170);plt.close(fig)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
