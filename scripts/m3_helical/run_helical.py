"""Execute helical CAD, exact collision checks and STEP roundtrips (no FEA)."""
import csv, hashlib, json, math, platform, subprocess, time
from pathlib import Path
from helical_cad import ROOT, settings, build, helical_gear, old
from run_geometry import csvout, writejson, overlaps
import cadquery as cq
OUT=ROOT/'results/m3_helical'; CAD=ROOT/'cad/m3_helical'
CHANGED={'input_shaft','intermediate_shaft','stage1_gear','stage2_gear','oil_inventory'}

def main():
    OUT.mkdir(parents=True,exist_ok=True); CAD.mkdir(parents=True,exist_ok=True)
    (CAD/'parts').mkdir(exist_ok=True)
    p=settings(); rows=[]; parameters=[]; checks=[]; runs=[]; reference={}; start=time.time()
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    oldmass=list(csv.DictReader((ROOT/'results/m3_review/mass_heat_capacity.csv').open(encoding='utf-8')))
    oldv={(r['case'],r['variant'],r['part']):float(r['volume_m3'])*1e9 for r in oldmass if r['diameter_mm']=='50'}
    for s in p['stages']:
        mt=s['mt_mm']; beta=math.radians(p['helix_angle_deg']); mn=mt*math.cos(beta)
        a=mn*(s['pinion_teeth']+s['gear_teeth'])/(2*math.cos(beta))
        assert abs(a-s['center_distance_mm'])<1e-10
        parameters.append(dict(stage=s['stage'],z_pinion=20,z_gear=60,ratio=3,mt_mm=mt,mn_mm=mn,center_mm=a,
            beta_deg=20,alpha_t_deg=20,alpha_n_deg=math.degrees(math.atan(math.tan(math.radians(20))*math.cos(beta))),
            pinion_hand='RH',gear_hand='LH',x_start_mm=s['start_x_mm'],x_end_mm=s['start_x_mm']+s['face_width_mm'],
            overlap_width_mm=s['face_width_mm'],pinion_twist_deg=math.degrees(s['face_width_mm']*math.tan(beta)/(mt*10)),
            gear_twist_deg=-math.degrees(s['face_width_mm']*math.tan(beta)/(mt*30)),
            axial_overlap_ratio=s['face_width_mm']*math.sin(beta)/(math.pi*mn),classification='S3_TRANSVERSE_SYSTEM_NONSTANDARD_MN'))
    csvout(OUT/'gear_parameters.csv',parameters)
    for case in ['Case0','CaseA','CaseB','CaseC']:
        for thermal in [False,True]:
            print('BUILD',case,thermal,flush=True)
            m=build(case,thermal); P=m['parts']; variant=m['variant']; name=f'{case}_d50_helical_{variant}'
            assert m['axes']=={'input':(120.0,100.0),'intermediate':(120.0,0),'output':(0,0)}
            materials=old.config()['materials']|{'seal_equivalent':dict(rho_kg_m3=1200,cp_J_kgK=1500)}
            for n,s in P.items():
                key=(variant,n)
                if case=='Case0':reference[key]=s.Volume()
                elif key in reference:assert abs(s.Volume()-reference[key])/max(s.Volume(),1)<1e-10
                ov=oldv.get((case,variant,n)); change=0 if ov is None else (s.Volume()-ov)/ov
                if n not in CHANGED:assert ov is not None and abs(change)<1e-8,(case,variant,n,change)
                mat=materials[m['materials'][n]]; rho=mat['rho_kg_m3']; cp=mat['cp_J_kgK']
                rows.append(dict(case=case,variant=variant,part=n,old_volume_mm3=ov,new_volume_mm3=s.Volume(),relative_change=change,
                    old_mass_kg=None if ov is None else ov*1e-9*rho,new_mass_kg=s.Volume()*1e-9*rho,
                    old_C_J_K=None if ov is None else ov*1e-9*rho*cp,new_C_J_K=s.Volume()*1e-9*rho*cp,
                    classification='ENVELOPE_NOT_INSTALLED_BEARING_MASS' if '_bearing_' in n else 'S3_GEOMETRIC_CANDIDATE'))
                if case=='Case0' and n in CHANGED:
                    cq.exporters.export(s,str(CAD/'parts'/f'{n}_{variant}.step'))
            print('INTERFERENCE',name,flush=True)
            cc=overlaps(m)
            for r in cc:r['variant']=variant
            checks+=cc; csvout(OUT/'interference_checks.csv',checks)
            failures=[r for r in cc if r['status']!='PASS']
            assert not failures, failures
            assembly=cq.Assembly(name=name)
            for n,s in P.items():assembly.add(s,name=n)
            path=CAD/(name+'.step');print('EXPORT',name,flush=True);assembly.export(str(path))
            loaded=cq.importers.importStep(str(path)).val(); vol=sum(s.Volume() for s in P.values())
            error=abs(loaded.Volume()-vol)/vol
            assert loaded.isValid() and len(loaded.Solids())==sum(len(s.Solids()) for s in P.values()) and error<1e-7
            runs.append(dict(case=case,variant=variant,parts=len(P),roundtrip_valid=True,roundtrip_volume_error=error,collision_pairs=len(cc),collisions=len(failures)))
            csvout(OUT/'volume_mass_capacity.csv',rows)
            writejson(OUT/'checks.json',dict(status='PASS_GEOMETRY_ONLY',source_commit=source,cadquery=cq.__version__,python=platform.python_version(),
                runs=runs,elapsed_s=time.time()-start,ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED',manufacturing_release='BLOCKED',loss_calibration='PARTIAL_UNCHANGED_M1'))
            # Store BREP for subsequent independent plots/checks; ignored tmp cache.
            if case=='Case0':
                cache=ROOT/'tmp/m3_helical';cache.mkdir(exist_ok=True)
                for n,s in P.items():s.exportBrep(str(cache/f'{n}_{variant}.brep'))
            print('PASS',name,error,flush=True)
    capacities=[]
    for case in ['Case0','CaseA','CaseB','CaseC']:
        by_body={(r['variant'],r['part']):r['new_volume_mm3'] for r in rows if r['case']==case}
        for variant,name in by_body:
            if variant!='full':continue
            vf=by_body['full',name];vt=by_body['thermal',name]
            error=abs(vf-vt)/max(vf,1)
            assert error<1e-7,(case,name,error)
            capacities.append(dict(case=case,part=name,full_volume_mm3=vf,thermal_volume_mm3=vt,relative_C_error=error))
    csvout(OUT/'thermal_capacity_checks.csv',capacities)
    writejson(OUT/'step_manifest.json',{'files':[{ 'path':f.relative_to(ROOT).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in CAD.rglob('*.step')]})
    assert len(runs)==8

if __name__=='__main__':main()
