#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from active_control_run import load_schedule,run
from short_horizon import load_sim


def sample_preflight():
    return {
        "schema":"abio-e014-active-control-preflight-v1",
        "matching_possible_at_each_target_step":True,
        "proposed_control_events":[{
            "target_suppression":{"step":16},
            "candidate_control":{"step":16,"catalyst_pair":[100,101],"particle_id":300,
                                  "producer_fid":22}
        }],
    }


class ActiveControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e014_sim.py")
        cls.settings={
            "size":8,"steps":20,"initial_density":.35,
            "decay":.008,"supply":.018,"bond_form":.075,
            "bond_break":.018,"rule_density":.85,
            "catalysis_rate":.14,"background_rate":.0015,
            "interrupt_fraction":.5,"min_target_size":3,
            "activity_window":5,
        }

    def test_schedule(self):
        self.assertEqual(load_schedule(sample_preflight()),{16:{(100,101)}})

    def test_matched_deterministic(self):
        a=run(self.sim,self.settings,seed=3,start=16,end=18,
              preflight=sample_preflight())
        b=run(self.sim,self.settings,seed=3,start=16,end=18,
              preflight=sample_preflight())
        self.assertEqual(a,b)
        self.assertEqual(a["planned_offtarget_suppressions"],1)
        self.assertEqual(a["realized_scheduled_offtarget_suppressions"],0)
        self.assertFalse(a["all_offtarget_events_realized"])
        self.assertFalse(a["interpretation"]["verified_self_maintenance"])

    def test_reject_unmatched_schedule(self):
        bad=sample_preflight()
        bad["matching_possible_at_each_target_step"]=False
        with self.assertRaises(ValueError):
            run(self.sim,self.settings,3,16,18,bad)


if __name__=="__main__":
    unittest.main()
