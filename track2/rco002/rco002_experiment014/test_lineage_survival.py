#!/usr/bin/env python3
import unittest
from lineage_survival import summarize_rows, audit


def row(t, n, motif=0, regeneration=0, candidate=0):
    return dict(step=t, target_functional_size=n,
                exact_motif_preservation=motif,
                recent_regenerative_incorporations=regeneration,
                strict_candidate=candidate,
                target_functional_similarity=float(n>0))


class SurvivalTests(unittest.TestCase):
    def test_intervals_and_reappearance(self):
        out=summarize_rows([row(1,3,1),row(2,0),row(3,2,1),row(4,0)])
        self.assertEqual(out["first_absent_step"],2)
        self.assertEqual(out["first_reappearance_after_absence"],3)
        self.assertEqual(out["present_intervals"],[
            {"start":1,"end":1,"duration":1},
            {"start":3,"end":3,"duration":1}
        ])

    def test_contiguous_required(self):
        with self.assertRaises(ValueError):
            summarize_rows([row(1,1),row(3,0)])

    def test_no_absence(self):
        out=summarize_rows([row(1,1),row(2,1)])
        self.assertIsNone(out["first_absent_step"])
        self.assertIsNone(out["first_reappearance_after_absence"])

    def test_schema_rejection(self):
        with self.assertRaises(ValueError):
            audit({"schema":"unknown"})


if __name__=="__main__":
    unittest.main()
