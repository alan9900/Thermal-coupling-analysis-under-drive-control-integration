"""Scientific plots from actual RTH extraction, explicitly diagnostic."""
import csv,json,argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4'
def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('--study');args=ap.parse_args()
    if args.study:OUT=ROOT/'results/m4/studies'/args.study
    context='finite face contacts' if args.study else 'original whole-body contacts'
    meta=json.loads((OUT/'study_settings.json').read_text()) if (OUT/'study_settings.json').exists() else {}
    case_name=meta.get('case','B_BRAKE_ONLY_CONCEPT')
    origin='Brake onset' if case_name.startswith('B') else 'Controlled-cycle start'
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.dpi':150})
    hist=list(csv.DictReader((OUT/'pilot_temperature_history.csv').open()))
    groups=[('M4_BRAKE_DISC_HAT','Disc'),('M4_PAD_NEAR','Near pad'),('M4_OUTPUT_SHAFT','Output shaft'),
        ('M4_OUTPUT_BEARING_2','Output bearing rear'),('M4_GEAR_CASE_REAR','Gear case rear'),('M4_OIL_INVENTORY','Oil'),('M4_MOTOR_WINDING','Winding')]
    fig,ax=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
    for j,(name,label) in enumerate(groups):
        r=[x for x in hist if x['part']==name];t=[0]+[float(x['time_s']) for x in r]
        ax[0].plot(t,[25]+[float(x['maximum']) for x in r],label=label,color='C'+str(j))
        if name not in ['M4_PAD_NEAR','M4_BRAKE_DISC_HAT']:
            ax[1].plot(t,[0]+[float(x['maximum'])-25 for x in r],label=label,color='C'+str(j))
    ax[0].set(ylabel='Local maximum temperature [degC]',xlabel=origin+' [s]')
    ax[1].set(ylabel='Local maximum rise [K]',xlabel=origin+' [s]')
    for a in ax:
        a.grid(alpha=.2);a.legend(fontsize=8)
        if case_name.startswith('B'):a.axvline(3.775437,ls=':',color='gray',lw=1)
    fig.suptitle('Actual ANSYS diagnostic | S3 assumptions | '+context+'\n'+case_name+'; mesh / time validation tracked separately',fontsize=11)
    fig.savefig(OUT/'pilot_temperature_curves.png');plt.close(fig)
    data=np.load(OUT/'pilot_actual_FE_surface.npz');p=data['points']*1000;tri=data['triangles'];T=data['temperature'];time=float(data['time_s'])
    fig=plt.figure(figsize=(7,5.3),layout='constrained');a=fig.add_subplot(projection='3d')
    norm=Normalize(vmin=25,vmax=float(T.max()));col=Poly3DCollection(p[tri],linewidth=0,rasterized=True)
    col.set_facecolor(plt.get_cmap('inferno')(norm(T[tri].mean(axis=1))));a.add_collection3d(col)
    lo=p.min(axis=0);hi=p.max(axis=0);a.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='Axial X [mm]',ylabel='Y [mm]',zlabel='Z [mm]')
    a.set_xticks(np.round(np.linspace(lo[0],hi[0],3),1));a.set_xlabel('X [mm]',fontsize=9)
    a.set_box_aspect((.3,1,1));a.view_init(elev=23,azim=-25)
    fig.colorbar(ScalarMappable(norm=norm,cmap='inferno'),ax=a,shrink=.65,label='Temperature [degC]')
    a.set_title(f'Actual ANSYS disc FE field at {time:.3f} s\nS3 diagnostic; contact / mesh / time validation pending',fontsize=10)
    fig.savefig(OUT/'pilot_disc_actual_FE.png');plt.close(fig)
    r=list(csv.DictReader((OUT/'pilot_FE_energy_balance.csv').open()));t=[0]+[float(x['time_s']) for x in r]
    fig,ax=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for k,label in [('input_J','Input'),('stored_J','FE storage'),('convection_out_J','Convection out'),('radiation_net_out_J','Net radiation out')]:
        ax[0].plot(t,[0]+[float(x[k])/1000 for x in r],label=label)
    ax[0].set(xlabel='Time [s]',ylabel='Energy [kJ]');ax[0].legend();ax[0].grid(alpha=.2)
    ax[1].plot(t,[0]+[float(x['residual_J']) for x in r]);ax[1].set(xlabel='Time [s]',ylabel='Input - storage - boundaries [J]');ax[1].grid(alpha=.2)
    fig.suptitle('Actual diagnostic FE energy balance | native signed boundary results | S3 concept',fontsize=11)
    fig.savefig(OUT/'pilot_FE_energy_balance.png');plt.close(fig)
    print('Saved 3 actual FE diagnostic figures; no fabricated contours or calibrated temperatures')
if __name__=='__main__':main()
