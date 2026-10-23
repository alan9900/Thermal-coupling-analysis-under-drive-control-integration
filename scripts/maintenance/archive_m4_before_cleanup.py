"""Preserve existing M4 evidence before authorized native-file cleanup.

This script does not launch a solver, change a model, or delete files. It verifies
existing receipts, archives the tracked workspace plus native documentary evidence,
then reads every archived member back and compares SHA256. Deletion is a separate,
explicit PowerShell operation against the exact roots in the resulting manifest.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/m4/storage_cleanup_20261023"
ARCHIVE_DIR = Path("E:/ansys_runs_archives")
ARCHIVE = ARCHIVE_DIR / "M4_core_results_20261023.zip"
ROOTS = [Path("E:/ansys_runs") / name for name in (
    "m4_case0_20261021", "m4_viewer_20261022",
    "M4_Case0_reproduction_prepared_20261021",
    "M4_D_reproduction_prepared_20261021", "m4_native_benchmark",
)]
DOC_EXT = {".json", ".err", ".log", ".wbjn", ".py", ".ps1", ".csv",
           ".txt", ".out", ".png", ".pdf", ".mac", ".ans", ".xml"}


def digest_stream(stream):
    h = hashlib.sha256()
    size = 0
    while chunk := stream.read(8 * 1024 * 1024):
        h.update(chunk)
        size += len(chunk)
    return h.hexdigest(), size


def digest(path):
    with path.open("rb") as f:
        return digest_stream(f)[0]


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if ARCHIVE.exists():
        raise FileExistsError(f"Refusing to overwrite archive: {ARCHIVE}")
    OUT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    base = (REPO / "results/m4").resolve()
    capture = json.loads((base / "contour_captures/capture_manifest.json").read_text(encoding="utf-8"))
    assert len(capture["figures"]) == 29
    for row in capture["figures"]:
        assert digest(base / "contour_captures" / row["image"]) == row["sha256"], row["image"]
    report_receipts = [
        ("M4_report", base / "document_checks.json"),
        ("M4_contour_explained", base / "contour_captures/document_checks.json"),
        ("PROJECT_REVIEW_AND_NEXT_PLAN", REPO / "reports/project_review_evidence/document_checks.json"),
    ]
    for name, receipt in report_receipts:
        row = json.loads(receipt.read_text(encoding="utf-8"))
        assert row["visual_inspection"] == "PASS"
        for ext, expected in row["sha256"].items():
            assert digest(REPO / "reports" / f"{name}.{ext}") == expected, (name, ext)
    packages = json.loads((base / "model_input/native_input_packages.json").read_text(encoding="utf-8"))
    for key, row in packages.items():
        p = base / "model_input" / row["file"]
        assert digest(p) == row["gzip_sha256"], key
        with gzip.open(p, "rb") as f:
            raw_hash, raw_bytes = digest_stream(f)
        assert raw_hash == row["raw_sha256"] and raw_bytes == row["raw_bytes"], key
    studies = ["A_normal12_rd95_dt1_retry1", "B_normal12_rd95h_dt2",
               "B_normal24_rd95h_dt1", "C_normal12_rd95_dt1", "D_normal12_rd95_dt1"]
    for name in studies:
        for f in ("pilot_temperature_history.csv", "study_settings.json"):
            assert (base / "studies" / name / f).is_file(), (name, f)
        if name.startswith(("A_", "C_", "D_")):
            assert (base / "studies" / name / "source_intervals.csv").is_file(), name
    for name in ("C_normal12_rd95_dt1", "D_normal12_rd95_dt1"):
        for f in ("pilot_FE_energy_balance.csv", "pilot_FE_energy_checks.json", "signed_heat_paths.csv"):
            assert (base / "studies" / name / f).is_file(), (name, f)
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    tags = subprocess.check_output(["git", "show-ref", "--tags"], cwd=REPO, text=True)
    inventory = []
    supplements = []
    for root in ROOTS:
        assert root.resolve().parent == Path("E:/ansys_runs").resolve()
        assert root.is_dir() and not root.is_symlink(), root
        for p in sorted(root.rglob("*")):
            if p.is_symlink():
                raise ValueError(f"Unexpected link in cleanup candidate: {p}")
            if not p.is_file():
                continue
            s = p.stat()
            rel = p.relative_to(root).as_posix()
            keep = p.suffix.lower() in DOC_EXT or (p.suffix.lower() == ".dat" and s.st_size <= 2_000_000)
            arc = f"native_documentary_evidence/{root.name}/{rel}" if keep else None
            inventory.append({"path": str(p), "root": str(root), "bytes": s.st_size,
                              "mtime_ns": s.st_mtime_ns, "documentary_archive_member": arc})
            if keep:
                supplements.append((p, arc))
    save("native_deletion_inventory.json", {
        "status": "PRE_DELETION_INVENTORY", "date": "2026-10-23",
        "authorized_scope": "Existing project-specific native models, full fields and solver caches only",
        "roots": [str(p) for p in ROOTS], "files": inventory,
        "file_count": len(inventory), "logical_bytes": sum(p["bytes"] for p in inventory),
        "excluded_roots": ["E:/ansys_runs/f510s_d280_20260928", "E:/ansys_runs/m4_python_ascii"],
    })
    checks = {"status": "PASS_PRE_ARCHIVE", "workspace_head": git_sha,
              "contour_sha256_checks": 29, "report_sha256_checks": 9,
              "report_visual_checks": "Existing Word-render receipts verified; no new report render claimed",
              "exact_input_gzip_and_decompressed_sha256_checks": len(packages),
              "temperature_source_histories_present": studies,
              "simulation_executed_this_task": False, "tags_before": tags,
              "drive_free_bytes_before_archive": shutil.disk_usage("E:/").free}
    save("preservation_checks.json", checks)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO).decode("utf-8").split("\0")
    members = [(REPO / x, "repository_snapshot/" + x) for x in tracked if x and (REPO / x).is_file()]
    members.append((Path(__file__), "repository_snapshot/scripts/maintenance/" + Path(__file__).name))
    for p in OUT.iterdir():
        members.append((p, "repository_snapshot/" + p.relative_to(REPO).as_posix()))
    unique = dict((arc, p) for p, arc in members + supplements)
    readme = """# Existing M4 core-results archive / 2026-10-23

