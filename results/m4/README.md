# M4 actual execution evidence — development, not accepted

ANSYS Workbench/Mechanical 2024 R1 is installed and has been executed. The native
working directory is `E:/ansys_runs/m4_case0_20261021`; large project/scratch files
are outside Git. Reproducible journals and source scripts are in `scripts/m4`.
All present material, contact and cooling candidates are S3 engineering values.
Actual calibrated contact/cooling/temperature fields remain null.

- `attempts/`: preserved unsuccessful import/save/mesh/solve attempts. In the
  earliest face audit, `area_m2` incorrectly contains native mm². Use the corrected
  `face_regions_SI.json` only (native centroids are explicitly mm).
- `input_tests.json`: preprocessing tests only, not FE validation.
- `contact_scope_candidates.json`: initial fail-closed face mapping; 24 small
  oil/wheel cut faces failed the 3% area tolerance.
- `contact_scope_resolved.json`: all 24 uniquely mapped within 1 mm / 10% area,
  explicitly limited to those imported small wet faces. Discrepancies remain in
  `import_mapping_audit`. This does not validate oil-film conductance.
- `live_rth_inspection.json`: subset of converged native result sets read while
  the solver runs; neither full-transient completion nor validation.
- The first full B pilot uses 332431 solid elements / 88049 solid nodes, 2-core
  SMP. It is a diagnostic with original whole-body finite-contact scoping.
  A subsequent face-scoped model is required before interpreting coupling.

The first capacity extraction assumed nodal body selections; that assumption
was rejected. `dpf_regions.py` now resolves Elemental or Nodal selections before
forming SOLID278 capacity weights. No capacity or energy PASS may be claimed
until the native volume and whole-network energy checks actually finish.

No M4 completion tag, M4 merge, M5 calculation, Fluent calculation, or claimed
measured temperature calibration is authorized.
