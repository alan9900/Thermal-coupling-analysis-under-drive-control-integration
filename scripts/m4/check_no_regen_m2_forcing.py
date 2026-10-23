"""P2-A independent input/energy preflight. Never evaluates temperatures.

The MATLAB adapter reuses m2_forcing's cumulative analytic primitive. This
checker instead clips every original interval to each target bin and sums
trapezoids of the original linear power. It does not import a thermal solver.
"""
from __future__ import annotations

import argparse
import copy
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = "configs/m4_no_regen_m2_baseline.json"
RAW_KEYS = ["copper", "iron", "rotor_other", "inverter", "gear_mesh", "gear_bearing", "gear_other", "disc", "pad"]
OUT_KEYS = ["copper", "iron", "rotor_other", "inverter_external", "gear_mesh", "gear_bearing", "gear_other", "disc", "pad"]
EXPECTED_IDS = ["disc", "pad_caliper", "output_shaft", "output_bearing", "gears", "oil", "gear_case", "motor_case", "stator", "winding", "rotor_other", "shield", "local_air"]


class Failure(RuntimeError):
    pass


def need(ok, why):
    if not bool(ok):
        raise Failure(why)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def verify_hashes(records):
    for row in records:
        need(sha(ROOT / row["path"]) == row["sha256"], "input/output SHA256 changed: " + row["path"])


def table(path):
    a = np.genfromtxt(path, delimiter=",", names=True, encoding="utf-8-sig")
    return {name: np.atleast_1d(a[name]) for name in a.dtype.names}


def near(a, b, atol, why, rtol=0):
    need(np.all(np.isfinite(a)) and np.all(np.isfinite(b)), why + ": nonfinite")
    need(np.allclose(a, b, atol=atol, rtol=rtol), why)


def m1_unit(name):
    explicit = {"time_s": "s", "vehicle_speed_m_s": "m/s", "disc_speed_rad_s": "rad/s", "motor_speed_rpm": "rpm", "motor_torque_Nm": "N*m", "current_proxy_Arms": "A_RMS_proxy_not_measured"}
    return explicit.get(name, "W" if name.endswith("_W") else "1")


def forcing_unit(name):
    return {"start_s": "s", "end_s": "s", "speed_m_s": "m/s", "motor_rpm": "rpm", "motor_torque_Nm": "N*m", "segment_id": "1"}.get(name, "W")


def check_raw(cfg, sides, metas):
    required = {key + "_engineering_W" for key in RAW_KEYS} | {"time_s", "vehicle_speed_m_s", "motor_speed_rpm", "motor_torque_Nm", "disc_speed_rad_s", "emot_total_reference_W", "gear_total_assumed_W", "disc_contact_W", "calibrated_winding_heat_W"}
    lim = cfg["thresholds_registered_before_execution"]
    for side in ["left", "right"]:
        q, m = sides[side], metas[side]
        need(required <= set(q), side + " missing source field")
        need(set(m["units"]) == set(q), side + " incomplete units")
        for key in q:
            need(m["units"][key] == m1_unit(key), side + " invalid input unit: " + key)
        need(m["mode"] == "engineering" and m["side"] == side and m["scenario_id"] == cfg["p1a_scenario_id"], "P1-A source identity")
        t = q["time_s"]
        need(t[0] == 0 and len(t) == 190 and np.all(np.isfinite(t)) and np.all(np.diff(t) > 0), "raw timeline")
        need(np.all(np.isnan(q["calibrated_winding_heat_W"])), "raw calibrated winding must stay NaN")
        need(np.all(q["motor_torque_Nm"] == 0), "raw regeneration torque not zero")
        for group, keys, total in [("motor", RAW_KEYS[:4], "emot_total_reference_W"), ("gear", RAW_KEYS[4:7], "gear_total_assumed_W"), ("brake", RAW_KEYS[7:], "disc_contact_W")]:
            near(sum(q[k + "_engineering_W"] for k in keys), q[total], lim["partition_tolerance_W"], "raw " + group + " partition")
        for key in ["actual_unpowered_motor_drag_W", "actual_inverter_standby_W", "actual_no_load_gear_churning_W"]:
            need(m[key] is None, "unmeasured loss filled")
    need(set(sides["left"]) == set(sides["right"]), "left/right fields differ")
    for name, a in sides["left"].items():
        b = sides["right"][name]
        need(a.shape == b.shape and np.array_equal(np.isnan(a), np.isnan(b)), "left/right shape or unknowns differ")
        use = np.isfinite(a)
        near(a[use], b[use], lim["kinematics_tolerance"], "left/right asymmetry: " + name)


