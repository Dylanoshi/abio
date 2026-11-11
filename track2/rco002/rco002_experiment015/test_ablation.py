#!/usr/bin/env python3
import unittest
from pathlib import Path
from run import DEFAULTS
from ablation import load_sim, run, eligible_groups, physical_signature

HERE=Path(__file__).resolve().parent

class AblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e015_sim.py")

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            run(self.sim,dict(DEFAULTS,size=8,steps=100),[0],100,100)

    def test_identical_checkpoint_and_three_postbranch_arms(self):
        result=run(self.sim,dict(DEFAULTS,size=8,steps=100),[0],50,55)
        rec=result["records"][0]
        self.assertEqual(set(rec["by_mode"]),{"local","disabled","shuffled"})
        self.assertTrue(rec["checkpoint_physical_field_hash"])
        self.assertEqual(len(rec["by_mode"]["local"]["timeline"]),5)
        self.assertEqual(len(rec["by_mode"]["disabled"]["timeline"]),5)
        self.assertEqual(len(rec["by_mode"]["shuffled"]["timeline"]),5)
        self.assertEqual(
            rec["by_mode"]["disabled"]["postbranch_exposed_trials"],0)

    def test_checkpoint_groups_are_preselected(self):
        from argparse import Namespace
        a=Namespace(**dict(DEFAULTS,size=8,steps=100))
        state=self.sim.initialize(0,a)
        for t in range(1,21):
            self.sim.tick(state,0,"local",t,a,[],[])
        for g in eligible_groups(state):
            self.assertGreaterEqual(g["age_at_checkpoint"],30)
            self.assertGreaterEqual(g["size_at_checkpoint"],3)
            self.assertTrue(g["profile_at_checkpoint"])

if __name__=="__main__":
    unittest.main()
