"""Independent CSV/energy checks and source-evidence receipt for M1."""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/m1"


def load_csv(path):
    return np.genfromtxt(path, delimiter=",", names=True, encoding="utf-8")


def main():
    validation = json.loads((OUT / "validation.json").read_text())
    assert validation["status"] == "PASS" and validation["case_count"] == 23
    tests = json.loads((OUT / "tests.json").read_text())
    checked = []
    max_energy = 0.0
    for path in sorted((OUT / "traces").glob("*.csv")):
        tr = load_csv(path)
        t = tr["time_s"]
        assert len(t) > 2 and np.all(np.diff(t) > 0)
        assert np.all(np.isfinite(tr["speed_m_s"])) and np.all(tr["trace_feasible"] == 1)
        for side in ["left", "right"]:
            def col(name):
                return tr[name + "_" + side]
            assert np.allclose(col("motor_rpm")*2*np.pi/60, 9*col("wheel_omega_rad_s"), atol=1e-8)
            assert np.array_equal(col("disc_omega_rad_s"), col("wheel_omega_rad_s"))
            assert np.all(col("disc_contact_power_W") >= -1e-8)
            assert np.all(col("gear_heat_assumed_W") >= -1e-8)
            assert np.all(col("emot_combined_heat_W") >= 0)
            assert np.all(np.isnan(col("winding_heat_W")))
            assert np.allclose(col("disc_deposited_heat_assumed_W")+col("pad_deposited_heat_assumed_W"), col("disc_contact_power_W"), atol=1e-7)
            split = np.nan_to_num(col("motor_total_heat_estimated_W")) + np.nan_to_num(col("inverter_heat_estimated_W")) + col("unallocated_emot_heat_W")
            assert np.allclose(split, col("emot_combined_heat_W"), atol=1e-7)
            assert np.all(col("rear_adhesion_utilization") <= .8+1e-10)
        assert np.allclose(tr["dc_power_total_W"], tr["dc_power_each_W_left"]+tr["dc_power_each_W_right"]+tr["auxiliary_power_W"], atol=1e-7)
        assert np.all(-tr["dc_power_total_W"] <= tr["battery_charge_effective_cap_W"]+1e-4)
        assert np.all(tr["front_adhesion_utilization"] <= .8+1e-10)
        # Integrate terminal power ports independently from the MATLAB summary.
        dK=.5*1800*(tr["speed_m_s"][-1]**2-tr["speed_m_s"][0]**2)
        diss = tr["front_axle_friction_power_W"] + tr["road_power_W"] + tr["grade_power_W"] + tr["lr_kinematic_exchange_W"] + tr["auxiliary_power_W"]
        for side in ["left", "right"]:
            for name in ["disc_contact_power_W", "gear_heat_assumed_W", "emot_combined_heat_W"]:
                diss = diss + tr[name+"_"+side]
        residual=np.trapezoid(tr["dc_power_total_W"]+tr["unmet_power_W"]-diss,t)-dK
        relative=abs(residual)/max(1,abs(dK)); max_energy=max(max_energy,relative)
        assert relative<1e-6
        checked.append(dict(case=path.stem, rows=len(t), independent_energy_residual_relative=relative))
    assert len(checked)==23
    nominal=load_csv(OUT / "traces/stop_z06_bat00_road0.csv")
    independent_disc=np.trapezoid(nominal["disc_contact_power_W_left"],nominal["time_s"])
    expected=.5*1800*(100/3.6)**2*(.55-.6*.55/2.765)/2
    assert abs(independent_disc-expected)<1e-6
    inputs=json.loads((OUT / "inputs.json").read_text(encoding="utf-8"))
    for name,sha in inputs["provenance"]["input_sha256"].items():
        assert hashlib.sha256((ROOT/name).read_text(encoding="utf-8").encode("utf-8")).hexdigest()==sha
    model_files=sorted((ROOT/"scripts/m1").glob("*.m"))
    code_hashes={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest() for p in model_files}
    code_commit=subprocess.check_output(["git","log","-1","--format=%H","--","scripts/m1/*.m"],cwd=ROOT,text=True).strip()
    result=dict(status="PASS", stage_status="PARTIAL", matlab_test_groups=tests["test_group_count"],
                independent_python_cases=checked, maximum_independent_energy_residual_relative=max_energy,
                model_implementation_commit=code_commit, matlab_source_sha256=code_hashes,
                original_baseline="M0-v1.0", M0_commit=inputs["provenance"]["baseline_commit"],
                winding_heat_is_unknown_in_all_traces=True, M1_approved=False, M1_tag_created=False, M2_started=False)
    (OUT/"independent_checks.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Independent checks PASS:",len(checked),"traces; energy residual",max_energy)


if __name__=="__main__":
    main()
