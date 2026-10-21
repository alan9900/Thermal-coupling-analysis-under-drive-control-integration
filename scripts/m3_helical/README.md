# M3 bounded helical revision: reproduction

Run from repository root, sequentially. Old spur files remain read-only.

```powershell
tmp/m3_cad/Scripts/python.exe -u scripts/m3_helical/run_helical.py
tmp/m3_cad/Scripts/python.exe -u scripts/m3_helical/update_interface.py
tmp/m3_cad/Scripts/python.exe -u scripts/m3_helical/check_part_steps.py
tmp/m3_cad/Scripts/python.exe -u scripts/m3_helical/verify_helical.py
tmp/m3_cad/Scripts/python.exe -u scripts/m3_helical/plot_helical.py
tmp/m3_cad/Scripts/python.exe scripts/m3_helical/write_report.py
& C:/Users/90521/.codex/skills/pandoc-report-word/scripts/Convert-PandocReport.ps1 -InputPath reports/M3_helical_revision.md -OutputPath reports/M3_helical_revision.docx -ReferenceDoc reports/M3_reference.docx
py scripts/m3_helical/document_qa.py
```

CadQuery2.8.0/OCCT7.9.3.1/Python3.13.12; global Python has pywin32/python-docx/PyMuPDF, actual Microsoft Word renders PDF. Inspect all `tmp/m3_helical_qa/page_*.png`, then record with `py scripts/m3_helical/document_qa.py --record-visual`.

`run_helical.py` may take several minutes; writes ignored BREP cache under tmp/m3_helical for checks and figures. Do not start final verification before all eight exports finish. `--finalize-existing` only rechecks/summarizes already-executed four edge and fourteen mesh results; it does not execute new meshing checks. Initial parallel finalization failure retained transparently.

No MATLAB/ANSYS/Fluent solve in this revision. M1 losses unchanged/not recalibrated, prior mechanical BLOCKED items remain. Geometry validity does not imply axial bearing load acceptance, manufacturing quality or improved cooling/efficiency.
