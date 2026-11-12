#!/usr/bin/env python3
"""Phase 4: test observational-only tracing and conservative ancestry."""
import argparse
import copy
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import DEFAULTS
from ablation import physical_signature
from ancestry_exposure_audit import ExposureRecorder, audit, load_sim
from source_ablation import choose_focal

class Phase4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e015_sim.py")
        cls.a=argparse.Namespace(**dict(DEFAULTS,size=12,steps=100,
                                         rule_density=1.0,catalysis_rate=.8,
                                         initial_density=.5,supply=.1))

    def test_tracing_does_not_change_physics(self):
        for seed in (0,1):
            a=self.a; sim=self.sim
            base=sim.initialize(seed,a)
            for t in range(1,51):
                sim.tick(base,seed,"local",t,a,[],[])
            focal,_=choose_focal(base,50)
            x=copy.deepcopy(base)
            x["e015_audit_hook"]=ExposureRecorder(x,focal,a)
            y=copy.deepcopy(base)
            for t in range(51,61):
                sim.tick(x,seed,"local",t,a,[],[])
                sim.tick(y,seed,"local",t,a,[],[])
                self.assertEqual(physical_signature(x),physical_signature(y),
                                 f"seed={seed}, step={t}")

    def test_no_focal_still_produces_valid_provenance(self):
        a=self.a
        s=self.sim.initialize(4,a)
        tracer=ExposureRecorder(s,None,a)
        s["e015_audit_hook"]=tracer
        for t in range(1,8):
            self.sim.tick(s,4,"local",t,a,[],[])
        self.assertEqual(tracer.stats["bridge_bond_trials"],0)
        self.assertEqual(len(tracer.by_step),7)

    def test_small_full_audit(self):
        params=dict(DEFAULTS,size=12,steps=100,rule_density=1.0,
                    catalysis_rate=.8,initial_density=.5,supply=.1)
        result=audit(self.sim,params,[0],50,60)
        self.assertEqual(len(result["records"]),1)
        self.assertEqual(result["records"][0]["seed"],0)
        self.assertEqual(len(result["records"][0]["per_step"]),10)

if __name__=="__main__":
    unittest.main()
