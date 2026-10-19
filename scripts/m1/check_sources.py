"""Independent source-interface/energy checks; no MATLAB result is trusted alone."""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/m1/engineering'
PARTS=['copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad']


def load(path):
    return np.genfromtxt(path,delimiter=',',names=True,encoding='utf-8')


def main():
    inputs=json.loads((ROOT/'results/m1/inputs.json').read_text(encoding='utf-8'))
    cfg=inputs['engineering_partition_configuration']; v={k:r[1] for k,r in cfg['parameters'].items()}
    assert cfg['metadata']['actual_internal_loss_map'] is None
    checks=[]; max_residual=0.; max_energy=0.; scales=[]; artifact_hashes={}
    nominal={}
    for path in sorted((OUT/'interface').glob('*.csv')):
        q=load(path); meta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
        assert meta['mode']=='engineering' and meta['classification']=='S3_ENGINEERING_NOT_MEASURED'
        assert not meta['original_calibrated_data_modified'] and not meta['M2_executed']
        assert meta['inverter_thermal_destination']=='external_boundary_not_motor_internal'
        assert meta['input_provenance']['code_commit']==inputs['provenance']['code_commit']
        t=q['time_s']; assert np.all(np.isfinite(t)) and np.all(np.diff(t)>0)
        assert np.all(np.isnan(q['calibrated_winding_heat_W'])) and np.all(q['source_class_code']==3)
        assert np.allclose(q['motor_speed_rpm']*2*np.pi/60,9*q['disc_speed_rad_s'],atol=1e-8)
        parent=load(ROOT/meta['trace_file']); side=meta['side']
        assert np.array_equal(t,parent['time_s'])
        for child,source in [('emot_total_reference_W','emot_combined_heat_W'),('gear_total_assumed_W','gear_heat_assumed_W'),('disc_contact_W','disc_contact_power_W')]:
            assert np.allclose(q[child],parent[source+'_'+side],atol=1e-9)
        for members,total in [(PARTS[:4],'emot_total_reference_W'),(PARTS[4:7],'gear_total_assumed_W'),(PARTS[7:],'disc_contact_W')]:
            residual=sum(q[k+'_engineering_W'] for k in members)-q[total]
            max_residual=max(max_residual,float(np.max(np.abs(residual))))
            energy=abs(float(np.trapezoid(residual,t))); max_energy=max(max_energy,energy)
            assert np.max(np.abs(residual))<1e-7 and energy<1e-7
        for part in PARTS:
            value=q[part+'_engineering_W']; lo=q[part+'_lower_W']; hi=q[part+'_upper_W']
            assert np.all(np.isfinite(value)) and np.all(value>=0)
            assert np.all(value>=lo-1e-7) and np.all(value<=hi+1e-7)
        # Rebuild nominal physical weights independently of MATLAB.
        n=q['motor_speed_rpm']; T=np.abs(q['motor_torque_Nm']); x=n/6000
        current=T/v['torque_constant_Nm_per_Arms']*np.sqrt(1+v['field_weakening_current_factor']*np.maximum(n/4500-1,0)**2)
        R=.077*(1+.00393*(v['winding_temperature_C']-20))/(1+.00393)
        raw=np.column_stack([3*R*current**2*(1+v['ac_copper_speed_factor']*x**2),v['iron_hysteresis_ref_W']*x+v['iron_eddy_ref_W']*x**2,v['rotor_speed_squared_ref_W']*x**2+v['motor_stray_load_ref_W']*(T/100)**2])
        parent_inv=parent['inverter_heat_estimated_W_'+side]
        L=q['emot_total_reference_W']; ratio=np.divide(parent_inv,L,out=np.full_like(L,np.nan),where=L>0)
        covered=np.isfinite(ratio)&(q['motor_torque_Nm']>0)&(L>0)
        f=np.full_like(L,v['fallback_inverter_fraction']); f[covered]=np.clip(ratio[covered]*v['drive_inverter_ratio_multiplier'],.01,.99)
        budget=L*(1-f); denom=raw.sum(axis=1)
        expected=np.divide(raw*budget[:,None],denom[:,None],out=np.zeros_like(raw),where=denom[:,None]>0)
        assert np.allclose(expected,np.column_stack([q[k+'_engineering_W'] for k in PARTS[:3]]),atol=1e-8)
        assert np.allclose(q['inverter_engineering_W'],L*f,atol=1e-8)
        assert np.allclose(q['disc_engineering_W'],.9*q['disc_contact_W'],atol=1e-8)
        scales.extend(q['motor_budget_normalization'][np.isfinite(q['motor_budget_normalization'])].tolist())
        energy={k:float(np.trapezoid(q[k+'_engineering_W'],t)/1000) for k in PARTS}
        nominal[(meta['case_id'],side)]=energy
        checks.append(dict(file=path.name,rows=len(q),classification='S3_ENGINEERING_NOT_MEASURED'))
        for artifact in [path,path.with_suffix('.json'),ROOT/meta['trace_file']]:
            artifact_hashes[str(artifact.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(artifact.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    assert len(checks)==46
    # Read sensitivity scenario vectors and integrated energies independently.
    parameters=np.genfromtxt(OUT/'sensitivity_parameters.csv',delimiter=',',names=True,dtype=None,encoding='utf-8')
    scenario_count=len(parameters); assert scenario_count==161
    for name,r in cfg['parameters'].items():
        assert np.all(parameters[name]>=r[0]) and np.all(parameters[name]<=r[2])
    sensitivity=np.genfromtxt(OUT/'sensitivity_energies.csv',delimiter=',',names=True,dtype=None,encoding='utf-8')
    assert len(sensitivity)==322
    for row in sensitivity:
        baseline=nominal[(row['case_id'],'left')]
        for members in [PARTS[:4],PARTS[4:7],PARTS[7:]]:
            assert abs(sum(row[k+'_kJ'] for k in members)-sum(baseline[k] for k in members))<1e-8
        for part in PARTS:
            assert row[part+'_lower_kJ']-1e-8<=row[part+'_kJ']<=row[part+'_upper_kJ']+1e-8
    # Critical M0 paths must match the immutable accepted snapshot byte-for-byte.
    protected=['configs/baseline_vehicle.yaml','data/raw/m0','results/m0','scripts/m0','reports/M0_report.md','reports/M0_report.docx','reports/M0_report.pdf']
    changed=subprocess.check_output(['git','diff','M0-v1.0','--name-only','--',*protected],cwd=ROOT,text=True).strip()
    assert not changed,changed
    for name,sha in inputs['provenance']['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_text(encoding='utf-8').encode()).hexdigest()==sha
    diagnostic=cfg['controls']['normalized_loss_ratio_warning_bounds']; scales=np.asarray(scales)
    tests=json.loads((OUT/'tests.json').read_text())
    result=dict(status='PASS',single_side_exports=checks,sensitivity_runs=322,scenario_count_per_case=scenario_count,
                maximum_partition_residual_W=max_residual,maximum_partition_energy_residual_J=max_energy,
                motor_budget_normalization_min=float(scales.min()),motor_budget_normalization_max=float(scales.max()),
                normalization_diagnostic_outside_fraction=float(np.mean((scales<diagnostic[0])|(scales>diagnostic[1]))),
                diagnostic_interpretation='large normalization reveals uncalibrated raw weights; this is a conserved allocation, not absolute 3IR copper-loss validation',
                model_code_commit=inputs['provenance']['code_commit'],matlab_new_test_groups=tests['test_group_count'],
                interface_and_parent_sha256=artifact_hashes,
                artifact_hash_definition='UTF-8 text normalized to LF for portable Git checkout verification',
                M0_protected_files_unchanged=True,strict_mode='EXPECTED_REJECTION',M1_approved=False,M2_executed=False)
    (OUT/'independent_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Independent source checks PASS:',len(checks),'single-side histories;',len(sensitivity),'sensitivity runs; max residual W',max_residual)


if __name__=='__main__': main()
