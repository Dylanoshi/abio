#!/usr/bin/env python3
"""Tests of E014 mechanistic trace against small reproducible E011 dynamics."""
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from mechanism_trace import trace
from short_horizon import load_sim


class TraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE.parent/"rco002_experiment011"/"sim.py")
        cls.settings={
            "size":8,"steps":20,"initial_density":.35,
            "decay":.008,"supply":.018,"bond_form":.075,
            "bond_break":.018,"rule_density":.85,
            "catalysis_rate":.14,"background_rate":.0015,
            "interrupt_fraction":.5,"min_target_size":3,
            "activity_window":5,
        }

    def test_determinism_and_branch_alignment(self):
        first=trace(self.sim,self.settings,3,16,18)
        second=trace(self.sim,self.settings,3,16,18)
        self.assertEqual(first,second)
        self.assertEqual(len(first["branches"]),4)
        self.assertEqual(len(first["branches"]["sham"]["rows"]),3)
        self.assertEqual(first["provenance"]["original_branch_step"],10)
        self.assertFalse(first["interpretation"]["verified_self_maintenance"])
        self.assertIn("suppressed_events",first["comparisons"]["target_block"])

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            trace(self.sim,self.settings,0,10,14)


if __name__=="__main__":
    unittest.main()
