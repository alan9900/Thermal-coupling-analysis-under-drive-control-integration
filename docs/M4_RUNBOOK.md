# M4 Case0 reproducibility (development / PARTIAL)

M3 baseline: `M3-v1.0` → `7a6b9b1512495283fa12dd4a2a7ffdf698554d3e`.
M4 development: `stage/M4-ansys`, [draft PR #5](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/5).
The accepted M0–M3 files/tags are read-only. No M4 completion tag is authorized.

## Current execution scope — 2026-10-22

The researcher has moved all future simulation work to **no regenerative braking**;
see [the current work plan](NO_REGEN_WORK_PLAN.md). Research remains paused. This
revision authorizes documentation and GitHub updates only, not model changes or
solver execution. Commands below reproduce **historical inputs**, including the
30 kW regeneration-limited sources; do not run them as the new default baseline.
The stopped B time-refinement and C contact/cooling queues are historical, not a
resume queue for the revised plan. Fresh zero-regeneration sources, provenance
and numerical verification will be required after a new execution instruction.
Do not relabel existing fields or temperature values as no-regeneration results.

## Actual software and inputs

ANSYS Workbench/Mechanical/MAPDL **2024 R1**, installed under
`E:/Program Files/ANSYS Inc/v241`. This is not ANSYS 2025 or a MATLAB surrogate.
The accepted STEP was really imported into Mechanical, with 129 parts / 131
solids (three disconnected oil inventory solids). Twenty-eight retained part
groups / 30 solids are meshed. Minor bolts, seals, fluid inventories, etc. are
suppressed with their missing heat capacity/paths remaining a limitation.

Actual native working folder: `E:/ansys_runs/m4_case0_20261021`. ASCII paths avoid
native DLL/path issues encountered with the Chinese workspace path. No ANSYS
binary or license file is distributed. MATLAB M1/M2 source histories are read
from accepted archived CSV; M4 finite element solutions use ANSYS, not MATLAB.

## Embedded native solver model

`results/m4/model_input/Case0_B_face_scoped.dat.gz` contains the actual complete
Mechanical-exported input: FE mesh, material coefficients, explicit finite
contacts, friction-ring loads, finite convection, open radiosity and load steps.
The uncompressed SHA256 is in `input_manifest.json`. It reproduces the first
**coarse diagnostic** B run, not a mesh-independent accepted model.

Extract to a fresh ASCII directory, then run (PowerShell):

```powershell
& 'E:/Program Files/ANSYS Inc/v241/ANSYS/bin/winx64/ANSYS241.exe' `
  -b -smp -np 2 -p ansys -j study `
  -dir 'E:/ansys_runs/m4_reproduce' `
  -i 'E:/ansys_runs/m4_reproduce/study.dat' `
  -o 'E:/ansys_runs/m4_reproduce/study.out'
```

The launcher may return before the native child. Require the terminal log,
zero solver errors, all expected result sets, and a separate FE energy audit.
Do not read an actively written RTH: an orphan DPF reader contributed to a
first Mechanical result-transfer failure. Preserve that failure; do not change
its `SolveFailed` status to `Solved`. The later face-scoped run did report
Mechanical `Solved`, and an actual Mechanical result image was exported.

## Thermal mesh verification

`mechanical_mesh_variants.py` and `run_mesh_variants.wbjn` add local thermal mesh
controls without changing M3 geometry. The first attempted face-only pad
refinements were rejected: automatic sweeping kept one element through the
8.5mm thickness. Those exports are not a valid convergence sequence.

The replacement explicitly sizes all eight axial pad edges to **6 / 12 / 24
layers**, keeps tangential pad size 3mm, and refines disc friction faces to
4 / 2 / 1mm. Actual mesh states, counts and quality must be recorded, then each
variant requires native solution and its own FE capacity weights. Node numbering
can change when contacts are regenerated even if solid volumes are unchanged;
never reuse nodal weights merely because counts or masses agree.

`export_native_brake.py` generates short native brake-only verification studies.
`export_native_sources.py` produces controlled first-cycle A/C/D source masks:
drive, optional 60s high-load hold, first brake, 30s cooling. They preserve M1-
derived energy but are not the full six-cycle M2 scenario. `run_native_studies.ps1`
runs named studies sequentially. Generated settings are not evidence of execution.

## Extraction and validation

Use the local DPF environment through its ASCII junction:
`E:/ansys_runs/m4_python_ascii/Scripts/python.exe`. It contains ansys-dpf-core
0.16.3; the installed ANSYS server is 7.1. The legacy server uses insecure gRPC
on **127.0.0.1 only**. No global service/network security change is made.

1. `prepare_fe_capacity.py RESULT --out OUTPUT` integrates rho*cp*N_i over actual
   SOLID278 elements. Copy native DPF arrays while their owners remain alive;
   temporary array views caused a Windows access violation in an earlier attempt.
2. `postprocess_pilot.py --study NATIVE_STUDY_FOLDER` checks native completion,
   expected sets/end time and exact physical-node coverage before extraction.
   It excludes contact/radiation ghost nodes from temperatures and heat capacity.
3. `energy_pilot.py --study NATIVE_STUDY_FOLDER` reads native signed SURF152
   boundary powers and SURF252 net radiosity flux. It compares integrated inputs
   with FE storage plus convection/coolant/radiation, not just source partitions.
4. `plot_pilot.py --study NAME` produces explicitly labelled diagnostic figures.

SURF152 SMISC2 is HFCTOT (W in this MKS input). DPF's generic metadata labels
that miscellaneous result `J`; the native element definition determines the
quantity. Preserve this mismatch in the receipt rather than silently treating
energy as power. SURF252 NMISC4 is area and NMISC7 is signed net radiation flux.
The diagnostic energy closure verifies this interpretation. Official methods:
[SURF152](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_elem/Hlp_E_SURF152.html),
[SURF252](https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/ans_elem/Hlp_E_SURF252.html).

## Physical limitations

All actual contact/cooling/temperature calibration fields remain null. M1's
inverter heat is external. Rotor/other is an equivalent region, not magnets.
Total losses are never added on top of their component losses. Gear mesh heat
allocation to driven-wheel equivalents is S3, not tooth-contact calibration.

Disc and pad loads prescribe the M1 candidate partition as net thermal entry;
friction contact-temperature exchange and moving local flash temperatures are
not resolved. The pad peak depends strongly on that uncalibrated boundary and
normal mesh. Constant material properties, stationary oil with finite film
links, prescribed bulk coolant temperature, absent hot-air recirculation,
partial radiative visibility, and missing idle/churning/temperature-feedback
losses limit interpretation. Numerical convergence is not physical calibration.

## Radiation cost and preserved attempts

The un-decimated 24-layer/1mm-face mesh produced about 78k radiation facets
and a 48.58GB binary view-factor matrix. That interrupted attempt is retained,
including its input, logs and partial RTH. Byte-preserving NTFS compression
reduced the original VF storage to about 3.28GB; the logical file is unchanged.

Native RDEC on both surfaces failed with "Critical topology breaking" on the
coarse casing face. The replacement reduces **only disc RSURF101** (90/95%),
leaving case RSURF102 unchanged. Solid FE meshes are unchanged. Independent
full/reduced medium and 90/95%-reduced fine comparisons are required; reducing
radiation faces is not itself proof of mesh independence.

An attempted 1e-6 radiosity-flux tolerance caused excessive first-step coupling
iterations; no result from that interrupted attempt is accepted. Fresh h-named
studies retain a 1e-6 thermal heat residual and native 1e-4 radiosity-flux criterion.
Their actual energy and temperature checks remain mandatory.

The trial PCG solver reported ill-conditioning and fell back to SPARSE.
It was stopped and was **not** adopted or described as verified. Production
calculations retain the standard direct solver; no forced matrix reuse is used.

Use post_completed_studies.py / watch_completed.py only for terminal zero-error
runs. contact_audit.py additionally validates native active-branch areas and oil
energy; extract_paths.py checks a drive-subassembly control volume independently.
An earlier coarse B cut balance missed its 0.5% threshold and remains BLOCKED
even though whole-model energy closure passed.

## Refined standalone reproduction

Large completed plaintext log copies in this development tree are stored as
byte-preserving `.out.gz` files to avoid millions of native listing lines in the
PR. `results/m4/native_log_packages.json` records both digests and the unchanged
native original path. Every compressed log was decompressed and verified before
replacing its redundant repository plaintext copy. Native originals and all
previous Git commits remain intact.

The finite-size packages in `results/m4/model_input/native_input_packages.json`
identify exact executed native inputs by SHA256. Each includes the embedded mesh,
materials, finite contacts, loads and time steps. Large RTH/WBPJ/VF files remain
local and checksummed; they are not claimed to be uploaded remotely.

Run the following with a local Python interpreter (the example environment path
is specific to this machine). Use a **fresh ASCII output folder**:

```powershell
& 'E:/ansys_runs/m4_python_ascii/Scripts/python.exe' `
  scripts/m4/prepare_reproduction.py C_normal12_rd95_dt1 `
  --out E:/ansys_runs/M4_Case0_fresh_reproduction
```

The helper verifies the gzip and exact-input digests and retains
`executed_original.dat`. If an input reads a local binary view-factor cache, it
removes only `VFOPT,READ` in the derived `study.dat`, so the same radiation facets
are recomputed by ANSYS. The preparation receipt is explicitly **NOT EXECUTED**;
it is not a new thermal solution or proof of cross-version reproduction.

Use the native solver command above with the new folder, wait for terminal
`RUN COMPLETED` and zero errors, then generate **fresh** capacity weights and
run temperature/energy extraction. Do not reuse old node weights:

```powershell
& 'E:/ansys_runs/m4_python_ascii/Scripts/python.exe' `
  scripts/m4/prepare_fe_capacity.py `
  E:/ansys_runs/M4_Case0_fresh_reproduction/study.rth `
  --out results/m4/studies/M4_Case0_fresh_reproduction
& 'E:/ansys_runs/m4_python_ascii/Scripts/python.exe' `
  scripts/m4/postprocess_pilot.py --study E:/ansys_runs/M4_Case0_fresh_reproduction
& 'E:/ansys_runs/m4_python_ascii/Scripts/python.exe' `
  scripts/m4/energy_pilot.py --study E:/ansys_runs/M4_Case0_fresh_reproduction
```

Use UTF-8 explicitly for JSON. Windows PowerShell 5.1's default ANSI reader
corrupted a Chinese metadata path in one attempt; the error and verified path
repair are preserved. This changed metadata only, not the source bytes, native
solver input or RTH. New runners explicitly specify `-Encoding UTF8`.

`summarize_studies.py`, `plot_comparisons.py`, and `check_acceptance.py` read
completed receipts. Missing results remain PENDING; old failed studies remain
BLOCKED. `document_qa.py` requires current file hashes and manual inspection of
all rendered pages before recording a visual pass.
