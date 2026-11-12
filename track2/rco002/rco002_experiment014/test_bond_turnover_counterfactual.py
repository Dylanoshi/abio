#!/usr/bin/env python3
"""E014 Phase 9 tests: checkpoint matching and parameter validation."""
import unittest
from pathlib import Path
from short_horizon import load_sim
from bond_turnover_counterfactual import replay

HERE=Path(__file__).resolve().parent

class BondTurnoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e014_sim.py")
        cls.settings={
            "size":8,"steps":26,"initial_density":.35,
            "decay":.008,"supply":.018,"bond_form":.075,
            "bond_break":.018,"rule_density":.85,
            "catalysis_rate":.14,"background_rate":.0015,
            "interrupt_fraction":.5,"min_target_size":2,
            "activity_window":5
        }

    def test_invalid_rate(self):
        with self.assertRaises(ValueError):
            replay(self.sim,self.settings,seed=3,checkpoint=20,end=23,rates=[-0.1])

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            replay(self.sim,self.settings,seed=3,checkpoint=10,end=23)

    def test_identical_treatment_at_baseline_rate(self):
        # For a small test substrate, target selection is not guaranteed;
        # find a deterministic eligible seed and assert matched treatment paths.
        for seed in range(16):
            try:
                result=replay(self.sim,self.settings,seed=seed,
                              checkpoint=20,end=23,rates=[.018])
            except ValueError as exc:
                if "No target" in str(exc) or "no bonded" in str(exc):
                    continue
                raise
            a=result["branches"]["pulse_0.0180"]
            b=result["branches"]["sustained_0.0180"]
            self.assertEqual(a["rows"],b["rows"])
            self.assertEqual(a["first_target_absent_after_checkpoint"],
                             b["first_target_absent_after_checkpoint"])
            return
        self.skipTest("No eligible functional target in tiny deterministic fixture")

if __name__=="__main__":
    unittest.main()
