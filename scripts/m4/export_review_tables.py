"""Parameter provenance and interrupted-attempt receipts, without fake passes."""
import csv,hashlib,json,re,shutil
from pathlib import Path
from export_native_brake import RUN,ROOT
OUT=ROOT/'results/m4'
def write(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    config=json.loads((ROOT/'configs/m4_case0.json').read_text())
    rows=[]
    for material,values in config['materials'].items():
        for key in ['rho_kg_m3','cp_J_kgK','k_W_mK']:
            rows.append(dict(material=material,parameter=key,engineering_candidate=values[key],actual_calibrated_value=None,
                classification='S3_ENGINEERING_ASSUMPTION',reference='M3 engineering candidate carried into M4; no actual material grade certification'))
    write(OUT/'material_parameter_table.csv',rows)
    contacts=json.loads((OUT/'contact_scope_resolved.json').read_text())['contacts']
    write(OUT/'contact_parameter_table.csv',[dict(source=r['source'],target=r['target'],source_CAD_faces=';'.join(map(str,r['source_face_ids'])),
        target_CAD_faces=';'.join(map(str,r['target_face_ids'])),h_candidate_W_m2K=r['h_W_m2K'],
        actual_h_W_m2K=None,classification='S3_'+r['classification'],qualification='Actual native area/branch coverage audited separately; not real TCC calibration') for r in contacts])
    eng=config['engineering']
    boundaries=[]
    for key in ['external_h_W_m2K','jacket_h_W_m2K','coolant_K','ambient_K','initial_K','emissivity_disc','emissivity_case']:
        values=eng[key] if isinstance(eng[key],list) else [eng[key]]
        boundaries.append(dict(parameter=key,candidate_values=';'.join(map(str,values)),actual_calibrated_value=None,
            classification='S3_ENGINEERING_ASSUMPTION',note='Cooling h scenarios are varied; coolant bulk range is not yet a completed sensitivity study' if key=='coolant_K' else 'Finite boundary; no actual system calibration'))
    write(OUT/'boundary_parameter_table.csv',boundaries)
    attempts=[
      ('B_normal24_dt1','STOPPED_RADIATION_MATRIX_COST','Original binary view-factor file 48.58GB; byte-preserving NTFS compression retained it. No completed study accepted.'),
      ('B_normal24_r95_dt1','FAILED_NATIVE_TOPOLOGY_BREAKING','All-surface RDEC broke coarse case-face topology; replacement reduces disc only.'),
      ('B_normal24_rd95_dt1','STOPPED_EXPENSIVE_RADIOSITY_CRITERION','1e-6 radiosity-flux criterion expensive; fresh h-named studies keep heat tolerance 1e-6 and radiosity 1e-4.'),
      ('B_mesh4_dt1','STOPPED_INVALID_PAD_REFINEMENT','Face-only refinement retained one through-thickness layer; rejected convergence sequence.'),
      ('B_normal12_PCG_verify','STOPPED_PCG_NONCONVERGENCE_FALLBACK','Native PCG reported ill-conditioning and fell back to SPARSE; stopped this redundant diagnostic. PCG was not adopted for production or claimed verified.')]
    receipts=[]
    for name,status,reason in attempts:
        folder=RUN/'studies'/name
        if not folder.exists():continue
        entry=dict(study=name,status=status,reason=reason,accepted_temperature_result=False,files={})
        for file in ['study.dat','study.out','study_settings.json']:
            p=folder/file
            if p.exists():
                with p.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
                entry['files'][file]=dict(local_path=str(p),bytes=p.stat().st_size,sha256=sha)
        p=folder/'study.out'
        if p.exists():
            with p.open('rb') as f:f.seek(max(0,p.stat().st_size-16000));tail=f.read().decode(errors='replace')
            (OUT/'attempts'/f'{name}_native_tail.txt').write_text(tail,encoding='utf-8')
            entry['native_run_completed']='RUN COMPLETED' in tail
            entry['reported_errors']=re.findall(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+(\d+)',tail)
        receipts.append(entry)
    (OUT/'attempts/native_refinement_attempts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print('Material/contact/boundary tables and actual interrupted-attempt evidence saved')
if __name__=='__main__':main()
