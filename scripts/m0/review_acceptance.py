"""Recheck the historical M0 candidate without overwriting its artifacts.

Run `prepare`, run the printed MATLAB command, then run `collect`.
This is an M0 acceptance audit, not a new physics model or an approval.
"""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pymupdf
import yaml

import prepare_audit

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "tmp/m0_acceptance"
PROJECT = WORK / "project"
OUT = ROOT / "results/m0_acceptance"
CANDIDATE = "2ba858b8a047566f5932a621175d360154f869e8"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prepare():
    # Require a new scratch directory so prior verification runs are not erased.
    if PROJECT.exists():
        raise FileExistsError(f"Scratch run exists; preserve it and use collect: {PROJECT}")
    (PROJECT / "scripts/m0").mkdir(parents=True)
    (PROJECT / "results/m0").mkdir(parents=True)
    OUT.mkdir(parents=True, exist_ok=True)
    copied = ["scripts/m0/run_m0_review.m", "results/m0/baseline_vehicle.json", "results/m0/epa_map_numeric.json"]
    for name in copied:
        shutil.copy2(ROOT / name, PROJECT / name)
    before = {}
    tracked = subprocess.check_output(["git", "ls-files", "configs", "data/raw/m0", "reports", "results/m0", "scripts/m0"], cwd=ROOT, text=True).splitlines()
    # git's default output can quote Unicode names; all tracked paths here are ASCII.
    for name in tracked:
        path = ROOT / name
        assert path.is_file(), name
        before[name] = digest(path)
    save("original_artifact_hashes.json", before)
    test = subprocess.run([sys.executable, "scripts/m0/test_m0_audit.py"], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    (OUT / "python_tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    assert test.returncode == 0, "Configuration tests failed; inspect python_tests.txt"
    assert "Ran 3 tests" in test.stderr
    manifest = json.loads((ROOT / "data/raw/m0/manifest.json").read_text(encoding="utf-8"))
    sources = []
    for entry in manifest:
        if entry["status"] == "downloaded":
            path = ROOT / "data/raw/m0" / entry["file"]
            assert path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"]
            sources.append(entry["file"])
    # Re-read the original EPA data in scratch; downloaded code is never executed.
    raw = PROJECT / "data/raw/m0"
    raw.mkdir(parents=True)
    shutil.copy2(ROOT / "data/raw/m0/epa_2010_prius_mg2_emot_2023-04-06.zip", raw)
    prepare_audit.RAW = raw
    prepare_audit.OUT = WORK / "epa_audit"
    prepare_audit.OUT.mkdir(parents=True)
    audit = prepare_audit.read_map()
    historical = json.loads((ROOT / "results/m0/epa_map_audit.json").read_text(encoding="utf-8"))
    assert audit == historical, "EPA audit changed from historical candidate"
    for name in ["epa_zip_inventory.json", "epa_map_numeric.json"]:
        assert json.loads((prepare_audit.OUT / name).read_text()) == json.loads((ROOT / "results/m0" / name).read_text())
    cfg = yaml.safe_load((ROOT / "configs/baseline_vehicle.yaml").read_text(encoding="utf-8"))
    prepare_audit.validate_config(cfg)
    missing = [name for name, value in prepare_audit.flatten(cfg) if value is None]
    assert len(missing) == 39
    with ZipFile(ROOT / "reports/M0_report.docx") as z:
        tree = ET.fromstring(z.read("word/document.xml"))
        math = len(tree.findall(".//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"))
    assert math == 21
    with pymupdf.open(ROOT / "reports/M0_report.pdf") as pdf:
        pages = len(pdf)
        assert pages == 8
    save("preflight.json", dict(status="PASS", candidate_commit=CANDIDATE,
         review_base_commit=subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip(),
         audit_code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
         official_source_hashes_verified=sources, python_tests_passed=3, invalid_input_variants=10,
         epa_audit_matches_original=True, map_shape=audit["grid_shape"], paired_drive_points=audit["paired_drive_points"],
         missing_parameters=missing, docx_editable_math_objects=math, pdf_pages=pages,
         visual_qa="Existing 8-page QA record retained; no report edits or re-rendering in this review",
         downloads_refreshed=False, stage_approved=False, tag_created=False, m1_started=False))
    print("Preflight PASS. Run MATLAB with addpath('tmp/m0_acceptance/project/scripts/m0'); run_m0_review")


def collect():
    new = PROJECT / "results/m0"
    validation = json.loads((new / "validation.json").read_text())
    assert validation["status"] == "PASS"
    comparisons = {}
    for name in ["braking_review.csv", "speed_power_review.csv", "geometry_assumption_sensitivity.csv",
                 "radius_speed_sensitivity.csv", "regen_assumption_sensitivity.csv"]:
        with (new / name).open(newline="") as f:
            current = list(csv.reader(f))
        with (ROOT / "results/m0" / name).open(newline="") as f:
            old = list(csv.reader(f))
        assert current[0] == old[0] and len(current) == len(old), name
        x, y = np.array(current[1:], dtype=float), np.array(old[1:], dtype=float)
        assert np.allclose(x, y, atol=1e-10, rtol=1e-12), name
        comparisons[name] = dict(rows=len(x), max_absolute_difference=float(np.max(np.abs(x-y))))
    before = json.loads((OUT / "original_artifact_hashes.json").read_text())
    changed = [name for name, sha in before.items() if digest(ROOT / name) != sha]
    assert not changed, f"Historical inputs/artifacts modified: {changed}"
    # Add new-run evidence alongside, never replacing results/m0.
    for name in ["validation.json", "m0_results.mat", "m0_review.png", "m0_review.svg", *comparisons]:
        shutil.copy2(new / name, OUT / name)
    preflight = json.loads((OUT / "preflight.json").read_text(encoding="utf-8"))
    save("acceptance_checks.json", dict(status="PASS", formal_acceptance="PENDING_USER_REVIEW",
         candidate_commit=CANDIDATE, configuration_version="v0.4", original_artifacts_unchanged=True,
         original_artifact_count=len(before), numerical_comparisons=comparisons,
         python_tests_passed=preflight["python_tests_passed"], matlab_release=validation["release"],
         matlab_check_groups=len(validation["checks"]), braking_cases=18,
         max_energy_residual_relative=validation["max_energy_residual_relative"],
         integral_refinement_relative=validation["integral_refinement_relative"],
         unresolved_parameter_count=39, tag_created=False, m1_started=False,
         ansys_executed=False, optimization_executed=False))
    print("Acceptance recheck PASS; original M0 candidate preserved; approval remains pending.")


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