This is an archive of existing evidence, not a new simulation. M4 remains PARTIAL.
Historical sources include a 30 kW vehicle regeneration limit; these are NOT the
future no-regeneration cases. All temperatures are S3 concept predictions.

Start with repository_snapshot/reports/M4_contour_explained.docx (29 actual native
contours, 30 pages) or its PDF. M4_report.docx/PDF explains numerical evidence and
remaining limitations. results/m4/studies preserves component temperatures, source
power histories, energy balance, signed heat paths and selected FE field subsets.

repository_snapshot contains the currently tracked workspace, including M0-M3 CAD,
sources, configurations, exact compressed executed M4 inputs and all small results.
This is a file snapshot, not a Git-history bundle. Git history/tags remain in the
original repository and on GitHub. native_documentary_evidence preserves local
logs, macros, screenshots, metadata and reference documents outside Git.

Large native WBPJ/MECHDB, RTH and scratch matrices are intentionally NOT included.
The full arbitrary-time 3D field and Workbench database cannot be reopened from
this archive. Recomputing with ANSYS and scripts/m4/prepare_reproduction.py plus
the exact input packages is required for a new full-field result. Reproduction
is not executed here and still requires suitable ANSYS license/resources.
Future simulations remain paused pending the researcher's separate instruction.

Verify each member against ARCHIVE_MEMBERS_SHA256.json. The external .sha256 file
verifies the entire ZIP. Native deletion inventory records files selected before
cleanup; the final deletion receipt is maintained separately in the repository.
"""
    archive_members = []
    partial = ARCHIVE.with_suffix(".zip.partial")
    if partial.exists():
        raise FileExistsError(partial)
    with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        z.writestr("README.md", readme)
        archive_members.append({"member": "README.md", "bytes": len(readme.encode()),
                                "sha256": hashlib.sha256(readme.encode()).hexdigest()})
        for arc, p in sorted(unique.items()):
            expected = digest(p)
            z.write(p, arc)
            archive_members.append({"member": arc, "bytes": p.stat().st_size, "sha256": expected})
        z.writestr("ARCHIVE_MEMBERS_SHA256.json", json.dumps(archive_members, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(partial) as z:
        for row in archive_members:
            with z.open(row["member"]) as f:
                actual, size = digest_stream(f)
            assert actual == row["sha256"] and size == row["bytes"], row["member"]
        assert len(z.namelist()) == len(archive_members) + 1
    partial.rename(ARCHIVE)
    zip_sha = digest(ARCHIVE)
    ARCHIVE.with_suffix(".zip.sha256").write_text(f"{zip_sha}  {ARCHIVE.name}\n", encoding="ascii")
    save("archive_verification.json", {
        "status": "PASS_ALL_MEMBERS_READ_BACK_SHA256_AND_SIZE", "archive": str(ARCHIVE),
        "archive_bytes": ARCHIVE.stat().st_size, "archive_sha256": zip_sha,
        "members_verified": len(archive_members), "native_documentary_files": len(supplements),
        "raw_native_models_and_full_fields_included": False,
        "native_file_count_selected": len(inventory), "native_logical_bytes_selected": sum(p["bytes"] for p in inventory),
        "free_bytes_after_archive": shutil.disk_usage("E:/").free,
    })
    print(json.dumps({"status": "ARCHIVE_VERIFIED_READY_FOR_SEPARATE_CLEANUP",
                      "archive": str(ARCHIVE), "archive_bytes": ARCHIVE.stat().st_size,
                      "members": len(archive_members), "candidate_files": len(inventory),
                      "candidate_logical_bytes": sum(p["bytes"] for p in inventory)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
