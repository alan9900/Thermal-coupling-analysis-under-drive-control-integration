"""Small strict validation layer for M4 parameterized engineering inputs."""
import math
def validate(p,mode='engineering'):
    if mode not in ['strict','engineering']:raise ValueError('Unknown evidence mode')
    if mode=='strict' and any(v is None for v in p['unknown_actual'].values()):
        raise ValueError('Strict mode refuses uncalibrated internal/contact/cooling parameters')
    for key,values in p['engineering'].items():
        values=values if isinstance(values,list) else [values]
        if not values or any(v is None or not math.isfinite(v) or v<=0 for v in values):raise ValueError('Missing/invalid uncertainty range: '+key)
        if key in ['mesh_mm','time_step_s']:
            if values!=sorted(values,reverse=True):raise ValueError('Refinement grid must descend: '+key)
        elif len(values)==3 and values!=sorted(values):raise ValueError('Range must be lower/nominal/upper: '+key)
    for name,m in p['materials'].items():
        if any(m.get(k) is None or m[k]<=0 for k in ['rho_kg_m3','cp_J_kgK','k_W_mK']):raise ValueError('Invalid material '+name)
    return True
def radiation_W(Ta_K,Tb_K,area_m2,Fa_b,epsa,epsb):
    if min(Ta_K,Tb_K)<=0:raise ValueError('Absolute Kelvin required')
    if area_m2<=0 or not 0<=Fa_b<=1 or not 0<epsa<=1 or not 0<epsb<=1:raise ValueError('Invalid radiation geometry/material')
    return 5.670374419e-8*area_m2*Fa_b*(Ta_K**4-Tb_K**4)/(1/epsa+1/epsb-1)
