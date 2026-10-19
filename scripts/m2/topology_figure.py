"""Exact code-native network diagram; nodes/edges come from the M2 YAML."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Patch
from matplotlib.lines import Line2D
import yaml

ROOT=Path(__file__).resolve().parents[2]

def main():
    p=yaml.safe_load((ROOT/'configs/m2_thermal_network.yaml').read_text(encoding='utf-8'))
    pos={'disc':(.9,3.6),'pad_caliper':(.9,1.8),'output_shaft':(2.7,3.6),'output_bearing':(4.5,3.6),
         'gears':(6.3,3.6),'oil':(6.3,1.8),'gear_case':(8.1,3.6),'motor_case':(9.9,3.6),
         'stator':(11.7,3.6),'winding':(11.7,5.2),'rotor_other':(11.7,1.8),'shield':(2.7,5.8),'local_air':(6.3,7.1)}
    fig,ax=plt.subplots(figsize=(14,8),layout='constrained');ax.set(xlim=(-.15,12.7),ylim=(.1,8.5));ax.axis('off')
    band=FancyBboxPatch((3.55,.9),8.9,4.9,boxstyle='round,pad=0.08',facecolor='#eff7f1',edgecolor='#8fb59a',lw=1)
    ax.add_patch(band);ax.text(7.9,1.1,'Drive thermal domain: bearing + gears/oil/cases + motor',ha='center',fontsize=10,color='#356344')
    colors={'conduction':'#6a6974','convection':'#247aa6','radiation':'#c75d39'}
    for group,color in colors.items():
        for edge in p[group]:
            a,b=pos[edge['from']],pos[edge['to']]
            rad=0
            if group=='radiation':rad=-.28 if edge['from']=='disc' else .1
            if group=='convection' and edge['from']=='disc':rad=.15
            if edge['from']=='pad_caliper' and edge['to']=='gear_case':rad=-.20
            ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-',connectionstyle=f'arc3,rad={rad}',lw=1.7 if edge['cut'] else .9,
                                        color=color,zorder=2,linestyle='--' if group=='radiation' else '-'))
    for node,(x,y) in pos.items():
        face='#e8f0fb' if node not in p['drive_domain'] else '#ddecdf'
        ax.add_patch(FancyBboxPatch((x-.73,y-.3),1.46,.6,boxstyle='round,pad=.03',facecolor=face,edgecolor='#52708d',zorder=3))
        ax.text(x,y,node.replace('_','\n'),ha='center',va='center',fontsize=9,zorder=4)
    for x,y,label,target in [(1,7.6,'Ambient 298.15 K','local_air'),(9.9,7.5,'Coolant 298.15 K','motor_case')]:
        ax.text(x,y,label,ha='center',bbox=dict(boxstyle='round',fc='#fff4d9',ec='#b49b63'),fontsize=10)
        ax.annotate('',xy=pos[target],xytext=(x,y-.3),arrowprops=dict(arrowstyle='<->',color='#8c9aa8',lw=1.2))
    ax.text(.1,.5,'Other ambient convection/radiation edges are listed in the configuration.\nInverter is external; source totals are never loaded alongside their components.',fontsize=10,color='#404653')
    ax.legend(handles=[Line2D([0],[0],color=c,label=g.title()) for g,c in colors.items()],loc='upper left',bbox_to_anchor=(0,.98),frameon=False)
    ax.set_title('S3 CONCEPT LPTN - 13 dynamic nodes; topology/areas/contacts NOT geometrically calibrated',fontsize=13,pad=10)
    out=ROOT/'results/m2';fig.savefig(out/'thermal_topology.png',dpi=180);fig.savefig(out/'thermal_topology.svg');plt.close(fig)
    print('Topology PNG/SVG saved, 13 nodes and uniquely classified crossing edges.')

if __name__=='__main__':main()
