#!/usr/bin/env python3
"""Regression tests for E015 Phase 5 dynamically tracked source removal."""
import argparse
import copy
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

from ablation import physical_signature
from dynamic_source_ablation import MaterialBridge, precheckpoint_rate, run, load_sim
from run import DEFAULTS
from source_ablation import choose_focal


class DynamicAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e015_sim.py")
        cls.params=dict(DEFAULTS,size=12,steps=100,initial_density=.5,
                        rule_density=1.0,catalysis_rate=.8,supply=.1)
        cls.a=argparse.Namespace(**cls.params)

    def checkpoint(self,seed=0):
        s=self.sim.initialize(seed,self.a)
        for t in range(1,51):
            self.sim.tick(s,seed,"local",t,self.a,[],[])
        focal,_=choose_focal(s,50)
        return s,focal

    def test_observational_sham_matches_hook_free_replay(self):
        for seed in (0,1):
            base,focal=self.checkpoint(seed)
            observed=copy.deepcopy(base)
            plain=copy.deepcopy(base)
            observed["e015_audit_hook"]=MaterialBridge(focal)
            observed["e015_deposition_policy"]="all"
            for t in range(51,61):
                self.sim.tick(observed,seed,"local",t,self.a,[],[])
                self.sim.tick(plain,seed,"local",t,self.a,[],[])
                self.assertEqual(physical_signature(observed),physical_signature(plain),
                                 f"seed={seed}, step={t}")

    def test_policy_disables_only_deposits_on_same_tick(self):
        base,focal=self.checkpoint(0)
        a=copy.deepcopy(base)
        b=copy.deepcopy(base)
        a["e015_deposition_policy"]="all"
        b["e015_deposition_policy"]="dynamic_self_off"
        a["e015_audit_hook"]=MaterialBridge(focal)
        b["e015_audit_hook"]=MaterialBridge(focal)
        self.sim.tick(a,0,"local",51,self.a,[],[])
        self.sim.tick(b,0,"local",51,self.a,[],[])
        self.assertEqual(a["cells"],b["cells"])
        self.assertEqual(a["bonds"],b["bonds"])
        self.assertEqual(a["ids"],b["ids"])
        self.assertEqual(a["catalytic_births"],b["catalytic_births"])
        self.assertEqual(a["motif_events"],b["motif_events"])
        self.assertEqual(b["e015_audit_hook"].deposits["focal"],0)

    def test_calibration_uses_only_precheckpoint(self):
        base,focal=self.checkpoint(0)
        rate,counts=precheckpoint_rate(base,focal,50)
        self.assertGreaterEqual(rate,0.)
        self.assertLessEqual(rate,1.)
        self.assertEqual(sum(counts.values()),sum(
            10<e["step"]<=50 for e in base["motif_events"]))

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            run(self.sim,self.params,[0],50,50)

    def test_small_matched_control_smoke(self):
        result=run(self.sim,self.params,[0],50,57)
        rec=result["records"][0]
        self.assertEqual(set(rec["by_arm"]),{
            "sham","dynamic_self_off","offtarget_control","global_field_off"})
        self.assertEqual(len(rec["by_arm"]["sham"]["timeline"]),7)
        self.assertEqual(rec["by_arm"]["dynamic_self_off"]["focal_deposits_allowed"],0)
        self.assertEqual(rec["by_arm"]["offtarget_control"]["focal_deposits_prevented"],0)
        self.assertEqual(rec["by_arm"]["global_field_off"]["nonfocal_deposits_allowed"],0)


if __name__=="__main__":
    unittest.main()
