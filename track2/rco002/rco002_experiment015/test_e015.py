#!/usr/bin/env python3
"""E015 structural feedback regression and control tests."""
import copy
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"rco002_experiment014"))
from short_horizon import physical_hash, load_sim
from run import DEFAULTS, execute

class E015Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e015=load_sim(HERE/"e015_sim.py")
        cls.e014=load_sim(HERE.parent/"rco002_experiment014"/"e014_sim.py")
        import argparse
        cls.a=argparse.Namespace(**dict(DEFAULTS,size=8,steps=60))

    def test_disabled_matches_previous_simulator(self):
        # Strong regression: even with catalysis, E015 disabled must leave
        # all original physical dynamics unchanged relative to E014.
        for seed in (0,1,3):
            original=self.e014.initialize(seed,self.a)
            trial=self.e015.initialize(seed,self.a)
            for t in range(1,41):
                self.e014.tick(original,seed,"disabled",t,self.a,[],[])
                self.e015.tick(trial,seed,"disabled",t,self.a,[],[])
                self.assertEqual(physical_hash(original),physical_hash(trial),
                                 msg=f"seed={seed}, step={t}")

    def test_field_causality_and_monotone_protection(self):
        f=self.e015.effective_break_rate
        self.assertAlmostEqual(f(.018,3.0,0.0),.018)
        self.assertLess(f(.018,3.0,1.0),f(.018,3.0,.5))
        self.assertLess(f(.018,3.0,4.0),f(.018,3.0,1.0))
        self.assertAlmostEqual(f(.018,0.0,4.0),.018)
        self.assertAlmostEqual(f(.018,3.0,-1.0),.018)

    def test_no_catalysis_same_physical_dynamics(self):
        import argparse
        a=argparse.Namespace(**dict(DEFAULTS,size=8,steps=60,catalysis_rate=0.0))
        states={mode:self.e015.initialize(2,a) for mode in ("disabled","local","shuffled")}
        for t in range(1,31):
            for mode,s in states.items():
                self.e015.tick(s,2,mode,t,a,[],[])
            reference=physical_hash(states["disabled"])
            self.assertTrue(all(physical_hash(s)==reference for s in states.values()))

    def test_three_condition_smoke(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            result=execute(self.e015,dict(DEFAULTS,size=8,steps=100),[0],Path(tmp))
            self.assertEqual({r["condition"] for r in result["individual_records"]},
                             {"disabled","local","shuffled"})
            self.assertTrue((Path(tmp)/"results.json").exists())
            self.assertTrue((Path(tmp)/"per_seed.csv").exists())

if __name__=="__main__":
    unittest.main()