def preflight(cfg):
    out, prepath = ROOT / cfg["output_directory"], ROOT / cfg["preflight_file"]
    need(git("branch", "--show-current") == cfg["required_branch"], "wrong branch")
    need(git("rev-parse", "HEAD") == cfg["p1a_commit"], "unexpected starting HEAD")
    need(not out.exists() and not prepath.exists(), "would overwrite existing P2-A evidence")
    parent = ROOT / cfg["input_directory"]
    for row in read_json(parent / "delivery_manifest.json")["files"]:
        need(sha(ROOT / row["path"]) == row["sha256"], "P1-A manifest mismatch")
    # Anchor the actual P1-A evidence to its delivered Git commit, not just to
    # editable local CSV/JSON manifests which could be changed together.
    for path in sorted(parent.iterdir()):
        if path.is_file():
            rel = path.relative_to(ROOT).as_posix()
            blob = subprocess.check_output(["git", "show", cfg["p1a_commit"] + ":" + rel], cwd=ROOT)
            need(hashlib.sha256(blob).hexdigest() == sha(path), "P1-A commit mismatch: " + rel)
    need(read_json(parent / "independent_checks.json")["status"] == "PASS_CONCEPT_SOURCE_AUDIT_ONLY", "P1-A not audited")
    run = read_json(parent / "run_metadata.json")
    need(run["scenario_id"] == cfg["p1a_scenario_id"] and run["options"]["regen_available"] == [False, False], "P1-A control identity")
    sides = {s: table(parent / (s + "_sources.csv")) for s in ["left", "right"]}
    metas = {s: read_json(parent / (s + "_sources.json")) for s in sides}
    check_raw(cfg, sides, metas)
    p = yaml.safe_load((ROOT / cfg["m2_configuration"]).read_text(encoding="utf-8"))
    need(read_json(ROOT / cfg["m2_prepared_inputs"])["configuration"] == p, "stale prepared M2 configuration")
    need(not git("diff", "M2-v1.0", "--name-only", "--", cfg["m2_configuration"], "scripts/m2", "results/m2"), "M2 archived content changed")
    need(all(v is None for v in p["unknown_actual"].values()), "M2 unknown calibration filled")
    need(p["numerics"]["maximum_step_s"] == cfg["expected_maximum_step_s"], "dt drift")
    need(p["numerics"]["energy_relative_tolerance"] == cfg["thresholds_registered_before_execution"]["source_resampling_relative_tolerance"], "energy tolerance drift")
    names = {CONFIG, "scripts/m4/prepare_no_regen_m2_forcing.m", "scripts/m4/check_no_regen_m2_forcing.py", cfg["m2_configuration"], cfg["m2_prepared_inputs"], "results/m2/compiled_network.json", "configs/m4_no_regen_brake_baseline.json"}
    names.update(x.relative_to(ROOT).as_posix() for x in parent.iterdir() if x.is_file())
    names.update(x.relative_to(ROOT).as_posix() for x in (ROOT / "scripts/m2").glob("*.m"))
    notices = {"docs/NO_REGEN_WORK_PLAN.md", "docs/M4_RUNBOOK.md", "docs/STAGE_VERSIONS.md"}
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    value = {"status": "PASS_INPUT_PREFLIGHT_ONLY", "registered_at": datetime.now().astimezone().isoformat(), "workspace_head": git("rev-parse", "HEAD"),
             "m2_code_commit": git("log", "-1", "--format=%H", "--", "scripts/m2"), "thresholds": cfg["thresholds_registered_before_execution"],
             "input_files": [{"path": n, "sha256": sha(ROOT / n)} for n in sorted(names)],
             "protected_files": [{"path": n, "sha256": sha(ROOT / n)} for n in tracked if n and n not in notices],
             "tag_refs": git("show-ref", "--tags"), "P1A_commit_verification": "PASS", "python": sys.version, "numpy": np.__version__}
    write_json(prepath, value)
    print(f"PASS preregistration: {len(names)} inputs, {len(value['protected_files'])} protected files, P1-A commit verified; no temperature calculation")


