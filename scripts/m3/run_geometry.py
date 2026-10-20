"""Execute B-rep CAD, all-pair interference, STEP roundtrip and finite exports."""
import csv,hashlib,json,platform,subprocess,time
from pathlib import Path
import cadquery as cq
from cad_model import ROOT,config,build,air_domain

OUT=ROOT/'results/m3';CAD=ROOT/'cad/m3';CASES=['Case0','CaseA','CaseB','CaseC']

def writejson(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def csvout(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def overlaps(model):
    rows=[];parts=model['parts'];keys=list(parts)
    for i,a in enumerate(keys):
        A=parts[a];ba=A.BoundingBox()
        for b in keys[i+1:]:
            B=parts[b];bb=B.BoundingBox()
            if min(ba.xmax,bb.xmax)-max(ba.xmin,bb.xmin)<1e-6 or min(ba.ymax,bb.ymax)-max(ba.ymin,bb.ymin)<1e-6 or min(ba.zmax,bb.zmax)-max(ba.zmin,bb.zmin)<1e-6:continue
            common=A.intersect(B).Volume()
            rows.append(dict(case=model['case'],part_a=a,part_b=b,common_volume_mm3=common,status='PASS' if common<.001 else 'INTERFERENCE'))
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True);(CAD/'base_parts').mkdir(parents=True,exist_ok=True)
    p=config();masses=[];checks=[];exports=[];start=time.perf_counter()
    protected=['configs/m2_thermal_network.yaml','scripts/m2','results/m2','reports/M2_report.md','reports/M2_report.docx','reports/M2_report.pdf']
    assert not subprocess.check_output(['git','diff','M2-v1.0','--name-only','--',*protected],cwd=ROOT,text=True).strip()
    for case in CASES:
        print('BUILD',case,flush=True);model=build(p,case);parts=model['parts']
        rows=overlaps(model);checks.extend(rows)
        failures=[r for r in rows if r['status']!='PASS']
        csvout(OUT/'interference_checks.csv',checks)
        assert not failures,failures
        assembly=cq.Assembly(name=case)
        for name,sh in parts.items():
            mat=p['materials'][model['materials'][name]];mass=sh.Volume()*1e-9*mat['rho_kg_m3'];bb=sh.BoundingBox()
            masses.append(dict(case=case,part=name,role=model['roles'][name],material=model['materials'][name],volume_mm3=sh.Volume(),mass_kg=mass,heat_capacity_J_K=mass*mat['cp_J_kgK'],surface_area_m2=sh.Area()*1e-6,solid_count=len(sh.Solids()),classification='S3_GEOMETRY_CANDIDATE'))
            color={'aluminium':(.6,.7,.8),'copper':(.85,.4,.12),'cast_iron':(.4,.42,.45),'stainless':(.9,.75,.35),'steel':(.4,.5,.65),'pad':(.2,.2,.2),'oil':(.9,.6,.1),'water_equivalent':(.2,.6,.9)}[model['materials'][name]]
            assembly.add(sh,name=name,color=cq.Color(*color))
            # Common bodies stored once; case-specific shield/support bodies once per case.
            path=CAD/'base_parts'/f'{name}.step' if case=='Case0' else CAD/case/f'{name}.step'
            if case=='Case0' or name not in base_names:
                path.parent.mkdir(parents=True,exist_ok=True);cq.exporters.export(sh,str(path))
        path=CAD/f'{case}_assembly.step';assembly.export(str(path))
        reloaded=cq.importers.importStep(str(path)).val()
        expected=sum(s.Volume() for s in parts.values());err=abs(reloaded.Volume()-expected)/expected
        assert reloaded.isValid() and err<1e-6,(case,err)
        air=air_domain(model);path_air=CAD/f'{case}_air_domain.step';cq.exporters.export(air,str(path_air))
        assert len(air.Solids())==1,'External local air must be connected'
        exports.append(dict(case=case,parts=len(parts),step_roundtrip_volume_relative_error=err,air_volume_m3=air.Volume()*1e-9,air_connected_solids=len(air.Solids()),air_valid=air.isValid()))
        if case=='Case0':base_names=set(parts)
        print('PASS',case,'parts',len(parts),'air m3',exports[-1]['air_volume_m3'],flush=True)
    csvout(OUT/'mass_heat_capacity.csv',masses)
    writejson(OUT/'geometry_checks.json',dict(status='PASS',cad_executed=True,cadquery=cq.__version__,python=platform.python_version(),case_count=4,exports=exports,
        tested_pairs_after_AABB_cull=len(checks),positive_overlap_limit_mm3=.001,positive_interferences=0,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        runtime_s=time.perf_counter()-start,classification=p['metadata']['classification'],ANSYS='NOT EXECUTED',Fluent='NOT EXECUTED',SolidWorks='NOT EXECUTED',manufacturing_validation='NOT EXECUTED'))
    # Neutral STEP storage plan: common parts once + 4 bounded assemblies + 4 air domains.
    files=list(CAD.rglob('*.step'));writejson(OUT/'step_manifest.json',dict(count=len(files),total_bytes=sum(f.stat().st_size for f in files),
        files={f.relative_to(ROOT).as_posix():dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files}))
    print('All geometry exports and checks PASS',flush=True)

if __name__=='__main__':main()
