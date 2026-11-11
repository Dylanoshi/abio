#!/usr/bin/env python3
"""E015 Phase 3: source-deposition intervention must not suppress reactions."""
import argparse
import copy
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from ablation import physical_signature
from run import DEFAULTS
from source_ablation import choose_focal, evaluate, load_sim

class SourceAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e015_sim.py")
        cls.settings=argparse.Namespace(**dict(DEFAULTS,size=12,steps=100,
                                                 initial_density=.5,
                                                 rule_density=1.0,
                                                 catalysis_rate=1.0,
                                                 supply=.10))

    def test_policy_acts_after_birth_not_on_birth(self):
        sim=self.sim
        a=self.settings
        state=sim.initialize(1,a)
        for t in range(1,31):
            sim.tick(state,1,"local",t,a,[],[])
        # One shared checkpoint for policy comparison. At the next tick, birth
        # events must be identical; only the future field levels may differ.
        all_state=copy.deepcopy(state)
        stopped=copy.deepcopy(state)
        before_deposits=state["e015_stats"]["deposited_births_nonfocal"]
        before_blocked=state["e015_stats"]["blocked_deposits_nonfocal"]
        before_catalysis=state["catalytic_births"]
        stopped["e015_deposition_policy"]="none"
        sim.tick(all_state,1,"local",31,a,[],[])
        sim.tick(stopped,1,"local",31,a,[],[])
        self.assertEqual(all_state["cells"],stopped["cells"])
        self.assertEqual(all_state["bonds"],stopped["bonds"])
        self.assertEqual(all_state["ids"],stopped["ids"])
        self.assertEqual(all_state["catalytic_births"],stopped["catalytic_births"])
        self.assertEqual(all_state["motif_events"],stopped["motif_events"])
        # Counters are cumulative. Historical deposits before the checkpoint
        # must remain; the ablated branch must add no NEW deposits.
        self.assertEqual(
            stopped["e015_stats"]["deposited_births_nonfocal"],before_deposits)
        new_births=stopped["catalytic_births"]-before_catalysis
        self.assertGreater(new_births,0)
        self.assertEqual(
            stopped["e015_stats"]["blocked_deposits_nonfocal"]-before_blocked,
            new_births)
        self.assertEqual(
            all_state["e015_stats"]["deposited_births_nonfocal"]-before_deposits,
            new_births)
        # At this tick both variants see the same previous field; any effect
        # of deposit suppression on bond-breaking begins on later ticks.
        self.assertNotEqual(all_state["e015_field"],stopped["e015_field"])

    def test_default_equals_explicit_all_deposition(self):
        sim=self.sim
        a=self.settings
        left=sim.initialize(2,a)
        right=copy.deepcopy(left)
        right["e015_deposition_policy"]="all"
        for t in range(1,31):
            sim.tick(left,2,"local",t,a,[],[])
            sim.tick(right,2,"local",t,a,[],[])
            self.assertEqual(physical_signature(left),physical_signature(right))

    def test_focal_filter_pure_when_fid_missing(self):
        sim=self.sim
        a=self.settings
        state=sim.initialize(3,a)
        state["e015_deposition_policy"]="focal_only"
        state["e015_focal_fid"]=-999999
        for t in range(1,21):
            sim.tick(state,3,"local",t,a,[],[])
        self.assertEqual(state["e015_stats"]["deposited_births_focal"],0)
        self.assertEqual(state["e015_stats"]["deposited_births_nonfocal"],0)

    def test_checkpoint_selection_uses_only_prior_events(self):
        sim=self.sim
        state=sim.initialize(0,self.settings)
        for t in range(1,51):
            sim.tick(state,0,"local",t,self.settings,[],[])
        choice,record=choose_focal(state,50)
        self.assertTrue(choice is None or choice["age_at_checkpoint"]>=30)
        if choice:
            self.assertEqual(record["prior_window"],[11,50])
        else:
            self.assertEqual(record["eligible"],0)

    def test_small_seed_smoke(self):
        params=dict(DEFAULTS,size=12,steps=100)
        result=evaluate(self.sim,params,[0],50,55)
        self.assertEqual(set(result["individual"][0]["arms"]),{
            "all","no_new_field","remove_focal_source","focal_source_only"})
        self.assertEqual(len(result["individual"][0]["arms"]["all"]["timeline"]),5)

if __name__=="__main__":
    unittest.main()
