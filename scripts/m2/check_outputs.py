"""Independent thermal/source/cut-set checks and SciPy integration oracle."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m2'

def sha(path):return hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()

def main():
    net=json.loads((OUT/'compiled_network.json').read_text());inp=json.loads((OUT/'inputs.json').read_text(encoding='utf-8'))
    ids=net['ids'];C=np.array(net['C_J_K']);fr=np.array(net['from'])-1;to=np.array(net['to'])-1
    cut=np.array(net['cut_group']);drive=np.array(net['drive'],bool);ambient=net['Tambient_K']
    B=np.zeros((13,len(fr)));B[fr,np.arange(len(fr))]=1;B[to,np.arange(len(fr))]=-1
    assert np.all(np.sum(B,axis=0)==0)
    records=[];max_relative=0.;hashes={}
    for path in sorted((OUT/'cases').glob('*.csv')):
        if path.stem.endswith('_forcing'):continue
        a=np.genfromtxt(path,delimiter=',',names=True);f=np.genfromtxt(path.with_name(path.stem+'_forcing.csv'),delimiter=',',names=True)
        meta=json.loads(path.with_suffix('.json').read_text());assert meta['classification']=='S3_CONCEPT_PREDICTION_NOT_CALIBRATED'
        assert meta['temperature_unit']=='K' and not meta['inverter_loaded_in_thermal_domain']
        t=a['time_s'];T=np.column_stack([a[n+'_K'] for n in ids]);h=f['end_s']-f['start_s']
        assert np.all(np.diff(t)>0) and np.all(T>0) and np.allclose(h,np.diff(t),atol=1e-10)
        assert np.all(np.isnan(f['calibrated_winding_heat_W']))
        parts=np.column_stack([f[n+'_engineering_W'] for n in ['copper','iron','rotor_other','inverter_external','gear_mesh','gear_bearing','gear_other','disc','pad']])
        assert np.allclose(parts[:,:4].sum(axis=1),f['emot_reference_W'],atol=1e-7)
        assert np.allclose(parts[:,4:7].sum(axis=1),f['gear_reference_W'],atol=1e-7)
        assert np.allclose(parts[:,7:].sum(axis=1),f['disc_contact_W'],atol=1e-7)
        parts[:,:3]*=meta['parameters']['motor_total_loss_scale']*meta['mask_motor_gear_brake'][0]
        parts[:,4:7]*=meta['parameters']['gear_total_loss_scale']*meta['mask_motor_gear_brake'][1]
        parts[:,7:]*=meta['mask_motor_gear_brake'][2]
        applied=parts[:,[0,1,2,4,5,6,7,8]].sum(axis=1)
        Ein=np.r_[0,np.cumsum(applied*h)]
        assert np.allclose(Ein,a['source_energy_J'],atol=1e-6)
        stored=(T-T[0])@C
        residual=Ein-a['ambient_net_out_J']-a['coolant_net_out_J']-stored
        rel=float(np.max(np.abs(residual))/max(1,Ein[-1]));max_relative=max(max_relative,rel);assert rel<1e-6
        allq=np.column_stack([a[n+'_W'] for n in net['edge_names']])
        for j in range(3):
            prefix=['radiation','hotair','solid'][j];sel=cut==j+1
            assert np.allclose(allq[:,sel].sum(axis=1),a[prefix+'_into_drive_W'],atol=1e-7)
            assert np.all(a[prefix+'_forward_J']>=np.maximum(a[prefix+'_net_J'],0)-1e-8)
            assert np.all(np.diff(a[prefix+'_forward_J'])>=-1e-8)
        assert np.allclose(a['drive_source_energy_J']+a['radiation_net_J']+a['hotair_net_J']+a['solid_net_J']-a['drive_boundary_net_out_J'],(T[:,drive]-T[0,drive])@C[drive],atol=1e-5)
        enabled=np.array(meta['path_enabled']);G=np.array(net['G0_W_K']);Gv=np.array(net['Gv']);R=np.array(net['Rad_W_K4'])
        for j in range(3):
            if not enabled[j]:G[cut==j+1]=0;Gv[cut==j+1]=0;R[cut==j+1]=0
        vel=np.r_[f['speed_m_s'],f['speed_m_s'][-1]]
        expected=(G[None,:]+Gv[None,:]*np.sqrt(vel[:,None]))*(T[:,fr]-T[:,to])+R[None,:]*(T[:,fr]**4-T[:,to]**4)
        assert np.allclose(allq,expected,atol=1e-6)
        records.append(dict(case=path.stem,rows=len(t),independent_relative_energy_residual=rel))
        for artifact in [path,path.with_suffix('.json'),path.with_name(path.stem+'_forcing.csv')]:hashes[str(artifact.relative_to(ROOT)).replace('\\','/')]=sha(artifact)
    assert len(records)==7
    # Adaptive Dormand-Prince oracle on the SAME interval-average forcing as C.
    a=np.genfromtxt(OUT/'cases/C_combined.csv',delimiter=',',names=True)
    f=np.genfromtxt(OUT/'cases/C_combined_forcing.csv',delimiter=',',names=True);t=a['time_s']
    Q=np.zeros((len(f),13));dest=[9,8,10,4,3,5,0,1]
    for name,j in zip(['copper','iron','rotor_other','gear_mesh','gear_bearing','gear_other','disc','pad'],dest):Q[:,j]+=f[name+'_engineering_W']
    G=np.array(net['G0_W_K']);Gv=np.array(net['Gv']);R=np.array(net['Rad_W_K4'])
    ag=np.array(net['AmbG0']);av=np.array(net['AmbGv']);ar=np.array(net['AmbRad']);cg=np.array(net['CoolG']);cool=net['Tcoolant_K']
    def rhs(time,temp):
        i=min(max(np.searchsorted(t,time,side='right')-1,0),len(f)-1);v=f['speed_m_s'][i]
        flow=(G+Gv*np.sqrt(v))*(temp[fr]-temp[to])+R*(temp[fr]**4-temp[to]**4)
        out=(ag+av*np.sqrt(v))*(temp-ambient)+ar*(temp**4-ambient**4)+cg*(temp-cool)
        return (Q[i]-B@flow-out)/C
    oracle=solve_ivp(rhs,(t[0],t[-1]),np.full(13,ambient),t_eval=t,rtol=1e-9,atol=1e-9,max_step=.125)
    assert oracle.success
    matlab=np.column_stack([a[n+'_K'] for n in ids]);error=float(np.max(np.abs(oracle.y.T-matlab)))
    assert error<.01,error
    np.savetxt(OUT/'scipy_oracle_C.csv',np.column_stack([t,oracle.y.T]),delimiter=',',header=','.join(['time_s']+[n+'_K' for n in ids]),comments='')
    for name,s in inp['provenance']['input_sha256'].items():assert sha(ROOT/name)==s,name
    protected=['configs/baseline_vehicle.yaml','configs/m1_heat_sources.yaml','configs/m1_source_partition.yaml','data/raw/m0','data/raw/m1','scripts/m0','scripts/m1','results/m0','results/m1','reports/M1_report.md','reports/M1_report.docx','reports/M1_report.pdf']
    assert not subprocess.check_output(['git','diff','M1-v1.0','--name-only','--',*protected],cwd=ROOT,text=True).strip()
    files=sorted((ROOT/'scripts/m2').glob('*.m'))
    receipt=dict(status='PASS',cases=records,maximum_independent_energy_residual_relative=max_relative,
        scipy_method='adaptive RK45 Dormand-Prince; same energy-preserving interval-average sources',scipy_oracle_max_temperature_error_K=error,
        M0_M1_protected_files_unchanged=True,model_commit=inp['provenance']['code_commit'],
        matlab_source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
        output_sha256=hashes,hash_definition='UTF-8 normalized LF',M2_approved=False,M2_tag_created=False,M3_started=False)
    (OUT/'independent_checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('Independent checks PASS:',len(records),'cases; max energy relative',max_relative,'; SciPy max T difference K',error)

if __name__=='__main__':main()
