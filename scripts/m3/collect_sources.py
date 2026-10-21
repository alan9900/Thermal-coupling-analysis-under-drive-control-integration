"""Record primary-source access and narrowly scoped dimension facts, not OEM CAD."""
import hashlib,json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
SOURCES=[
 ('ORNL','https://info.ornl.gov/sites/publications/files/Pub26762.pdf','S1 reference only; Table2.7 printed46/PDF55','local: data/raw/m0/ornl_2010_prius_pub26762.pdf'),
 ('Brembo','https://www.bremboparts.com/europe/en/view-document/catalogue/disc/09-9908-21','S1 product envelope; custom hat/vane/PCD/caliper are S3',None),
 ('SKF6209','https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6209','S1 boundary size only; no life/preload selection',None),
 ('SKF6207','https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6207','S1 boundary size only',None),
 ('SKF6206','https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6206','S1 boundary size only',None),
 ('KHK','https://khkgears.net/gear-knowledge/gear-technical-reference/calculation-gear-dimensions/','Geometry method only; all selected modules/teeth/widths S3',None),
 ('CadQuery','https://cadquery.readthedocs.io/en/latest/importexport.html','Parametric source is Python; STEP neutral export, not parameter history',None)]
def main():
 rows=[]
 for name,url,use,local in SOURCES:
  row=dict(id=name,url=url,use=use,retrieval_date='2026-10-20')
  if local:
   path=ROOT/local[7:];row.update(local_original=local[7:],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),status='REUSED_READ_ONLY')
  else:
   try:
    r=requests.get(url,timeout=25);row.update(http_status=r.status_code,sha256=hashlib.sha256(r.content).hexdigest(),status='HTTP_OK' if r.ok else 'ACCESS_FAILED')
   except requests.RequestException as ex:row.update(status='ACCESS_FAILED',reason=type(ex).__name__)
  rows.append(row)
 out=ROOT/'data/raw/m3';out.mkdir(parents=True,exist_ok=True)
 payload=dict(sources=rows,source_facts=dict(ORNL_motor_casing_mm=[302,161],ORNL_stator_mm=[264,161.9,50.8],ORNL_rotor_mm=[160.4,51,50.165],
    Brembo_disc_mm=dict(outer=280,thickness=22,total_height=42,pilot=68),SKF6209_mm=[45,85,19],SKF6207_mm=[35,72,17],SKF6206_mm=[30,62,16]),
    applicability='Reference product values verified in original table/manufacturer browser. No catalogue certification is transferred to custom assembly. Failed direct retrievals are retained; no local original claimed.',
    limitations='Actual stub/mount, reducer, effective friction radius, hat/PCD, caliper, jacket/ports and vehicle envelope unknown. No finite-element or CFD execution.')
 (out/'manifest.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print([(r['id'],r['status']) for r in rows])
if __name__=='__main__':main()
