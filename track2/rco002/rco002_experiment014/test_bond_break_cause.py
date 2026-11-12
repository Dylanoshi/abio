#!/usr/bin/env python3
"""Regression: bond tracing must be observational and deterministic."""
import argparse
import copy
import unittest
from pathlib import Path

from short_horizon import load_sim, physical_hash
from bond_break_cause import analyze_step_543

HERE=Path(__file__).resolve().parent

class BondCauseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e014_sim.py")
        cls.original=load_sim(HERE.parent/"rco002_experiment011"/"sim.py")
        cls.settings=argparse.Namespace(
            size=8, steps=600, initial_density=.35, decay=.008,
            supply=.018, bond_form=.075, bond_break=.018,
            rule_density=.85, catalysis_rate=.14,
            background_rate=.0015, interrupt_fraction=.6,
            min_target_size=3, activity_window=5
        )

    def test_instrument_does_not_change_physical_dynamics(self):
        a=self.settings
        left=self.sim.initialize(7,a)
        right=self.original.initialize(7,a)
        for t in range(1,16):
            if t==15:
                left["e014_trace_bonds"]=[]
                left["e014_trace_step"]=t
            self.sim.tick(left,7,"common",t,a,[],[])
            self.original.tick(right,7,"common",t,a,[],[])
            self.assertEqual(physical_hash(left),physical_hash(right))
            if t==15:
                for event in left["e014_trace_bonds"]:
                    self.assertEqual(event["broken"],event["draw"]<a.bond_break)

    def test_missing_target_is_handled(self):
        s=self.sim.initialize(7,self.settings)
        # No target is selected; function must safely handle no target edges.
        self.assertEqual(analyze_step_543(self.sim,s,7,"common",self.settings)["pre_step_target_edges"],[])

if __name__=="__main__":
    unittest.main()
