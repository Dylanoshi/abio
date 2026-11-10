#!/usr/bin/env python3
"""Small smoke tests for E014 short-horizon branching."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from short_horizon import load_sim, run


class ShortHorizonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = load_sim(HERE.parent / "rco002_experiment011" / "sim.py")
        cls.settings = {
            "size": 8, "steps": 20, "initial_density": 0.35,
            "decay": 0.008, "supply": 0.018,
            "bond_form": 0.075, "bond_break": 0.018,
            "rule_density": 0.85, "catalysis_rate": 0.14,
            "background_rate": 0.0015, "interrupt_fraction": 0.5,
            "min_target_size": 3, "activity_window": 5,
        }

    def test_matched_reconstruction_is_repeatable(self):
        first = run(self.sim, self.settings, seed=3, event_start=16, horizon=3)
        again = run(self.sim, self.settings, seed=3, event_start=16, horizon=3)
        self.assertEqual(first, again)
        self.assertEqual(first["original_branch_step"], 10)
        self.assertEqual(len(first["branches"]), 4)
        self.assertEqual(len(first["branches"]["sham"]["rows"]), 3)
        self.assertEqual(first["historical_sham_reproduced"], None)
        self.assertFalse(first["scientific_conclusion"]["verified_self_maintenance"])

    def test_reject_prebranch_event(self):
        with self.assertRaises(ValueError):
            run(self.sim, self.settings, seed=0, event_start=10, horizon=1)

    def test_reject_horizon_overflow(self):
        with self.assertRaises(ValueError):
            run(self.sim, self.settings, seed=0, event_start=18, horizon=4)


if __name__ == "__main__":
    unittest.main()