def overlap_average(t, values, starts, ends):
    # Different implementation from MATLAB's cumulative primitive: explicitly
    # integrate every clipped original sample interval, with no extrapolation.
    result = np.zeros((len(starts), values.shape[1]))
    slope = np.diff(values, axis=0) / np.diff(t)[:, None]
    for i, (start, end) in enumerate(zip(starts, ends)):
        lo, hi = np.maximum(t[:-1], start), np.minimum(t[1:], end)
        use = hi > lo
        p0 = values[:-1][use] + slope[use] * (lo[use] - t[:-1][use])[:, None]
        p1 = values[:-1][use] + slope[use] * (hi[use] - t[:-1][use])[:, None]
        result[i] = np.sum((p0 + p1) * ((hi - lo)[use] / 2)[:, None], axis=0) / (end - start)
    return result


def validate(cfg, p, raw, metas, forcing, meta, net, mapping, node):
    check_raw(cfg, raw, metas)
    lim = cfg["thresholds_registered_before_execution"]
    q = raw[cfg["side"]]; t = q["time_s"]
    need(cfg["part_keys"] == OUT_KEYS and cfg["side"] == "left", "source side/key order")
    columns = [k + "_engineering_W" for k in OUT_KEYS]
    expected_fields = {"start_s", "end_s", "speed_m_s", "motor_rpm", "motor_torque_Nm", "emot_reference_W", "gear_reference_W", "disc_contact_W", "segment_id", "calibrated_winding_heat_W"} | set(columns)
    need(set(forcing) == expected_fields, "missing/unexpected forcing field")
    need(set(meta["units"]) == expected_fields, "missing forcing units")
    for key in forcing:
        need(meta["units"][key] == forcing_unit(key), "invalid output unit: " + key)
    a, b = forcing["start_s"], forcing["end_s"]
    dt = p["numerics"]["maximum_step_s"]
    target = np.linspace(0, t[-1], int(np.ceil(t[-1] / dt)) + 1)
    need(a.shape == target[:-1].shape and np.all(b > a) and np.all(np.diff(a) > 0), "invalid interval time")
    near(a, target[:-1], lim["time_absolute_tolerance_s"], "target interval starts")
    near(b, target[1:], lim["time_absolute_tolerance_s"], "coverage/time step")
    need(np.all(b - a <= dt + lim["time_absolute_tolerance_s"]), "maximum step exceeded")
    need(np.all(forcing["segment_id"] == 1) and meta["segment_labels"] == ["single_brake"], "cross-segment interpolation or extra phase")
    near(np.asarray(meta["segment_boundaries_s"]).ravel(), np.array([0, t[-1]]), lim["time_absolute_tolerance_s"], "segment bounds")
    need(meta["scenario_id"] == cfg["scenario_id"] and meta["p1a_scenario_id"] == cfg["p1a_scenario_id"] and meta["p1a_commit"] == cfg["p1a_commit"], "scenario identity")
    need(meta["source_csv"] == cfg["input_directory"] + "/left_sources.csv" and meta["source_metadata"] == cfg["input_directory"] + "/left_sources.json", "source provenance paths")
    need(meta["configuration_version"] == cfg["configuration_version"] and meta["model_version"] == p["metadata"]["model_version"], "configuration/model version")
    need(meta["side"] == "left" and meta["single_side_multiplier"] == 1 and meta["disc_face_multiplier"] == 1, "duplicated side or faces")
    need(meta["mask_motor_gear_brake"] == [0, 0, 1] and mapping["mask_motor_gear_brake"] == [0, 0, 1], "wrong expected source mask")
    need(not meta["inverter_loaded_in_thermal_domain"] and not mapping["inverter_loaded_in_thermal_domain"], "inverter incorrectly internal")
    need(not any(meta[k] for k in ["temperature_integration_executed", "cooldown_added", "preheat_added", "repeated_cycles_added"]), "out-of-scope phase or temperature solve")
    need(meta["calibrated_winding_heat_W"] is None and np.all(np.isnan(forcing["calibrated_winding_heat_W"])), "calibrated winding not NaN/null")
    need(all(x is None for x in meta["unknowns"].values()), "unknown actual parameters filled")
    original_cols = [k + "_engineering_W" for k in RAW_KEYS] + ["vehicle_speed_m_s", "motor_speed_rpm", "motor_torque_Nm", "emot_total_reference_W", "gear_total_assumed_W", "disc_contact_W"]
    output_cols = columns + ["speed_m_s", "motor_rpm", "motor_torque_Nm", "emot_reference_W", "gear_reference_W", "disc_contact_W"]
    original = np.column_stack([q[k] for k in original_cols])
    actual = np.column_stack([forcing[k] for k in output_cols])
    need(np.all(original[:, :9] >= 0) and np.all(actual[:, :9] >= 0), "negative heat source")
    expected = overlap_average(t, original, a, b)
    source_columns = np.r_[0:9, 12:15]
    near(actual[:, source_columns], expected[:, source_columns], lim["independent_interval_tolerance_W"], "independent clipped-interval integral mismatch")
    near(actual[:, 9:12], expected[:, 9:12], lim["kinematics_tolerance"], "independent interval kinematics mismatch")
    original_energy = np.sum((original[1:] + original[:-1]) * np.diff(t)[:, None] / 2, axis=0)
    resampled_energy = np.sum(actual * (b - a)[:, None], axis=0)
    errors = resampled_energy - original_energy
    require_abs = np.max(np.abs(errors[np.r_[0:9, 12:15]]))
    require_rel = np.max(np.abs(errors[np.r_[0:9, 12:15]]) / np.maximum(1, np.abs(original_energy[np.r_[0:9, 12:15]])))
    need(require_abs <= lim["source_resampling_absolute_tolerance_J"] and require_rel <= lim["source_resampling_relative_tolerance"], "source energy not conserved")
    residuals = np.column_stack([actual[:, :4].sum(axis=1) - forcing["emot_reference_W"], actual[:, 4:7].sum(axis=1) - forcing["gear_reference_W"], actual[:, 7:9].sum(axis=1) - forcing["disc_contact_W"]])
    need(np.max(np.abs(residuals)) <= lim["partition_tolerance_W"], "resampled partitions not conserved")
    near(np.asarray(meta["raw_integral_J"]), original_energy[:9], lim["source_resampling_absolute_tolerance_J"], "raw integral metadata")
    need(net["ids"] == EXPECTED_IDS == [n["id"] for n in p["nodes"]], "13-node identity mismatch")
    near(np.asarray(net["C_J_K"]), np.array([n["mass_kg"] * n["cp_J_kgK"] for n in p["nodes"]]), 1e-10, "mass/cp heat capacity")
    need(np.all(np.asarray(net["C_J_K"]) > 0), "invalid capacity")
    # Compare every compiled coefficient with immutable M2-v1.0 evidence; also
    # independently check capacities and identifiers from the current YAML.
    archived = read_json(ROOT / "results/m2/compiled_network.json")
    need(set(net) == set(archived), "compiled network fields")
    for key in archived:
        if key in ["ids", "edge_names"]: need(net[key] == archived[key], "network names")
        else:
            tol = lim["network_radiation_absolute_tolerance_W_K4"] if key in ["Rad_W_K4", "AmbRad"] else lim["network_absolute_tolerance"]
            near(np.asarray(net[key]), np.asarray(archived[key]), tol, "compiled network coefficient: " + key, lim["network_relative_tolerance"])
    need(all(x is None for x in p["unknown_actual"].values()), "M2 unknown calibration filled")
    for triple in p["sensitivity"].values(): need(len(triple) == 3 and np.all(np.isfinite(triple)) and min(triple) > 0 and np.all(np.diff(triple) >= 0), "invalid M2 parameter range")
    vector = np.asarray(mapping["destination_index_MATLAB"])
    dest = [10, 9, 11, 0, 5, 4, 6, 1, 2]
    need(np.array_equal(vector, dest), "wrong source node mapping")
    need(mapping["part_keys"] == OUT_KEYS and mapping["destination_node_ids"] == cfg["source_destination_node_ids"], "source mapping labels")
    need(mapping["node_input_unit"] == "W" and mapping["schema"] == cfg["m2_model_version"], "mapping units/schema")
    for key, triple in p["sensitivity"].items(): need(mapping["values"][key] == triple[1], "non-nominal network override")
    need(set(node) == {"start_s", "end_s"} | {i + "_source_W" for i in EXPECTED_IDS}, "node source fields")
    Q = np.zeros((len(a), 13))
    for j, d in enumerate(dest):
        if d:
            use = [0, 0, 0, 1, 0, 0, 0, 1, 1][j]
            Q[:, d - 1] += actual[:, j] * use
    for j, name in enumerate(EXPECTED_IDS): near(node[name + "_source_W"], Q[:, j], lim["partition_tolerance_W"], "node source distribution")
    near(node["start_s"], a, lim["time_absolute_tolerance_s"], "node interval starts")
    near(node["end_s"], b, lim["time_absolute_tolerance_s"], "node interval ends")
    near(Q.sum(axis=1), forcing["disc_contact_W"], lim["partition_tolerance_W"], "single-side domain loading")
    return {"status": "PASS_INPUT_PREFLIGHT_ONLY_NO_TEMPERATURE_SOLUTION", "interval_count": len(a), "duration_s": float(t[-1]),
            "configured_maximum_step_s": dt, "actual_interval_s": float(b[0] - a[0]), "node_count": len(net["ids"]),
            "maximum_source_integral_difference_J": float(require_abs), "maximum_source_integral_difference_relative": float(require_rel),
            "maximum_interval_power_difference_W": float(np.max(np.abs(actual[:, source_columns] - expected[:, source_columns]))),
            "maximum_partition_residual_W": float(np.max(np.abs(residuals))),
            "disc_energy_J": float(resampled_energy[7]), "pad_energy_J": float(resampled_energy[8]),
            "single_side_contact_energy_J": float(resampled_energy[14]), "inverter_external_energy_J": float(resampled_energy[3]),
            "expected_mask_motor_gear_brake": [0, 0, 1], "single_side_multiplier": 1, "disc_face_multiplier": 1,
            "M2_shield_node_retained": True, "Case0_no_shield_equivalence_verified": False,
            "temperature_solve_executed": False}, list(zip(output_cols, original_energy.tolist(), resampled_energy.tolist(), errors.tolist()))


