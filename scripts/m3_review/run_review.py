"""Executed OCCT audit. Checks are never bypassed to create a PASS result."""
import csv,hashlib,json,platform,subprocess,time
import cadquery as cq
from review_cad import *
from run_geometry import overlaps,csvout,writejson
OUT=ROOT/'results/m3_review';CAD=ROOT/'cad/m3_review'
CASES=['Case0','CaseA','CaseB','CaseC']

def main():
    OUT.mkdir(exist_ok=True,parents=True);CAD.mkdir(exist_ok=True,parents=True)
    start=time.perf_counter();checks=[];mass=[];runs=[];basehash={};contact=[]
    for case in CASES:
        print('BUILD CONCEPT TEMPLATE',case,flush=True);base=build(config(),case)
        for d in ([50,45] if case=='Case0' else [50]):
            for thermal in [False,True]:
                print('BUILD REVIEW',case,d,thermal,flush=True)
                m=build_review(d,case,thermal,base);P=m['parts'];tag=f'{case}_d{d}_{m["variant"]}'
                rows=overlaps(m)
                for row in rows:row.update(variant=m['variant'],diameter_mm=d)
                checks+=rows;csvout(OUT/'interference_checks.csv',checks)
                fail=[x for x in rows if x['status']!='PASS']
                if fail:print('BLOCKED',tag,fail,flush=True)
                assembly=cq.Assembly(name=tag)
                for n,s in P.items():
                    mat=MATERIALS[m['materials'][n]];v=s.Volume()*1e-9
                    # Bearing annuli are not solid steel: do not invent real mass.
                    bearing='_bearing_' in n
                    mass.append(dict(case=case,diameter_mm=d,variant=m['variant'],part=n,material=m['materials'][n],role=m['roles'][n],volume_m3=v,
                        geometric_solid_mass_candidate_kg=v*mat['rho_kg_m3'],geometric_solid_C_candidate_J_K=v*mat['rho_kg_m3']*mat['cp_J_kgK'],
                        installed_mass_kg=None if bearing else v*mat['rho_kg_m3'],installed_C_J_K=None if bearing else v*mat['rho_kg_m3']*mat['cp_J_kgK'],
                        classification='ENVELOPE_NOT_BEARING_STEEL_MASS' if bearing else 'S3_GEOMETRY_MATERIAL_CANDIDATE',solids=len(s.Solids()),area_m2=s.Area()*1e-6))
                    assembly.add(s,name=n)
                    if case=='Case0' and d==50 and not thermal:
                        folder=CAD/'revised_parts';folder.mkdir(exist_ok=True)
                        cq.exporters.export(s,str(folder/(n+'.step')))
                    if d==50:
                        key=(m['variant'],n)
                        if case=='Case0':basehash[key]=s.Volume()
                        elif n in basehash:
                            assert abs(s.Volume()-basehash[key])/max(s.Volume(),1)<1e-10,(case,n,'base mismatch')
                path=CAD/(tag+'.step');assembly.export(str(path))
                loaded=cq.importers.importStep(str(path)).val();v=sum(s.Volume() for s in P.values());err=abs(loaded.Volume()-v)/v
                assert loaded.isValid() and err<1e-6,(tag,err)
                regions={n:len(s.Solids()) for n,s in P.items()}
                # Contacts are geometric candidates. A touching nominal face does
                # not establish preload or a finite measured conductance.
                pairs=[('brake_disc_hat','disc_hub'),('disc_hub','output_shaft'),('disc_hub','hub_key_1'),('output_shaft','hub_key_1'),
                    ('output_shaft','output_bearing_2'),('output_bearing_2','gear_case_rear'),('caliper_reaction_bracket','gear_case_rear'),
                    ('caliper','caliper_reaction_bracket'),('motor_stator','motor_case'),('motor_gear_adapter','gear_case_front'),('gear_case_front','gear_case_rear'),
                    ('motor_input_coupling','motor_rotor_shaft'),('output_halfshaft_flange','wheel_halfshaft_interface')]
                for a,b in pairs:
                    A=P[a];B=P[b];dist=A.distance(B)
                    area=sum(f.intersect(B).Area() for f in A.Faces())*1e-6 if dist<1e-5 else 0
                    contact.append(dict(case=case,diameter_mm=d,variant=m['variant'],a=a,b=b,distance_mm=dist,nominal_contact_area_m2=area,
                        measured_contact_h_W_m2K=None,status='NOMINAL_TOUCH_REQUIRES_CONTACT_LAW' if area>1e-9 else 'GAP_OR_KEY_ONLY_INTERFACE'))
                row=dict(case=case,diameter_mm=d,variant=m['variant'],parts=len(P),valid=loaded.isValid(),roundtrip_relative_volume_error=err,
                    interferences=len(fail),status='BLOCKED' if fail else 'PASS_GEOMETRY_ONLY',region_solid_counts=regions)
                if not thermal:
                    air,pockets=external_air(m);cq.exporters.export(air,str(CAD/(tag+'_air.step')))
                    # Actual CAD probes at inlet, outlet and all points along the
                    # slanted duct centreline; outside points share one fluid solid.
                    probes=[]
                    if case=='CaseC':
                        for h in [-.2,0,10,30,50,70,70.2,90]:
                            x=216+max(0,h)*math.tan(math.radians(20));z=145+h
                            inside=air.isInside(cq.Vector(x,0,z),1e-6)
                            probes.append(dict(x=x,y=0,z=z,in_external_connected_air=inside))
                        assert all(x['in_external_connected_air'] for x in probes),probes
                    row.update(air_connected_solids=len(air.Solids()),air_valid=air.isValid(),closed_pockets_mm3=pockets,duct_centreline_probes=probes)
                    assert len(air.Solids())==1 and air.isValid()
                runs.append(row);writejson(OUT/'geometry_checks.json',dict(status='BLOCKED' if any(x['interferences'] for x in runs) else 'PASS_GEOMETRY_ONLY',
                    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),executed_CAD=True,cadquery=cq.__version__,python=platform.python_version(),runs=runs,
                    ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED',structural_certification='NOT EXECUTED',runtime_s=time.perf_counter()-start))
                csvout(OUT/'mass_heat_capacity.csv',mass);csvout(OUT/'contact_pairs.csv',contact)
                print(row['status'],tag,'pairs',len(rows),'volume error',err,flush=True)
    files=list(CAD.rglob('*.step'));writejson(OUT/'step_manifest.json',dict(count=len(files),total_bytes=sum(x.stat().st_size for x in files),files={x.relative_to(ROOT).as_posix():dict(bytes=x.stat().st_size,sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in files}))
    assert not any(x['interferences'] for x in runs),'BLOCKED: see interference_checks.csv'

MATERIALS=config()['materials']|{'seal_equivalent':dict(rho_kg_m3=1200,cp_J_kgK=1500,k_W_mK=.2)}
if __name__=='__main__':main()
