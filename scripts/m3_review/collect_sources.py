"""Small primary-source snapshots, timestamps and hashes; no OEM claim."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
import requests
from review_cad import ROOT
folder=ROOT/'data/raw/m3_review';folder.mkdir(parents=True,exist_ok=True)
sources={
 'SKF_6208':'https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6208',
 'SKF_6209':'https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6209',
 'SKF_6210':'https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6210',
 'Schaeffler_arrangements':'https://www.schaeffler.com/remotemedien/media/_shared_media/08_media_library/01_publications/schaeffler_2/catalogue_1/downloads_6/mh1_technical_principles_de_en.pdf'}
rows=[]
for name,url in sources.items():
    ext='.pdf' if name.startswith('Schaeffler') else '.html';path=folder/(name+ext)
    # Windows native TLS works where this venv requests/OpenSSL fails; do not
    # disable certificate validation. Inputs here are fixed URLs/owned paths.
    command="Invoke-WebRequest -Uri '"+url+"' -OutFile '"+str(path).replace("'","''")+"'"
    cached=path.exists() and path.stat().st_size>1000
    res=None if cached else subprocess.run(['pwsh','-NoProfile','-Command',command])
    if res is not None and res.returncode:
        rows.append(dict(id=name,url=url,retrieved_UTC=datetime.now(timezone.utc).isoformat(),file=None,status='LOCAL_DOWNLOAD_BLOCKED',
            note='Primary PDF readable through web tool; local native HTTPS download failed. Do not claim an archived PDF.',provenance='S1_PUBLIC_REFERENCE_NOT_LOCAL_SNAPSHOT'))
        continue
    content=path.read_bytes()
    rows.append(dict(id=name,url=url,retrieved_UTC=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),status='SNAPSHOT_PRESENT',bytes=len(content),sha256=hashlib.sha256(content).hexdigest(),file=path.relative_to(ROOT).as_posix(),
        scope='Boundary dimensions / catalogue mass only; bearing selection, preload, fits, life and application are not validated' if name.startswith('SKF') else 'Locating/non-locating arrangement methodology, not validation of our design',
        provenance='S1_MANUFACTURER_REFERENCE_ONLY'))
(folder/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('Primary sources:',sum(x.get('file') is not None for x in rows),'archived;',sum(x.get('file') is None for x in rows),'local download blocked.')