def audit(cfg):
    out = ROOT / cfg["output_directory"]; pre = read_json(ROOT / cfg["preflight_file"])
    verify_hashes(pre["input_files"] + pre["protected_files"])
    need(git("show-ref", "--tags") == pre["tag_refs"], "tag references changed")
    generated = read_json(out / "generated_files.json"); verify_hashes(generated["files"])
    rawdir = ROOT / cfg["input_directory"]
    raw = {s: table(rawdir / (s + "_sources.csv")) for s in ["left", "right"]}
    metas = {s: read_json(rawdir / (s + "_sources.json")) for s in raw}
    p = yaml.safe_load((ROOT / cfg["m2_configuration"]).read_text(encoding="utf-8"))
    ctx = dict(cfg=cfg, p=p, raw=raw, metas=metas, forcing=table(out / "single_brake_forcing.csv"), meta=read_json(out / "single_brake_forcing.json"),
               net=read_json(out / "compiled_network_input.json"), mapping=read_json(out / "source_mapping.json"), node=table(out / "node_source_input.csv"))
    m = ctx["meta"]
    need(m["input_files"] == pre["input_files"] and m["preflight_sha256"] == sha(ROOT / cfg["preflight_file"]), "input provenance metadata")
    need(m["forcing_csv_sha256"] == sha(out / "single_brake_forcing.csv"), "CSV/metadata hash pairing")
    need(m["workspace_head_before_run"] == cfg["p1a_commit"] and m["matlab_release"] == "2025a", "code/software version")
    need(m["m2_code_commit"] == pre["m2_code_commit"], "M2 code version missing or changed")
    result, energies = validate(**ctx)
    execution = read_json(out / "matlab_input_checks.json")
    need(execution["status"] == "PASS_INPUT_PREPARATION_ONLY" and execution["mat_file_readback"] == "PASS", "MAT input readback missing")
    need(not execution["forbidden_temperature_functions_called"] and not execution["temperature_results_created"], "scope violation")
    calls = execution["profiled_m2_functions"]
    need(all(not any(x in n for x in ["m2_simulate", "m2_flux", "run_m2", "m2_export"]) for n in calls), "solver/export call in profile")
    need("m2_load" in calls and "m2_network" in calls and "m2_forcing" in calls, "M2 interface not actually reused")
    tests = []
    names = ["missing_source_field", "invalid_input_unit", "invalid_output_unit", "double_sided_energy", "point_sampling_instead_of_integral", "filled_calibrated_winding", "wrong_source_mask", "inverter_to_winding", "wrong_time_coverage", "missing_network_node"]
    for name in names:
        bad = copy.deepcopy(ctx)
        if name == "missing_source_field": del bad["raw"]["left"]["copper_engineering_W"]
        elif name == "invalid_input_unit": bad["metas"]["left"]["units"]["disc_engineering_W"] = "kW"
        elif name == "invalid_output_unit": bad["meta"]["units"]["disc_engineering_W"] = "kW"
        elif name == "double_sided_energy":
            for key in ["disc_engineering_W", "pad_engineering_W", "disc_contact_W"]: bad["forcing"][key] *= 2
        elif name == "point_sampling_instead_of_integral":
            bad["forcing"]["disc_engineering_W"] = np.interp(bad["forcing"]["start_s"], raw["left"]["time_s"], raw["left"]["disc_engineering_W"])
        elif name == "filled_calibrated_winding": bad["forcing"]["calibrated_winding_heat_W"][0] = 0
        elif name == "wrong_source_mask": bad["meta"]["mask_motor_gear_brake"] = [1, 1, 1]
        elif name == "inverter_to_winding": bad["mapping"]["destination_index_MATLAB"][3] = 10
        elif name == "wrong_time_coverage": bad["forcing"]["end_s"][-1] += .1
        else: bad["net"]["ids"].pop()
        try: validate(**bad)
        except (Failure, KeyError) as error: tests.append({"test": name, "status": "PASS_EXPECTED_REJECTION", "reason": str(error)})
        else: raise Failure("checker accepted corruption: " + name)
    bad_hash = copy.deepcopy(pre["input_files"][:1]); bad_hash[0]["sha256"] = "0" * 64
    try: verify_hashes(bad_hash)
    except Failure as error: tests.append({"test": "changed_input_SHA256", "status": "PASS_EXPECTED_REJECTION", "reason": str(error)})
    else: raise Failure("checker accepted changed input hash")
    with (out / "source_integral_audit.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f); writer.writerow(["column", "raw_piecewise_linear_integral", "resampled_integral", "difference", "integral_unit"])
        for name, raw_e, sampled_e, error in energies:
            writer.writerow([name, raw_e, sampled_e, error, "J" if name.endswith("_W") else {"speed_m_s": "m", "motor_rpm": "rpm*s", "motor_torque_Nm": "N*m*s"}[name]])
    groups = ["P1A_commit_and_file_hashes", "raw_units_fields_and_symmetry", "time_step_and_full_single_segment_coverage", "independent_clipped_interval_averages", "source_and_budget_integral_conservation", "motor_gear_disc_partition_conservation", "single_side_and_surface_count", "calibrated_unknowns_and_external_inverter", "scenario_configuration_code_provenance", "13_node_network_and_parameters", "original_source_mapping_and_brake_mask", "MAT_input_readback_and_no_solver_profile"]
    result.update({"groups_passed": groups, "thresholds": cfg["thresholds_registered_before_execution"], "scenario_id": cfg["scenario_id"],
                   "p1a_commit": cfg["p1a_commit"], "input_and_output_hashes": "PASS", "protected_files_unchanged": len(pre["protected_files"]),
                   "tag_refs_unchanged": True, "failure_tests_passed": len(tests), "numpy": np.__version__, "python": sys.version,
                   "stage_status": "M4_PARTIAL_P2A_INPUT_ONLY_PENDING_REVIEW", "unmodelled_no_load_losses_are_physical_zero": False})
    write_json(out / "independent_preflight.json", result)
    write_json(out / "checker_regression_tests.json", {"status": "PASS", "tests": tests, "mutation_scope": "in-memory copies only; original files never edited"})
    paths = sorted(p for p in out.iterdir() if p.is_file() and p.name != "audit_files.json")
    write_json(out / "audit_files.json", {"files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]})
    print(json.dumps({k: result[k] for k in ["status", "interval_count", "actual_interval_s", "maximum_source_integral_difference_J", "maximum_partition_residual_W", "failure_tests_passed"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--preflight", action="store_true"); args = parser.parse_args()
    cfg = read_json(ROOT / CONFIG)
    try:
        preflight(cfg) if args.preflight else audit(cfg)
    except Exception as error:
        out = ROOT / cfg["output_directory"]
        if out.exists() and not args.preflight:
            write_json(out / "independent_preflight.json", {"status": "FAIL", "error": str(error), "type": type(error).__name__, "temperature_solve_executed": False})
        print(f"FAIL {type(error).__name__}: {error}", file=sys.stderr); raise SystemExit(1)


if __name__ == "__main__":
    main()
