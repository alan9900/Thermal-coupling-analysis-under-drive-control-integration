"""Create immutable, versioned inputs for the M1 MATLAB run; do not alter M0."""
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def main():
    base = yaml.safe_load((ROOT / "configs/baseline_vehicle.yaml").read_text(encoding="utf-8"))
    stage = yaml.safe_load((ROOT / "configs/m1_heat_sources.yaml").read_text(encoding="utf-8"))
    partition = yaml.safe_load((ROOT / "configs/m1_source_partition.yaml").read_text(encoding="utf-8"))
    assert base["metadata"]["version"] == "v0.4"
    assert base["drive"]["driven_axle"] == "rear" and not base["drive"]["differential_present"]
    assert base["drive"]["independent_motor_count"] == 2
    assert base["drive"]["rear_motor_per_side"]["motor_loss_map_file"] is None
    assert base["drive"]["rear_motor_per_side"]["continuous_mechanical_power_kw"] is None
    assert stage["metadata"]["baseline_commit"] == subprocess.check_output(
        ["git", "rev-parse", "M0-v1.0^{}"], cwd=ROOT, text=True).strip()
    input_files = ["configs/baseline_vehicle.yaml", "configs/m1_heat_sources.yaml",
                   "results/m0/epa_map_numeric.json", "results/m0/ornl_paired_drive_efficiency.csv",
                   "configs/m1_source_partition.yaml", "data/raw/m1/manifest.json"]
    hashes = {name: hashlib.sha256((ROOT / name).read_text(encoding="utf-8").encode("utf-8")).hexdigest() for name in input_files}
    payload = dict(vehicle_configuration=base, stage_configuration=stage, engineering_partition_configuration=partition,
                   provenance=dict(baseline_tag="M0-v1.0", baseline_commit=stage["metadata"]["baseline_commit"],
                                   code_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                                   input_sha256=hashes, hash_definition="UTF-8 text normalized to LF for portable Git checkout verification",
                                   source_classification="EPA combined fitted map; mirrored regeneration; S3 gearbox and partition",
                                   winding_heat_available=False, thermal_model_executed=False))
    out = ROOT / "results/m1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "inputs.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("M1 inputs prepared; original M0 outputs unchanged; physical unknowns preserved.")


if __name__ == "__main__":
    main()
