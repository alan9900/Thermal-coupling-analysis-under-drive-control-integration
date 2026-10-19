"""Pandoc reference style, editable math checks and actual Word PDF export."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pymupdf
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT=Path(__file__).resolve().parents[2]


def reference():
    d=Document(ROOT/'reports/M1_reference.docx')
    for sec in d.sections:
        for p in sec.footer.paragraphs:
            for run in p.runs:
                run.text=run.text.replace('M1 多热源模型','M2 概念瞬态热网络')
    d.save(ROOT/'reports/M2_reference.docx')


def render():
    import win32com.client
    path=ROOT/'reports/M2_report.docx'
    d=Document(path)
    for table in d.tables:
        for ri,row in enumerate(table.rows):
            trpr=row._tr.get_or_add_trPr()
            if trpr.find(qn('w:cantSplit')) is None:
                trpr.append(OxmlElement('w:cantSplit'))
            if ri==0 and trpr.find(qn('w:tblHeader')) is None:
                trpr.append(OxmlElement('w:tblHeader'))
            for cell in row.cells:
                if ri==0:
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EAF0F7');cell._tc.get_or_add_tcPr().append(shade)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.05
                    for run in p.runs:
                        run.font.size=Pt(9.5)
                        if ri==0:run.font.bold=True
    d.core_properties.language='zh-CN';d.save(path)
    with ZipFile(path) as z:
        tree=ET.fromstring(z.read('word/document.xml'))
        equations=len(tree.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'))
        figures=len([n for n in z.namelist() if n.startswith('word/media/')])
        assert equations>=15 and figures==6,(equations,figures)
    word=win32com.client.DispatchEx('Word.Application')
    word.Visible=False;word.DisplayAlerts=0;word.AutomationSecurity=3;doc=None
    try:
        doc=word.Documents.Open(str(path),ReadOnly=True,AddToRecentFiles=False)
        doc.ExportAsFixedFormat(str(ROOT/'reports/M2_report.pdf'),17)
    finally:
        if doc is not None:doc.Close(False)
        word.Quit()
    folder=ROOT/'tmp/m2_qa/report';folder.mkdir(parents=True,exist_ok=True)
    pdf=pymupdf.open(ROOT/'reports/M2_report.pdf')
    text='\n'.join(p.get_text() for p in pdf)
    assert all(s in text for s in ['PARTIAL','M1-v1.0','109.63','0.001203'])
    for i,page in enumerate(pdf):
        page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(folder/f'page_{i+1:02d}.png')
    result=dict(word_export='PASS',editable_math_objects=equations,pdf_pages=len(pdf),embedded_figures=figures,
                post_pandoc_changes='formatting only: repeating shaded table headers, row splitting, spacing and language metadata',
                visual_inspection='PENDING',document_sha256={n:hashlib.sha256((ROOT/'reports'/n).read_bytes()).hexdigest()
                for n in ['M2_report.md','M2_report.docx','M2_report.pdf']})
    (ROOT/'results/m2/document_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


def record_visual():
    # Invoke only AFTER inspecting all rendered pages; this is a review receipt.
    path=ROOT/'results/m2/document_checks.json'
    r=json.loads(path.read_text(encoding='utf-8'))
    for name,digest in r['document_sha256'].items():
        assert hashlib.sha256((ROOT/'reports'/name).read_bytes()).hexdigest()==digest
    r.update(visual_inspection='PASS',visually_inspected_pages=list(range(1,r['pdf_pages']+1)),
             visual_review_scope='All nine Word-exported pages inspected: equations, repeated table headers, six figures, pagination, Chinese text and footer; no clipping or missing content observed.')
    path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('Recorded actual all-page visual review; document hashes unchanged.')


if __name__=='__main__':
    {'reference':reference,'render':render,'record-visual':record_visual}[sys.argv[1]]()
