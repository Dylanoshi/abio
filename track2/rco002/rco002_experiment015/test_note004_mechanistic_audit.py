#!/usr/bin/env python3
"""Tests for Note 004 mechanistic audit observational parity and accounting."""
import argparse
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from ablation import load_sim
from note004_mechanistic_audit import paired_audit,summarize
from run import DEFAULTS

class Note004AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=load_sim(HERE/"e015_sim.py")
        cls.params=dict(DEFAULTS,size=12,steps=100,
                        initial_density=.5,rule_density=1.,
                        catalysis_rate=.8,supply=.1)

    def test_small_paired_audit_observation_only(self):
        report=paired_audit(self.sim,self.params,[0,1],50,58,True)
        self.assertEqual(report["seeds"],[0,1])
        for record in report["records"]:
            for arm in ("sham","self_removed"):
                rows=record["arms"][arm]["timeline"]
                self.assertEqual(len(rows),8)
                self.assertTrue(all(
                    r["focal_bond_exposed_trials"]<=r["focal_bond_break_trials"]
                    for r in rows))
                self.assertTrue(all(r["material_entered"]>=0 and
                                    r["material_departed"]>=0 for r in rows))
                self.assertTrue(all(r["focal_bond_actual_break_trials"]<=
                                    r["focal_bond_break_trials"] for r in rows))
            self.assertEqual(
                record["arms"]["self_removed"]["summary"]["total_self_field_deposits"],0)
            self.assertEqual(
                record["arms"]["sham"]["summary"]["total_self_deposits_blocked"],0)

    def test_empty_focal_trace_summarizes(self):
        rows=[{
            "bridge_present":0,"profile_similarity_to_checkpoint":0.,
            "active_motifs":0,"bridge_size":0,
            "material_entered":0,"material_departed":0,
            "internal_bond_gain":0,"internal_bond_loss":0,
            "focal_catalytic_births":0,"focal_field_deposits":0,
            "focal_deposits_blocked":0,"other_deposits_at_focal_sites":0,
            "field_at_focal_mean":0.,
            "nutrient_sites_in_bridge_and_one_hop":0,
            "focal_bond_break_trials":0,"focal_bond_exposed_trials":0,
            "focal_bond_actual_break_trials":0,
            "focal_bond_baseline_avoided_break_trials":0,
            "field_sum_at_focal_bond_trials":0.,
            "original_ids_in_bridge":0,
        }]
        out=summarize(rows,51)
        self.assertEqual(out["bridge_present_steps"],0)
        self.assertEqual(out["mean_field_per_focal_break_trial"],0.)

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            paired_audit(self.sim,self.params,[0],50,50)

if __name__=="__main__":
    unittest.main()
