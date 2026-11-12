#!/usr/bin/env python3
"""Tests for selecting off-target event opportunities."""
import unittest

from active_control_preflight import control_plan


def row(step, births=(), suppressed=()):
    return {
        "step": step,
        "new_catalytic_birth_events": list(births),
        "new_suppression_events": list(suppressed),
    }


class ControlPreflightTests(unittest.TestCase):
    def sample(self, include_other=True):
        births = [{"particle_id": 100, "catalyst_a": 1, "catalyst_b": 2}]
        ancestry = [{"particle_id": 100, "producer_fid": 7}]
        if include_other:
            births.append({"particle_id": 101, "catalyst_a": 3, "catalyst_b": 4})
            ancestry.append({"particle_id": 101, "producer_fid": 8})
        return {
            "schema": "abio-e014-mechanism-trace-v1",
            "provenance": {"target_flid": 7},
            "branches": {
                "sham": {
                    "rows": [row(513, births=births)],
                    "target_motif_births": ancestry,
                },
                "target_block": {
                    "rows": [row(513, suppressed=[{
                        "catalyst_a": 1,
                        "catalyst_b": 2,
                        "product_type": "A",
                    }])],
                },
            },
        }

    def test_finds_same_step_off_target(self):
        result = control_plan(self.sample())
        self.assertEqual(result["target_suppression_events"], 1)
        self.assertEqual(result["exact_step_matched_events"], 1)
        self.assertTrue(result["matching_possible_at_each_target_step"])
        self.assertEqual(result["proposed_control_events"][0]["candidate_control"]["producer_fid"], 8)

    def test_reports_no_control_when_none_exposed(self):
        result = control_plan(self.sample(include_other=False))
        self.assertEqual(result["exact_step_matched_events"], 0)
        self.assertFalse(result["matching_possible_at_each_target_step"])
        self.assertEqual(len(result["unmatched_target_events"]), 1)

    def test_rejects_wrong_schema(self):
        with self.assertRaises(ValueError):
            control_plan({"schema": "other"})


if __name__ == "__main__":
    unittest.main()
