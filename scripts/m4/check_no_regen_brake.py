"""P1-A independent audit of saved M1-derived no-regeneration braking sources.

--preflight registers hashes and checks immutable M1 inputs before MATLAB runs.
Default mode reads CSV/JSON, recomputes dynamics/power/energy using independent
NumPy formulas, and fails closed. No MATLAB routines, solvers or downloads here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = "configs/m4_no_regen_brake_baseline.json"
PREFLIGHT = ROOT / "results/m4/no_regen_p1a_preflight.json"


class AuditFailure(RuntimeError):
    pass


def require(ok, label):
    if not bool(ok):
        raise AuditFailure(label)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def preflight():
    cfg = read_json(ROOT / CONFIG)
    require(git("branch", "--show-current") == cfg["required_branch"], "wrong branch")
    require(not (ROOT / cfg["output_directory"]).exists(), "output already exists; no overwrite allowed")
    require(not PREFLIGHT.exists(), "preflight already exists; do not overwrite provenance")
    p = read_json(ROOT / cfg["m1_prepared_inputs"])
    base = yaml.safe_load((ROOT / cfg["vehicle_configuration"]).read_text(encoding="utf-8"))
    stage = yaml.safe_load((ROOT / cfg["m1_configuration"]).read_text(encoding="utf-8"))
    partition = yaml.safe_load((ROOT / cfg["partition_configuration"]).read_text(encoding="utf-8"))
    require(base == p["vehicle_configuration"], "M1 prepared vehicle snapshot stale")
    require(stage == p["stage_configuration"], "M1 prepared stage snapshot stale")
    require(partition == p["engineering_partition_configuration"], "M1 partition snapshot stale")
    for name, expected in p["provenance"]["input_sha256"].items():
        normalized = (ROOT / name).read_text(encoding="utf-8").encode("utf-8")
        require(hashlib.sha256(normalized).hexdigest() == expected, f"stale M1 input: {name}")
    lim = cfg["thresholds_registered_before_execution"]
    require(lim["point_power_tolerance_W"] == stage["numerics"]["point_power_tolerance_W"], "power threshold drift")
    require(lim["energy_relative_tolerance"] == stage["numerics"]["energy_relative_tolerance"], "energy threshold drift")
    require(cfg["sampling"]["expected_configured_interval_s"] == stage["numerics"]["sample_interval_s"], "sample interval drift")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    # All old tracked content is protected, except planned current-stage notices.
    notices = {"docs/NO_REGEN_WORK_PLAN.md", "docs/STAGE_VERSIONS.md", "docs/M4_RUNBOOK.md"}
    protected = [{"path": s, "sha256": sha(ROOT / s)} for s in tracked if s and s not in notices]
    inputs = {CONFIG, cfg["m1_prepared_inputs"], cfg["vehicle_configuration"], cfg["m1_configuration"],
              cfg["partition_configuration"], "scripts/m4/prepare_no_regen_brake.m",
              "scripts/m4/check_no_regen_brake.py", "docs/M1_HEAT_SOURCE_INTERFACE.md"}
    inputs.update(p["provenance"]["input_sha256"])
    inputs.update(x.relative_to(ROOT).as_posix() for x in (ROOT / "scripts/m1").glob("*.m"))
    value = {"status": "PASS_PREFLIGHT_ONLY_NOT_A_SIMULATION", "registered_at": datetime.now().astimezone().isoformat(),
             "workspace_head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
             "m1_model_last_commit": git("log", "-1", "--format=%H", "--", "scripts/m1"),
             "thresholds": lim, "input_files": [{"path": x, "sha256": sha(ROOT / x)} for x in sorted(inputs)],
             "protected_files": protected, "tag_refs": git("show-ref", "--tags"),
             "hash_definition": "raw bytes SHA256; M1 legacy normalized-text hashes separately checked",
             "python": sys.version, "numpy": np.__version__, "pyyaml": yaml.__version__}
    write_json(PREFLIGHT, value)
    print(f"PASS preflight: {len(inputs)} inputs and {len(protected)} protected files; thresholds fixed before MATLAB")


def maximum(a):
    return float(np.max(np.abs(a))) if np.size(a) else 0.0


def near(actual, expected, tolerance, label):
    require(np.all(np.isfinite(actual)) and np.all(np.isfinite(expected)), label + ": nonfinite")
    require(maximum(actual - expected) <= tolerance, label)


def integral(y, t):
    return np.r_[0., np.cumsum((y[1:] + y[:-1]) * np.diff(t) / 2)]


def physics(cfg, base, stage, tr, sources, metas):
    lim = cfg["thresholds_registered_before_execution"]
    f_tol = lim["force_tolerance_N"]
    p_tol = lim["point_power_tolerance_W"]
    k_tol = lim["kinematics_absolute_tolerance"]
    s_tol = lim["source_partition_tolerance_W"]
    t, v = tr["time_s"], tr["speed_m_s"]
    b = base["vehicle"]
    m, g = b["mass_kg"], b["gravity_m_s2"]
    inertia, radius = b["rotational_inertia_factor"], b["wheel_effective_rolling_radius_m"]
    ratio = base["drive"]["rear_gearbox_per_side"]["reduction_motor_to_wheel"]
    a = cfg["deceleration_g"] * g
    u, w = cfg["initial_speed_kmh"] / 3.6, cfg["final_speed_kmh"] / 3.6
    duration = (u - w) / a
    dt = stage["numerics"]["sample_interval_s"]
    expected_t = np.linspace(0, duration, int(np.ceil(duration / dt)) + 1)
    require(t.shape == expected_t.shape and np.all(np.diff(t) > 0), "sampling shape/monotonicity")
    near(t, expected_t, k_tol, "sampling inherited from M1")
    near(v, u - a * t, k_tol, "speed trajectory and endpoints")
    near(tr["accel_m_s2"], np.full_like(t, -a), k_tol, "target acceleration")
    require(np.all(tr["trace_feasible"] == 1), "infeasible flag")
    groups = ["sampling_trajectory_and_feasibility"]
    rear_fraction = b["static_rear_axle_fraction"] - cfg["deceleration_g"] * b["cg_height_m"] / b["wheelbase_m"]
    n_rear = m * g * rear_fraction
    n_front = m * g - n_rear
    require(n_rear > 0 and n_front > 0, "axle lift")
    drag = .5 * stage["assumptions"]["air_density_kg_m3"] * b["drag_coefficient"] * b["frontal_area_m2"]
    rolling = m * g * b["rolling_resistance_coefficient"]
    road_force = rolling + drag * v**2
    brake_force = m * inertia * a - road_force
    require(np.all(brake_force > 0), "not a braking-only trajectory")
    front_force, rear_side_force = brake_force * (1 - rear_fraction), brake_force * rear_fraction / 2
    near(tr["front_normal_force_N"], np.full_like(t, n_front), f_tol, "front dynamic load")
    near(tr["front_friction_force_N"], front_force, f_tol, "front friction allocation")
    near(tr["front_axle_friction_power_W"], front_force * v, p_tol, "front axle power")
    near(tr["front_adhesion_utilization"], front_force / n_front, k_tol, "front adhesion utilization")
    require(np.all(front_force <= b["tire_road_mu"] * n_front + f_tol), "front adhesion exceeded")
    near(tr["road_power_W"], road_force * v, p_tol, "independent road power")
    for field in ["unmet_force_N", "unmet_power_W", "grade_power_W", "lr_kinematic_exchange_W", "auxiliary_power_W"]:
        near(tr[field], np.zeros_like(t), f_tol, "unexpected port: " + field)
    for side in ["left", "right"]:
        col = lambda name: tr[name + "_" + side]
        q = sources[side]
        near(col("rear_normal_force_N"), np.full_like(t, n_rear / 2), f_tol, side + " dynamic load")
        near(col("rear_friction_force_N"), rear_side_force, f_tol, side + " friction allocation")
        near(col("requested_rear_brake_force_N"), rear_side_force, f_tol, side + " requested brake force")
        near(col("rear_total_force_N"), rear_side_force, f_tol, side + " actual brake force")
        near(col("rear_adhesion_utilization"), rear_side_force / (n_rear / 2), k_tol, side + " adhesion utilization")
        require(np.all(rear_side_force <= b["tire_road_mu"] * n_rear / 2 + f_tol), side + " adhesion exceeded")
        for name in ["rear_regen_force_N", "motor_torque_Nm", "dc_power_each_W", "motor_mechanical_power_W", "regen_is_estimated"]:
            near(col(name), np.zeros_like(t), lim["zero_regen_absolute_tolerance"], "regeneration/nonzero port: " + name)
        near(col("wheel_omega_rad_s"), v / radius, k_tol, side + " wheel speed")
        near(col("disc_omega_rad_s"), v / radius, k_tol, side + " disc-wheel equality")
        near(col("motor_rpm"), v / radius * ratio * 60 / (2 * np.pi), k_tol, side + " motor ratio")
        require(np.all(col("motor_rpm") <= 13000), side + " EPA map speed bound")
        near(col("disc_friction_torque_Nm"), rear_side_force * radius, f_tol, side + " disc torque")
        near(col("disc_contact_power_W"), rear_side_force * v, p_tol, side + " force-speed contact power")
        near(col("disc_contact_power_W"), col("disc_friction_torque_Nm") * col("disc_omega_rad_s"), p_tol, side + " torque-speed contact power")
        require(np.all(np.isnan(col("winding_heat_W"))) and np.all(np.isnan(q["calibrated_winding_heat_W"])), "calibrated winding must remain unknown")
        for qname, trname in [("time_s", "time_s"), ("vehicle_speed_m_s", "speed_m_s")]:
            near(q[qname], tr[trname], k_tol, side + " source/trace " + qname)
        for qname, trname in [("motor_speed_rpm", "motor_rpm"), ("motor_torque_Nm", "motor_torque_Nm"),
                              ("disc_speed_rad_s", "disc_omega_rad_s"), ("emot_total_reference_W", "emot_combined_heat_W"),
                              ("gear_total_assumed_W", "gear_heat_assumed_W"), ("disc_contact_W", "disc_contact_power_W")]:
            near(q[qname], col(trname), k_tol, side + " source/trace " + qname)
        sets = [("emot", ["copper", "iron", "rotor_other", "inverter"], "emot_total_reference_W"),
                ("gear", ["gear_mesh", "gear_bearing", "gear_other"], "gear_total_assumed_W"),
                ("disc", ["disc", "pad"], "disc_contact_W")]
        for group, parts, total in sets:
            value = sum(q[key + "_engineering_W"] for key in parts)
            near(value, q[total], s_tol, side + " " + group + " partition conservation")
            near(q[group + "_partition_residual_W"], value - q[total], s_tol, "stored partition residual")
        beta = stage["assumptions"]["disc_contact_heat_fraction"]
        near(q["disc_engineering_W"], beta * rear_side_force * v, s_tol, side + " nominal disc partition")
        near(q["pad_engineering_W"], (1 - beta) * rear_side_force * v, s_tol, side + " nominal pad partition")
        near(q["disc_engineering_W"], col("disc_deposited_heat_assumed_W"), s_tol, side + " disc trace match")
        near(q["pad_engineering_W"], col("pad_deposited_heat_assumed_W"), s_tol, side + " pad trace match")
        for key in ["copper", "iron", "rotor_other", "inverter", "gear_mesh", "gear_bearing", "gear_other", "disc", "pad"]:
            nominal, lower, upper = [q[key + suffix] for suffix in ["_engineering_W", "_lower_W", "_upper_W"]]
            require(np.all(np.isfinite([nominal, lower, upper])), side + " nonfinite allocation")
            require(np.all(lower >= -s_tol) and np.all(nominal >= lower - s_tol) and np.all(nominal <= upper + s_tol), side + " invalid conditional enclosure")
        # Independent sum uses component loads once, never total + components.
        load = sum(q[key + "_engineering_W"] for key in ["copper", "iron", "rotor_other", "inverter", "gear_mesh", "gear_bearing", "gear_other", "disc", "pad"])
        near(load, col("emot_combined_heat_W") + col("gear_heat_assumed_W") + col("disc_contact_power_W"), s_tol, side + " no duplicate budget")
        require(np.all(q["source_class_code"] == 3), side + " source classification")
        meta = metas[side]
        require(meta["mode"] == "engineering" and meta["side"] == side and meta["scenario_id"] == cfg["scenario_id"], side + " metadata identity")
        require(meta["single_side_only_not_two_rear_sides"] and meta["single_disc_and_pad_pair_both_faces_combined"], "single-side/faces definition")
        require(meta["inverter_thermal_destination"] == "external_boundary_not_motor_internal", "inverter destination")
        for key in ["actual_unpowered_motor_drag_W", "actual_inverter_standby_W", "actual_no_load_gear_churning_W"]:
            require(meta[key] is None, "unknown physical loss was filled: " + key)
        require(not meta["no_load_gear_drag_included"] and not meta["temperature_feedback_executed"], "omission disclosure")
        require(set(meta["units"]) == set(q.dtype.names), "missing source units")
    near(tr["dc_power_total_W"], np.zeros_like(t), 0, "battery recovery must be exactly zero")
    near(tr["battery_charge_effective_cap_W"], np.zeros_like(t), 0, "regen enable/cap")
    actual_a = -(tr["front_friction_force_N"] + tr["rear_friction_force_N_left"] + tr["rear_friction_force_N_right"] + road_force) / (m * inertia)
    near(actual_a, np.full_like(t, -a), k_tol, "independently achieved target deceleration")
    groups.extend(["disabled_regen_all_ports", "dynamic_axle_loads_and_adhesion", "front_and_two_rear_force_allocation",
                   "disc_wheel_motor_kinematics", "single_disc_force_torque_power", "source_trace_interface",
                   "motor_gear_disc_partition_and_no_double_loading", "conditional_bounds_and_units", "calibrated_unknowns_and_omission_metadata"])
    for name in tr.dtype.names:
        if name.endswith("_left"):
            other = name[:-5] + "_right"
            require(np.array_equal(np.isnan(tr[name]), np.isnan(tr[other])), "left/right NaN symmetry")
            mask = np.isfinite(tr[name])
            near(tr[name][mask], tr[other][mask], lim["symmetry_absolute_tolerance"], "left/right trace symmetry: " + name)
    for name in sources["left"].dtype.names:
        x, y = sources["left"][name], sources["right"][name]
        require(np.array_equal(np.isnan(x), np.isnan(y)), "left/right source NaN symmetry")
        near(x[np.isfinite(x)], y[np.isfinite(y)], lim["symmetry_absolute_tolerance"], "left/right source symmetry: " + name) if np.any(np.isfinite(x)) else None
    groups.append("left_right_symmetry")
    totals = tr["front_axle_friction_power_W"] + road_force * v
    for side in ["left", "right"]:
        for name in ["disc_contact_power_W", "gear_heat_assumed_W", "emot_combined_heat_W"]:
            totals = totals + tr[name + "_" + side]
    residual = tr["dc_power_total_W"] + tr["unmet_power_W"] - (m * inertia * (-a) * v + totals)
    near(residual, np.zeros_like(t), p_tol, "independent point power residual")
    near(tr["power_residual_W"], residual, p_tol, "stored vehicle power residual")
    for side in ["left", "right"]:
        near(sources[side]["vehicle_power_residual_W"], residual, p_tol, side + " interface residual")
    kinetic_drop = .5 * m * inertia * (u**2 - v**2)
    cumulative_dissipation = integral(totals, t)
    energy_residual = kinetic_drop + integral(tr["dc_power_total_W"] + tr["unmet_power_W"], t) - cumulative_dissipation
    energy_scale = max(1., .5 * m * inertia * (u**2 - w**2))
    max_energy_relative = maximum(energy_residual) / energy_scale
    require(max_energy_relative <= lim["energy_relative_tolerance"], "cumulative whole-vehicle energy residual")
    analytic_road = rolling * (u**2 - w**2) / (2 * a) + drag * (u**4 - w**4) / (4 * a)
    integrated_road = integral(road_force * v, t)[-1]
    analytic_relative = abs(integrated_road - analytic_road) / energy_scale
    require(analytic_relative <= lim["energy_relative_tolerance"], "independent analytic road-energy quadrature check")
    groups.extend(["independent_point_power_balance", "cumulative_vehicle_energy_balance", "closed_form_road_energy_cross_check"])
    history = {"time_s": t, "kinetic_energy_removed_J": kinetic_drop,
               "front_friction_energy_J": integral(tr["front_axle_friction_power_W"], t),
               "road_dissipation_energy_J": integral(road_force * v, t),
               "battery_net_energy_J": integral(tr["dc_power_total_W"], t),
               "independent_power_residual_W": residual, "cumulative_vehicle_energy_residual_J": energy_residual}
    side_energies = {}
    for side in ["left", "right"]:
        q = sources[side]
        history[side + "_friction_energy_J"] = integral(q["disc_contact_W"], t)
        side_energies[side] = {key + "_J": float(integral(q[key + "_engineering_W"], t)[-1]) for key in
                             ["copper", "iron", "rotor_other", "inverter", "gear_mesh", "gear_bearing", "gear_other", "disc", "pad"]}
        history[side + "_disc_deposited_energy_J"] = integral(q["disc_engineering_W"], t)
        history[side + "_pad_deposited_energy_J"] = integral(q["pad_engineering_W"], t)
    return {"status": "PASS_CONCEPT_SOURCE_AUDIT_ONLY", "groups_passed": groups,
            "samples": len(t), "duration_s": duration, "configured_dt_s": dt, "actual_dt_s": float(t[1] - t[0]),
            "rear_dynamic_fraction": rear_fraction, "front_normal_force_N": n_front, "rear_normal_force_total_N": n_rear,
            "initial_disc_torque_each_Nm": float(tr["disc_friction_torque_Nm_left"][0]),
            "peak_disc_torque_each_Nm": float(np.max(tr["disc_friction_torque_Nm_left"])),
            "initial_disc_contact_power_each_W": float(sources["left"]["disc_contact_W"][0]),
            "max_front_adhesion_utilization": float(np.max(front_force / n_front)),
            "max_rear_adhesion_utilization": float(np.max(rear_side_force / (n_rear / 2))),
            "max_motor_speed_rpm": float(np.max(tr["motor_rpm_left"])),
            "max_independent_power_residual_W": maximum(residual),
            "max_cumulative_energy_residual_J": maximum(energy_residual),
            "max_cumulative_energy_residual_relative": max_energy_relative,
            "final_cumulative_energy_residual_J": float(energy_residual[-1]),
            "kinetic_energy_removed_J": energy_scale, "front_friction_energy_J": float(history["front_friction_energy_J"][-1]),
            "rear_contact_energy_each_J": float(history["left_friction_energy_J"][-1]),
            "road_energy_J": float(integrated_road), "analytic_road_energy_J": analytic_road,
            "analytic_road_quadrature_relative_to_vehicle_KE": analytic_relative,
            "side_component_energy_J": side_energies,
            "feasibility_scope": "Prescribed longitudinal dynamics and assumed tire adhesion only; brake torque capacity and hardware safety remain unverified"}, history


def audit():
    cfg = read_json(ROOT / CONFIG)
    out = ROOT / cfg["output_directory"]
    pre = read_json(PREFLIGHT)
    for row in pre["input_files"] + pre["protected_files"]:
        require(sha(ROOT / row["path"]) == row["sha256"], "changed input/protected file: " + row["path"])
    require(git("show-ref", "--tags") == pre["tag_refs"], "tag references changed")
    generated = read_json(out / "generated_files.json")
    for row in generated["files"]:
        p = ROOT / row["path"]
        require(p.stat().st_size == row["bytes"] and sha(p) == row["sha256"], "generated output hash: " + row["path"])
    load = lambda p: np.genfromtxt(p, delimiter=",", names=True, encoding="utf-8-sig")
    tr = load(out / "vehicle_trace.csv")
    sources = {side: load(out / f"{side}_sources.csv") for side in ["left", "right"]}
    metas = {side: read_json(out / f"{side}_sources.json") for side in sources}
    run = read_json(out / "run_metadata.json")
    require(run["matlab_release"] == "2025a", "MATLAB release")
    require(run["scenario"] == cfg, "run scenario snapshot mismatch")
    require(run["preflight_sha256"] == sha(PREFLIGHT), "preflight receipt changed")
    require(not any(run[key] for key in ["temperature_solver_executed", "ANSYS_executed", "Fluent_executed", "preheat_executed", "cooldown_executed"]), "out-of-scope execution flags")
    base = yaml.safe_load((ROOT / cfg["vehicle_configuration"]).read_text(encoding="utf-8"))
    stage = yaml.safe_load((ROOT / cfg["m1_configuration"]).read_text(encoding="utf-8"))
    require(run["vehicle_configuration"] == base and run["m1_configuration"] == stage, "M1/vehicle snapshot mismatch")
    require(base["drive"]["rear_motor_per_side"]["motor_loss_map_file"] is None, "calibration map filled")
    require(base["brakes"]["rear_rotor_per_side"]["pad_disc_heat_partition"] is None, "calibrated partition filled")
    require(run["options"]["regen_available"] == [False, False] and run["options"]["battery_charge_cap_total_kW"] == 0, "regen control flags")
    for side, meta in metas.items():
        require(meta["csv_sha256"] == sha(out / f"{side}_sources.csv"), "source csv pairing")
        require(meta["trace_sha256"] == sha(out / "vehicle_trace.csv"), "source trace pairing")
        require(meta["source_config_sha256"] == sha(ROOT / CONFIG), "source config pairing")
        require(meta["input_files"] == pre["input_files"], "source provenance mismatch")
    result, history = physics(cfg, base, stage, tr, sources, metas)
    summary = read_json(out / "matlab_summary.json")
    require(summary["trace_feasible"] and summary["case_id"] == cfg["scenario_id"], "MATLAB summary feasibility")
    for key, value in [("left_disc_contact_energy_kJ", result["rear_contact_energy_each_J"] / 1000),
                       ("right_disc_contact_energy_kJ", result["rear_contact_energy_each_J"] / 1000),
                       ("front_axle_friction_energy_kJ", result["front_friction_energy_J"] / 1000),
                       ("road_energy_kJ", result["road_energy_J"] / 1000)]:
        require(abs(summary[key] - value) < 1e-7, "MATLAB summary cross-check: " + key)
    # Fault injection changes in-memory copies only. Never edits real CSVs.
    regressions = []
    for name in ["nonzero_regen", "double_disc_heat", "fake_calibrated_winding", "infeasible_trace", "wrong_motor_ratio"]:
        bad_tr = tr.copy(); bad_src = {s: q.copy() for s, q in sources.items()}
        if name == "nonzero_regen": bad_tr["rear_regen_force_N_left"][0] = 1
        elif name == "double_disc_heat": bad_src["left"]["disc_engineering_W"][0] *= 2
        elif name == "fake_calibrated_winding": bad_src["left"]["calibrated_winding_heat_W"][0] = 0
        elif name == "infeasible_trace": bad_tr["trace_feasible"][0] = 0
        else: bad_tr["motor_rpm_left"][0] *= 2
        try:
            physics(cfg, base, stage, bad_tr, bad_src, metas)
        except AuditFailure as e:
            regressions.append({"test": name, "status": "PASS_EXPECTED_REJECTION", "reason": str(e)})
        else:
            raise AuditFailure("checker failed to reject corruption: " + name)
    with (out / "independent_energy_history.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f); writer.writerow(history)
        writer.writerows(zip(*history.values()))
    result.update({"scenario_id": cfg["scenario_id"], "thresholds": cfg["thresholds_registered_before_execution"],
                   "audit_method": "Independent Python/NumPy equations, trapezoidal cumulative quadrature and closed-form road work; saved MATLAB summary only cross-checked afterward",
                   "input_and_generated_hash_checks": "PASS", "protected_file_count": len(pre["protected_files"]),
                   "protected_files_unchanged": True, "tags_unchanged": True,
                   "matlab_summary_cross_check": "PASS", "python": sys.version, "numpy": np.__version__,
                   "matlab_release": run["matlab_release"], "m1_model_last_commit": pre["m1_model_last_commit"],
                   "source_base_commit": pre["workspace_head"], "preflight_sha256": sha(PREFLIGHT),
                   "stage_status": "M4_PARTIAL_P1A_ONLY_PENDING_RESEARCHER_REVIEW",
                   "motor_and_gear_zero_budget_is_measured": False, "temperature_prediction_executed": False})
    write_json(out / "independent_checks.json", result)
    write_json(out / "checker_regression_tests.json", {"status": "PASS", "tests": regressions, "real_output_files_modified": False})
    paths = sorted(p for p in out.iterdir() if p.is_file() and p.name != "audit_files.json")
    write_json(out / "audit_files.json", {"files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]})
    print(json.dumps({"status": result["status"], "audit_groups": len(result["groups_passed"]), "corruption_rejections": len(regressions),
                      "max_power_residual_W": result["max_independent_power_residual_W"],
                      "max_energy_residual_J": result["max_cumulative_energy_residual_J"],
                      "max_energy_residual_relative": result["max_cumulative_energy_residual_relative"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        preflight() if args.preflight else audit()
    except Exception as e:
        cfg = read_json(ROOT / CONFIG)
        out = ROOT / cfg["output_directory"]
        # A failure receipt must supersede any previous PASS, without changing
        # original generation data. Re-running a failed audit never hides failure.
        if out.exists() and not args.preflight:
            write_json(out / "independent_checks.json", {"status": "FAIL", "error": str(e), "type": type(e).__name__, "stage_status": "M4_PARTIAL"})
        print(f"FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
