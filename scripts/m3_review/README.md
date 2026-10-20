# M3 geometry review reproduction

Use the existing CAD environment (`scripts/m3/requirements.txt`), e.g. on this
workspace `tmp/m3_cad/Scripts/python.exe`. Python3.13 / CadQuery2.8 / OCCT7.9.3.1
were actually executed. No MATLAB/ANSYS/Fluent solve is involved in this review.

Run in this order from the repository root:

```powershell
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/collect_sources.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/run_review.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/add_contact_review.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/analyze_review.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/check_review.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/radiation_review.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/plot_review.py
& tmp/m3_cad/Scripts/python.exe scripts/m3_review/write_report.py
```

Mechanical design constants are coordinated discrete45/50mm layouts in YAML
and editable Python source. Other diameters are rejected; this is not an
unrestricted dimensional optimizer. Changing a journal also requires bearing,
hub, casing, retention and seal revisions. The60mm adapter translates the motor
without resizing its reference envelope. Removable pressure-fit seats resolve a
trapped rear bearing, but do not validate the torque interface.

The smooth driven gears preserve volume with a swept pinion/oil clearance.
Integral pinions remain toothed to preserve conduction; heat source regions are
computed by actual CAD clipping, not spread along all of the shaft. No original
M3 or archived M2 output is overwritten. Live geometry is checked against the
saved masses; STEP hashes and finite storage plan are recorded separately.

Regressions passing means that failed engineering conditions were correctly
retained as BLOCKED. It is not release approval. Null real contacts, cooling,
materials and fits must not be replaced with engineering predictions.

Word must be generated from Markdown using the local pandoc-report-word
conversion script. Then run `py scripts/m3_review/document_qa.py render`, visually
inspect every page under`tmp/m3_review_qa/`, and only then use`record-visual`.
The QA script modifies table formatting only; equations remain editable OMML.

Reproducible evidence is bounded to this geometry review: no M4 solver setup,
mesh, ANSYS/Fluent execution, claimed temperatures or M3 completion Tag.
