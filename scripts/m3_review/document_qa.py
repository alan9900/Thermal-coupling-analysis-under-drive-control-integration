"""Actual Word rendering, OMML inspection and explicit visual QA record."""
import sys,json,hashlib,xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path
import pymupdf
from docx import Document
from docx.oxml import OxmlElement
from docx.shared import Pt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m3_review';BASE='M3_geometry_review'
def render():
    import win32com.client
    path=ROOT/'reports'/f'{BASE}.docx';d=Document(path)
    for table in d.tables:
        for i,row in enumerate(table.rows):
            props=row._tr.get_or_add_trPr();props.append(OxmlElement('w:cantSplit'))
            if i==0:props.append(OxmlElement('w:tblHeader'))
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.05
                    for run in p.runs:run.font.size=Pt(9);run.font.bold=i==0
    d.core_properties.language='zh-CN';d.save(path)
    with ZipFile(path) as z:
        # The authored review contains six display and two inline equations.
        xml=ET.fromstring(z.read('word/document.xml'));math=len(xml.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'));images=len([n for n in z.namelist() if n.startswith('word/media/')]);assert math==8 and images==7,(math,images)
    app=win32com.client.DispatchEx('Word.Application');app.Visible=False;app.DisplayAlerts=0;app.AutomationSecurity=3;doc=None
    try:
        doc=app.Documents.Open(str(path),ReadOnly=True,AddToRecentFiles=False);doc.ExportAsFixedFormat(str(ROOT/'reports'/f'{BASE}.pdf'),17)
    finally:
        if doc is not None:doc.Close(False)
        app.Quit()
    pdf=pymupdf.open(ROOT/'reports'/f'{BASE}.pdf');folder=ROOT/'tmp/m3_review_qa';folder.mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(pdf):page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(folder/f'page_{i+1:02d}.png')
    text='\n'.join(p.get_text() for p in pdf)
    for expected in ['BLOCKED','752.839','911.057','NOT EXECUTED','M2']:assert expected in text,expected
    data=dict(status='PASS_RENDER_STRUCTURE',editable_math_objects=math,figures=images,pdf_pages=len(pdf),visual_inspection='PENDING',
        post_pandoc_changes='Table layout only: font, repeating headers, no split rows; equations unchanged.',
        document_sha256={ext:hashlib.sha256((ROOT/'reports'/f'{BASE}.{ext}').read_bytes()).hexdigest() for ext in ['md','docx','pdf']})
    (OUT/'document_checks.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print(data)
def record_visual():
    path=OUT/'document_checks.json';r=json.loads(path.read_text())
    for ext,h in r['document_sha256'].items():assert hashlib.sha256((ROOT/'reports'/f'{BASE}.{ext}').read_bytes()).hexdigest()==h
    r.update(visual_inspection='PASS',visually_inspected_pages=list(range(1,r['pdf_pages']+1)),review='All Word-rendered pages inspected, including seven CAD/engineering figures, equations, Chinese text, tables and pagination.')
    path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('Visual QA recorded.')
if __name__=='__main__':{'render':render,'record-visual':record_visual}[sys.argv[1]]()
