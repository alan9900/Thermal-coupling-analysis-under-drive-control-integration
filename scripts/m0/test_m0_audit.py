"""Negative configuration tests: stale architecture must fail closed."""
import copy
import unittest
import yaml
from prepare_audit import ROOT, validate_config


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.config = yaml.safe_load((ROOT / "configs/baseline_vehicle.yaml").read_text(encoding="utf-8"))

    def test_valid_current_configuration(self):
        validate_config(self.config)

    def test_reject_stale_architecture_and_nonphysical_values(self):
        invalid = [
            ("metadata", "version", "v0.3"), ("drive", "driven_axle", "front"),
            ("drive", "independent_motor_count", 1), ("drive", "differential_present", True),
            ("vehicle", "mass_kg", -1800), ("vehicle", "wheelbase_m", 0),
            ("vehicle", "wheel_effective_rolling_radius_m", 0),
            ("vehicle", "static_rear_axle_fraction", 1.1),
            ("brakes", "rotor_speed_to_own_wheel_speed_ratio", 9),
            ("brakes", "front_conventional_service_brakes_retained", False),
        ]
        for group, key, value in invalid:
            with self.subTest(group=group, key=key):
                c=copy.deepcopy(self.config); c[group][key]=value
                with self.assertRaises(AssertionError):
                    validate_config(c)

    def test_missing_geometry_and_losses_remain_unknown(self):
        motor=self.config["drive"]["rear_motor_per_side"]
        for key in ["motor_loss_map_file", "inverter_loss_map_file", "continuous_mechanical_power_kw", "configured_regen_torque_limit_nm"]:
            self.assertIsNone(motor[key])


if __name__ == "__main__":
    unittest.main(verbosity=2)
