"""Retrieve primary method sources and record hashes; do not change M0 evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/raw/m1'
SOURCES = [
    ('ORNL', 'Evaluation of the 2010 Toyota Prius Hybrid Synergy Drive System',
     'https://info.ornl.gov/sites/publications/files/Pub26762.pdf',
     'data/raw/m0/ornl_2010_prius_pub26762.pdf', 'S1 reference motor; Table 2.7 p46; pp58,62-63; no internal loss map'),
    ('NBS', 'Copper wire tables, NBS Handbook 100',
     'https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf',
     'nbs_copper_wire_tables.pdf', 'Generic copper resistance law; not MG2 material certification'),
    ('CORLEY2019', 'Thermal modelling of a small wind turbine gearbox for condition monitoring',
     'https://strathprints.strath.ac.uk/71746/1/Corley_etal_IET_JOE_2019_Thermal_modelling_of_a_small_wind_turbine.pdf',
     'corley2019_gearbox.pdf', 'S2 method only, DOI 10.1049/joe.2018.9282; CC BY 3.0; not concept gearbox coefficients'),
    ('SKF', 'Using a friction model as an engineering tool',
     'https://evolution.skf.com/using-a-friction-model-as-an-engineering-tool-3/',
     None, 'Primary manufacturer method: rolling/sliding/seal/drag torque; selected bearing data absent'),
    ('MATHWORKS_PMSM', 'FEM-Parameterized PMSM',
     'https://www.mathworks.com/help/simscape-electrical/ref/femparameterizedpmsm.html',
     None, 'Primary software method reference: current-dependent flux and iron-loss coefficients; no use of newer-version block'),
    ('INFINEON', 'Calculate IGBT losses for a SPWM voltage source converter',
     'https://community.infineon.com/t5/Knowledge-Base-Articles/Calculate-IGBT-losses-for-a-SPWM-voltage-source-converter/ta-p/381757',
     None, 'Primary manufacturer method only: conduction and switching losses require device/current data'),
    ('MATHWORKS_BRAKE', 'Thermal and Structural Analysis of Disc Brake',
     'https://www.mathworks.com/help/pde/ug/thermal-and-structural-analysis-of-disc-brake.html',
     None, 'Primary example of effusivity partition; its material values do not identify our disc/pad'),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    # CrossRef T1 metadata lookup; academic-search MCP is not mounted in this session.
    try:
        response=requests.get('https://api.crossref.org/works/10.1049/joe.2018.9282', timeout=40)
        response.raise_for_status()
        work=response.json()['message']
        (OUT/'corley_crossref.json').write_text(json.dumps({k:work.get(k) for k in
            ['DOI','title','author','container-title','published','license','URL']},indent=2)+'\n',encoding='utf-8')
        crossref='PASS'
    except requests.RequestException as exc:
        crossref=type(exc).__name__
    for key, title, url, name, use in SOURCES:
        r=dict(id=key,title=title,url=url,retrieved_utc=datetime.now(timezone.utc).isoformat(),applicability=use)
        if key=='ORNL':
            path=ROOT/name
            r.update(status='EXISTING_M0_ORIGINAL_REUSED_NO_REDOWNLOAD',local_file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            try:
                response=requests.get(url,timeout=60); response.raise_for_status()
                r.update(status='HTTP_OK',http_status=response.status_code,final_url=response.url,
                         sha256=hashlib.sha256(response.content).hexdigest(),bytes=len(response.content))
                if name:
                    assert response.content[:4]==b'%PDF'
                    path=OUT/name; path.write_bytes(response.content); r['local_file']=str(path.relative_to(ROOT)).replace('\\','/')
                else:
                    r['archive_note']='Metadata and retrieval hash only; official live page supports method, not fitted constants'
            except requests.RequestException as exc:
                r.update(status='DOWNLOAD_FAILED',error_type=type(exc).__name__,browser_verified=True)
        records.append(r)
    manifest=dict(scope='M1 engineering partition methods; not exhaustive literature review',
                  academic_mcp='NOT_AVAILABLE; primary official web sources and CrossRef used',crossref=crossref,sources=records)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({r['id']:r['status'] for r in records},indent=2))


if __name__=='__main__': main()
