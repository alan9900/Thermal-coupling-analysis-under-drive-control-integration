"""Figures from executed BREP tessellation, no AI-generated gear pictures."""
import sys
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb
from matplotlib.ticker import MaxNLocator
from helical_cad import ROOT, old
sys.path.insert(0,str(ROOT/'scripts/m3_review'))
from plot_review import COL
OUT=ROOT/'results/m3_helical';CACHE=ROOT/'tmp/m3_helical'

def triangles(s):
    v,t=s.tessellate(.7,.14)
    return np.array([p.toTuple() for p in v])[np.array(t)]

def draw(ax,s,color,alpha=1):
    tri=triangles(s)
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-14)
    light=np.array([.6,-.3,.74]);light/=np.linalg.norm(light)
    strength=.40+.60*np.maximum(0,normals@light)
    colors=np.array(to_rgb(color))[None,:]*strength[:,None]
    ax.add_collection3d(Poly3DCollection(tri,facecolor=colors,edgecolor='none',alpha=alpha,rasterized=True))

def limits(ax,shapes):
    bb=cq.Compound.makeCompound(shapes).BoundingBox();a=np.array([bb.xmin,bb.ymin,bb.zmin]);b=np.array([bb.xmax,bb.ymax,bb.zmax]);span=b-a
    ax.set(xlim=(a[0]-5,b[0]+5),ylim=(a[1]-5,b[1]+5),zlim=(a[2]-5,b[2]+5),xlabel='x / mm',ylabel='y / mm',zlabel='z / mm')
    ax.set_box_aspect(np.maximum(span,20));ax.view_init(23,45)
    for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:axis.set_major_locator(MaxNLocator(3))
    ax.grid(False);ax.tick_params(labelsize=8)

def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=165);plt.close(fig)

def main():
    P={f.stem.removesuffix('_full'):cq.Shape.importBrep(str(f)) for f in CACHE.glob('*_full.brep')}
    import csv
    mass=list(csv.DictReader((ROOT/'results/m3_review/mass_heat_capacity.csv').open(encoding='utf-8')))
    mat={r['part']:r['material'] for r in mass if r['case']=='Case0' and r['diameter_mm']=='50' and r['variant']=='full'}
    fig=plt.figure(figsize=(12,7),layout='constrained');ax=fig.add_subplot(111,projection='3d')
    for n,s in P.items():
        if 'bolt' in n or mat[n] in ['oil','water_equivalent']:continue
        alpha=.055 if n in ['motor_case','gear_case_front','gear_case_rear','motor_gear_adapter'] else 1
        draw(ax,s,COL[mat[n]],alpha)
    limits(ax,list(P.values()));ax.set_title('S3 helical concept | same shaft centres, housing, motor and brake\nActual CAD tessellation; transparent housings; no temperature/efficiency result')
    save(fig,'assembly_helical')
    for stage,x,w,small,big,yc,zc in [(1,33,25,'input_shaft','stage1_gear',120,100),(2,95,32,'intermediate_shaft','stage2_gear',120,0)]:
        slab=old.box(x,x+w,-200,350,-200,300)
        pair=[P[small].intersect(slab),P[big]]
        fig=plt.figure(figsize=(10,6),layout='constrained');ax=fig.add_subplot(111,projection='3d')
        draw(ax,pair[0],'#cc9755');draw(ax,pair[1],'#638ca8');limits(ax,pair)
        ax.set_title(f'Stage {stage}: actual helical BREP | 20 RH / 60 LH, beta=20 deg\nS3 transverse-system concept, not manufacturing geometry')
        save(fig,f'stage{stage}_helical_detail')
    fig=plt.figure(figsize=(12,5.5),layout='constrained')
    spur=cq.importers.importStep(str(ROOT/'cad/m3_review/revised_parts/stage2_gear.step')).val()
    for i,(shape,title) in enumerate([(spur,'Archived spur gear'),(P['stage2_gear'],'Helical gear: actual screw-swept teeth')]):
        ax=fig.add_subplot(1,2,i+1,projection='3d');draw(ax,shape,'#638ca8');limits(ax,[shape]);ax.view_init(18,55);ax.set_title(title,fontsize=11)
    fig.suptitle('Same 60 teeth, mt=3 mm, face width=32 mm, keyed bore | S3 CAD comparison')
    save(fig,'spur_helical_comparison')
    thermal=cq.Shape.importBrep(str(CACHE/'stage2_gear_thermal.brep'))
    fig=plt.figure(figsize=(12,5.5),layout='constrained')
    for i,(shape,title) in enumerate([(P['stage2_gear'],'Full assembly: helical teeth'),(thermal,'Thermal candidate: equal-volume smooth wheel')]):
        ax=fig.add_subplot(1,2,i+1,projection='3d');draw(ax,shape,'#638ca8');limits(ax,[shape]);ax.set_title(title,fontsize=11)
    fig.suptitle('Same per-body heat capacity; keyed contacts retained; mesh contact law remains unknown')
    save(fig,'thermal_equivalent')
    print('5 actual-CAD figures generated')

if __name__=='__main__':main()
