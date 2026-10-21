"""Plot stored actual FE triangles; no generated or interpolated contours."""
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from export_native_brake import ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('study');a=p.parse_args()
    folder=ROOT/'results/m4/studies'/a.study
    checks=json.loads((folder/'component_field_checks.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'figure.dpi':150})
    fig=plt.figure(figsize=(12,8),layout='constrained')
    for i,r in enumerate(checks['components'],1):
        d=np.load(folder/r['file']);points=d['points']*1000;tri=d['triangles'];T=d['temperature']
        ax=fig.add_subplot(2,3,i,projection='3d')
        low=float(T.min());high=max(low+1e-6,float(T.max()))
        norm=Normalize(low,high);c=Poly3DCollection(points[tri],linewidth=0,rasterized=True)
        c.set_facecolor(plt.get_cmap('inferno')(norm(T[tri].mean(axis=1))));ax.add_collection3d(c)
        lo=points.min(axis=0);hi=points.max(axis=0);span=hi-lo
        ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]')
        ax.set_box_aspect(np.maximum(span,.3*span.max()));ax.view_init(elev=24,azim=-30)
        for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:axis.set_major_locator(plt.MaxNLocator(3))
        ax.set_title(r['part'].replace('M4_','').replace('_',' ')+'\nat %.3f s; max %.4g C'%(r['time_s'],r['volume_nodal_max_C']),fontsize=8)
        fig.colorbar(ScalarMappable(norm=norm,cmap='inferno'),ax=ax,shrink=.5,label='degC',pad=.02,format='%.2f' if high-low>.1 else '%.5f')
    fig.suptitle('Actual ANSYS FE nodal fields | '+a.study+'\nS3 concept prediction; each component at its own peak time; independent color scales; numerical qualification separate',fontsize=10)
    fig.savefig(folder/'component_peak_fields.png');plt.close(fig)

if __name__=='__main__':main()
