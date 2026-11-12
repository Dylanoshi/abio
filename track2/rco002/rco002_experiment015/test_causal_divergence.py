#!/usr/bin/env python3
"""Regression tests for timed sham-derived control and Phase 6 causal audit."""
import argparse
import copy
import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import DEFAULTS
from ablation import load_sim,physical_signature
from dynamic_source_ablation import MaterialBridge
from source_ablation import choose_focal
from causal_divergence import execute

class CausalDivergenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e015_sim.py")
        cls.params=dict(DEFAULTS,size=12,steps=100,rule_density=1.0,
                        catalysis_rate=.9,initial_density=.5,supply=.1)
        cls.a=argparse.Namespace(**cls.params)

    def checkpoint(self,seed=0):
        s=self.sim.initialize(seed,self.a)
        for t in range(1,51):
            self.sim.tick(s,seed,"local",t,self.a,[],[])
        return s,choose_focal(s,50)[0]

    def test_zero_budget_exact_sham_physics(self):
        s,focal=self.checkpoint()
        normal=copy.deepcopy(s)
        control=copy.deepcopy(s)
        normal["e015_audit_hook"]=MaterialBridge(focal)
        control["e015_audit_hook"]=MaterialBridge(focal)
        normal["e015_deposition_policy"]="all"
        control["e015_deposition_policy"]="offtarget_step_budget"
        control["e015_offtarget_step_budget"]={}
        for t in range(51,60):
            self.sim.tick(normal,0,"local",t,self.a,[],[])
            self.sim.tick(control,0,"local",t,self.a,[],[])
            self.assertEqual(physical_signature(normal),physical_signature(control))

    def test_large_budget_only_suppresses_nonfocal_deposits(self):
        s,focal=self.checkpoint()
        normal=copy.deepcopy(s)
        ctrl=copy.deepcopy(s)
        normal["e015_audit_hook"]=MaterialBridge(focal)
        ctrl["e015_audit_hook"]=MaterialBridge(focal)
        ctrl["e015_deposition_policy"]="offtarget_step_budget"
        ctrl["e015_offtarget_step_budget"]={51:100000}
        self.sim.tick(normal,0,"local",51,self.a,[],[])
        self.sim.tick(ctrl,0,"local",51,self.a,[],[])
        self.assertEqual(normal["cells"],ctrl["cells"])
        self.assertEqual(normal["bonds"],ctrl["bonds"])
        self.assertEqual(normal["ids"],ctrl["ids"])
        self.assertEqual(normal["catalytic_births"],ctrl["catalytic_births"])
        self.assertEqual(ctrl["e015_audit_hook"].suppressed["focal"],0)
        self.assertEqual(ctrl["e015_audit_hook"].deposits["nonfocal"],0)
        self.assertEqual(ctrl["e015_audit_hook"].suppressed["nonfocal"],
                         ctrl["e015_audit_hook"].births["nonfocal"])

    def test_small_smoke_matches_planned_count_where_possible(self):
        out=execute(self.sim,self.params,[0],50,62)
        rec=out["records"][0]
        self.assertEqual(set(rec["arms"]),{
            "sham","self_removed","timed_offtarget"})
        self.assertEqual(len(rec["per_tick_exposure"]),12)
        self.assertEqual(
            sum(v["sham_focal_birth_budget"] for v in rec["per_tick_exposure"].values()),
            rec["sham_prescribed_focal_suppression_count"])
        self.assertLessEqual(rec["actual_offtarget_suppression_count"],
                             rec["sham_prescribed_focal_suppression_count"])
        self.assertEqual(
            rec["arms"]["timed_offtarget"]["focal_suppressed"],0)

if __name__=="__main__":
    unittest.main()
