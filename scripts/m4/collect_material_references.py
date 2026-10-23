"""Cache public references locally; publish numerical facts and provenance only."""
import csv,hashlib,json,urllib.request
from pathlib import Path
from export_native_brake import RUN,ROOT
SOURCES={
 'hydro6061':('https://www.hydro.com/Document/Index?id=560718&name=Alloy+6061.pdf','Hydro Alloy 6061, revision 2019/01, PDF page 2','pdf'),
 'kme2021':('https://www.kme.com/fileadmin/DOWNLOADCENTER/COPPER%20DIVISON/4%20Industrial%20Rolled/3_Datasheets/Datasheets_NEW_2021/2021_KME_Handout_e.pdf','KME 2021 handbook, PDF pages 12 and 14','pdf'),
 'nist_copper':('https://webbook.nist.gov/cgi/cbook.cgi?ID=C7440508&Mask=6&Units=CAL','NIST SRD69 copper solid Shomate, Chase 1998, 298-1358 K','html')}
def main():
    cache=RUN/'reference_data';cache.mkdir(exist_ok=True)
    out=ROOT/'data/raw/m4_reference';out.mkdir(parents=True,exist_ok=True)
    records={}
    for key,(url,title,ext) in SOURCES.items():
        path=cache/(key+'.'+ext)
        try:
            if not path.exists():
                with urllib.request.urlopen(url,timeout=45) as response:raw=response.read()
                assert (raw.startswith(b'%PDF') if ext=='pdf' else b'Copper' in raw)
                path.write_bytes(raw)
            records[key]=dict(url=url,title=title,download='ACTUAL_FILE_CACHED',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size,local_cache=str(path),classification='S2_PUBLISHED_REFERENCE_NOT_ACTUAL_ASSEMBLY_MATERIAL',
                redistribution='Full catalog kept locally; Git contains numerical facts, URL and checksum only')
        except Exception as e:records[key]=dict(url=url,title=title,download='BLOCKED_LOCAL_DOWNLOAD',error=str(e),sha256=None)
    t=298.15/1000
    cp_cal=4.237312+6.715751*t-7.469620*t*t+3.339491*t**3+.016398/t**2
    cp=cp_cal*4.184/.063546
    facts=[
      dict(reference='hydro6061',material='6061 T6/T6511 extrusion',parameter='rho_kg_m3',published_value=.098*27679.9047102,model_candidate=2710,temperature='density as listed',note='Converted 0.098 lb/in3, published rounded density; not casting grade certification'),
      dict(reference='hydro6061',material='6061 T6/T6511 extrusion',parameter='k_W_mK',published_value=167,model_candidate=170,temperature='25 degC',note='Actual housing alloy unknown'),
      dict(reference='kme2021',material='C11000 Cu-ETP, PDF p12',parameter='rho_kg_m3',published_value=8920,model_candidate=8960,temperature='20 degC annealed',note='Published reference, not winding fill / porosity'),
      dict(reference='kme2021',material='C11000 Cu-ETP, PDF p12',parameter='cp_J_kgK',published_value=394,model_candidate=385,temperature='20 degC annealed',note='Record brochure value as published; do not silently change to another copper value'),
      dict(reference='kme2021',material='C11000 Cu-ETP, PDF p12',parameter='k_W_mK',published_value=394,model_candidate=390,temperature='20 degC annealed',note='Bulk copper does not establish effective transverse winding conductivity'),
      dict(reference='kme2021',material='C10300 Cu-HCP, PDF p14',parameter='cp_J_kgK',published_value=385,model_candidate=385,temperature='20 degC annealed',note='Different copper grade, no actual MG2 winding grade identification'),
      dict(reference='nist_copper',material='pure Cu solid',parameter='cp_J_kgK',published_value=cp,model_candidate=385,temperature='298.15 K',note='CAL Shomate converted by 4.184 J/cal and 0.063546 kg/mol; not composite winding data')]
    with (out/'material_reference_crosscheck.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(facts[0]));w.writeheader();w.writerows(facts)
    (out/'source_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Published-reference facts recorded; NIST pure-Cu cp',cp)
    print({k:r['download'] for k,r in records.items()})
if __name__=='__main__':main()
