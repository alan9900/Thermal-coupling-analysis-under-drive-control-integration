"""M4 inputs: immutable M1-derived histories, S3 candidates and material XML.
No temperature solve. Never overwrite accepted M1/M2/M3 or their nulls.
"""
import copy,csv,hashlib,json,math,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m4';RUN=Path('E:/ansys_runs/m4_case0_20261021')
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    OUT.mkdir(exist_ok=True);RUN.mkdir(exist_ok=True)
    source=yaml.safe_load((ROOT/'configs/m3_geometry.yaml').read_text(encoding='utf-8'))
    mats=source['materials'];mass=list(csv.DictReader((ROOT/'results/m3_review/mass_heat_capacity.csv').open(encoding='utf-8')))
    bodymat={r['part']:r['material'] for r in mass if r['case']=='Case0' and r['diameter_mm']=='50' and r['variant']=='thermal'}
    vols={r['part']:float(r['volume_m3']) for r in mass if r['case']=='Case0' and r['diameter_mm']=='50' and r['variant']=='thermal'}
    materials={k:dict(v) for k,v in mats.items()}
    materials['seal_equivalent']=dict(rho_kg_m3=1200,cp_J_kgK=1500,k_W_mK=.2)
    # Explicit equivalent bearing masses; output catalogue reference is not a
    # validation of this assembled bearing, contact resistance or preload.
    bearing_mass={'input':.2,'intermediate':.37,'output':.442}
    for ax,m in bearing_mass.items():
        key='bearing_'+ax
        materials[key]=dict(rho_kg_m3=m/vols[ax+'_bearing_1'],cp_J_kgK=460,k_W_mK=20,
            classification='S3_EFFECTIVE_ENVELOPE_NOT_SOLID_STEEL',mass_candidate_kg=m)
        for j in [1,2]:bodymat[ax+'_bearing_'+str(j)]=key
    # Use only local schema structure; all generated material values are ours.
    schema=Path('E:/Program Files/ANSYS Inc/v241/Addins/EngineeringData/Samples/Thermal_Materials.xml')
    tree=ET.parse(schema);doc=tree.find('./Materials/MatML_Doc');template=copy.deepcopy(doc.find('Material'))
    for child in list(doc):
        if child.tag=='Material':doc.remove(child)
    for key,p in materials.items():
        mat=copy.deepcopy(template)
        for node in list(mat):
            if node.tag!='BulkDetails':mat.remove(node)
        bulk=mat.find('BulkDetails');bulk.find('Name').text='M4_S3_'+key
        bulk.find('Description').text='Uncalibrated conceptual equivalent; see M4 parameter provenance.'
        for pd in list(bulk.findall('PropertyData')):
            prop=pd.get('property')
            if prop not in ['pr0','pr1','pr2']:bulk.remove(pd);continue
            param={'pr0':'pa1','pr1':'pa3','pr2':'pa4'}[prop]
            value=p[{'pr0':'k_W_mK','pr1':'rho_kg_m3','pr2':'cp_J_kgK'}[prop]]
            pd.find("ParameterValue[@parameter='%s']/Data"%param).text=str(value)
        doc.insert(0,mat)
    tree.write(RUN/'M4_materials.xml',encoding='utf-8',xml_declaration=True)
    shutil.copy2(RUN/'M4_materials.xml',ROOT/'configs/M4_materials.xml')
    cfg=dict(version='m4-case0-0.1',classification='S3_CONCEPT_NOT_CALIBRATED',case='Case0',baseline_tag='M3-v1.0',
        baseline_commit='7a6b9b1512495283fa12dd4a2a7ffdf698554d3e',materials=materials,body_materials=bodymat,
        unknown_actual=dict(contact_h_W_m2K=None,actual_cooling=None,calibrated_temperature=None,helical_loss_map=None),
        engineering=dict(contact_h_W_m2K=[100,1000,10000],bearing_k_W_mK=[5,20,45],external_h_W_m2K=[5,15,40],
            jacket_h_W_m2K=[100,300,800],coolant_K=[298.15,298.15,333.15],ambient_K=298.15,initial_K=298.15,
            emissivity_disc=.8,emissivity_case=.7,mesh_mm=[15,10,7],time_step_s=[1,.5,.25]),
        status='INPUT_PREPARATION_NOT_SOLVER_VALIDATION')
    write(ROOT/'configs/m4_case0.json',cfg);write(RUN/'m4_case0.json',cfg)
    checks=[]
    for case in ['A_internal_only','B_brake_only','C_combined','D_preheat_braking']:
        path=ROOT/'results/m2/cases'/f'{case}_forcing.csv'
        with path.open() as f:rows=list(csv.DictReader(f))
        maxres=0
        for r in rows:
            q=lambda n:float(r[n+'_engineering_W'])
            err=max(abs(q('copper')+q('iron')+q('rotor_other')+q('inverter_external')-float(r['emot_reference_W'])),
                abs(q('gear_mesh')+q('gear_bearing')+q('gear_other')-float(r['gear_reference_W'])),
                abs(q('disc')+q('pad')-float(r['disc_contact_W'])))
            maxres=max(maxres,err)
            assert math.isnan(float(r['calibrated_winding_heat_W'])) and err<1e-6
        checks.append(dict(case=case,rows=len(rows),budget_residual_W=maxres,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            origin='Archived M2 interval averages of accepted M1 sources; not newly measured nor regenerated M1',
            inverter_loaded=False,raw_calibrated_winding_still_NaN=True))
    write(OUT/'input_checks.json',dict(status='PASS_SOURCE_BUDGETS_ONLY',cases=checks,temperature_solve='NOT EXECUTED'))
    print('Prepared material library, explicit parameter ranges and four source budget audits')
if __name__=='__main__':main()
