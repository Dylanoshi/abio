#!/usr/bin/env python3
"""Unit tests for E014 retrospective candidate audit."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from audit import analyze, intervals


class AuditTests(unittest.TestCase):
    def test_intervals(self):
        self.assertEqual(intervals([6, 5, 3, 6]), [
            {"start": 3, "end": 3, "duration_steps": 1},
            {"start": 5, "end": 6, "duration_steps": 2},
        ])

    def test_actual_branch_step_and_control_only_flags(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "batch_example"
            out = root / "regime_00" / "e011"
            out.mkdir(parents=True)
            (out / "settings.json").write_text(json.dumps({
                "steps": 100, "interrupt_fraction": 0.3, "seeds": 1,
                "rule_density": 0.85, "catalysis_rate": 0.14,
            }))
            header = [
                "step", "strict_candidate", "founder_replacement",
                "exact_motif_preservation", "recent_regenerative_incorporations",
            ]
            for mode in ("sham", "target_block", "control_block", "product_scramble"):
                with (out / f"exact_network_seed0_{mode}.csv").open("w", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=header)
                    writer.writeheader()
                    writer.writerow(dict(step=25, strict_candidate=1, founder_replacement=1,
                                         exact_motif_preservation=1, recent_regenerative_incorporations=1))
                    writer.writerow(dict(step=31, strict_candidate=int(mode == "control_block"),
                                         founder_replacement=1, exact_motif_preservation=1,
                                         recent_regenerative_incorporations=1))
            result = analyze(root)
            regime = result["regimes"][0]
            self.assertEqual(regime["branch_step"], 30)
            self.assertEqual(regime["sham_positive_seeds"], 0)
            self.assertEqual(regime["control_only_seeds"], 1)
            self.assertEqual(regime["seeds"][0]["by_mode"]["control_block"]["candidate_steps"], 1)
            self.assertFalse(result["interpretation"]["verified_organizational_self_maintenance"])


if __name__ == "__main__":
    unittest.main()
