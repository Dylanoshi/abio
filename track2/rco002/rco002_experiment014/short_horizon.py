#!/usr/bin/env python3
"""E014 phase 2: short-horizon prospective counterfactuals from one reconstructed E011 state.

Reconstructs E011 from its recorded settings, advances the SHAM trajectory up to
the step immediately before a reported candidate, then branches into matched
modes. Does NOT infer verified organizational self-maintenance.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

MODES = ("sham", "target_block", "control_block", "product_scramble")


def load_sim(path):
    spec = importlib.util.spec_from_file_location("e011_module_for_e014", str(path))
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load E011 simulator: {path}")
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)
    return sim


def physical_hash(s):
    """Hash physical state plus target/control identity; omit derived audit histories."""
    snapshot = dict(
        cells=sorted(s["cells"].items()),
        ids=sorted(s["ids"].items()),
        nutrient=sorted(s["nutrient"]),
        bonds=sorted([list(x) for x in s["bonds"]]),
        rules=sorted([[a, b, value] for (a, b), value in s["rule"].items()]),
        next_id=s["next_id"],
        target_lid=s["target_lid"],
        control_lid=s["control_lid"],
        target_flid=s["target_flid"],
        control_flid=s["control_flid"],
        original_ids=sorted(s["original_ids"]),
        branch_motifs=sorted(s.get("branch_motifs", set())),
    )
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def branch_step_rows(sim, s, seed, mode, event_start, end, args):
    before_suppressed = s["suppressed"]
    before_births = s["catalytic_births"]
    output = []
    events = []
    lineage_rows = []
    for step in range(event_start, end + 1):
        before = physical_hash(s)
        pre_suppressed = s["suppressed"]
        sim.tick(s, seed, mode, step, args, events, lineage_rows)
        exact = s["exact_rows"][-1]
        history = s["history"][-1]
        output.append({
            "step": step,
            "strict_candidate": int(exact["strict_candidate"]),
            "founder_replacement": int(exact["founder_replacement"]),
            "exact_motif_preservation": int(exact["exact_motif_preservation"]),
            "recent_branch_motif_births": int(exact["recent_branch_motif_births"]),
            "recent_regenerative_incorporations": int(exact["recent_regenerative_incorporations"]),
            "target_functional_age": history["target_functional_age"],
            "target_functional_size": history["target_functional_size"],
            "target_functional_original_retained": history["target_functional_original_retained"],
            "target_functional_similarity": history["target_functional_similarity"],
            "target_functional_entered": history["target_functional_entered"],
            "target_functional_departed": history["target_functional_departed"],
            "target_catalytic_births_cumulative": history["target_catalytic_births"],
            "suppressed_this_step": s["suppressed"] - pre_suppressed,
            "state_changed": before != physical_hash(s),
        })
    return {
        "rows": output,
        "strict_candidate_steps": sum(x["strict_candidate"] for x in output),
        "suppressed_total": s["suppressed"] - before_suppressed,
        "catalytic_births_total": s["catalytic_births"] - before_births,
        "final_physical_hash": physical_hash(s),
        "event_count": len(events),
    }


def run(sim, settings, seed, event_start, horizon, expected_sham_steps=None):
    a = argparse.Namespace(**settings)
    branch_at = int(a.steps * a.interrupt_fraction)
    if not branch_at < event_start <= a.steps:
        raise ValueError("Event must fall after initial intervention selection and within run")
    if not (1 <= horizon <= a.steps - event_start + 1):
        raise ValueError("Horizon must be positive and remain within simulation steps")
    base = sim.initialize(seed, a)
    shared_events, shared_lineages = [], []
    for step in range(1, branch_at + 1):
        sim.tick(base, seed, "common", step, a, shared_events, shared_lineages)
    sim.select_target(base, a, seed, shared_events, branch_at)
    # Reconstruct the ORIGINAL SHAM branch until immediately before the event.
    for step in range(branch_at + 1, event_start):
        sim.tick(base, seed, "sham", step, a, shared_events, shared_lineages)
    initial_hash = physical_hash(base)
    branches = {}
    for mode in MODES:
        s = copy.deepcopy(base)
        if physical_hash(s) != initial_hash:
            raise AssertionError("Branches did not begin from the same physical state")
        branches[mode] = branch_step_rows(
            sim, s, seed, mode, event_start, event_start + horizon - 1, a)
    sham_count = branches["sham"]["strict_candidate_steps"]
    # E011 uses cumulative catalytic ancestry and an activity window, so a
    # late intervention may not immediately change the strict-candidate flag.
    comparison = {}
    sham = branches["sham"]
    for mode in MODES[1:]:
        other = branches[mode]
        comparison[mode] = {
            "candidate_step_difference_vs_sham": sham_count - other["strict_candidate_steps"],
            "intervention_exposure": (other["suppressed_total"] > 0 if mode != "product_scramble"
                                      else other["final_physical_hash"] != sham["final_physical_hash"]),
            "final_physical_state_differs_from_sham":
                other["final_physical_hash"] != sham["final_physical_hash"],
        }
    return {
        "schema": "abio-e014-short-horizon-branch-v1",
        "source": "prospective reconstruction from E011 algorithm/settings, not saved E013 checkpoint",
        "seed": seed,
        "event_start_step": event_start,
        "end_step": event_start + horizon - 1,
        "original_branch_step": branch_at,
        "identical_initial_physical_hash": initial_hash,
        "initial_target_flid": base["target_flid"],
        "initial_control_flid": base["control_flid"],
        "branches": branches,
        "matched_comparison": comparison,
        "expected_historical_sham_steps": expected_sham_steps,
        "historical_sham_reproduced": (
            None if expected_sham_steps is None else sham_count == expected_sham_steps),
        "scientific_conclusion": {
            "verified_self_maintenance": False,
            "limitations": [
                "Late interventions cannot prove how a network initially arose.",
                "Reconstructed state must reproduce historical sham evidence before interpretation.",
                "Candidate steps are serially correlated, not independent organizations.",
                "Intervention exposure and target identity must be verified independently.",
                "Physical hash verifies matched initial reconstruction, not functional-organizational identity.",
                "Short-horizon divergence is not proof of causal necessity or regeneration.",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e011", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--event-start", type=int, required=True)
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--expected-sham-steps", type=int)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    sim = load_sim(a.e011)
    settings = json.loads(a.settings.read_text())
    result = run(sim, settings, a.seed, a.event_start, a.horizon,
                 a.expected_sham_steps)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "output": str(a.out),
        "historical_sham_reproduced": result["historical_sham_reproduced"],
        "candidate_steps_by_mode": {k: v["strict_candidate_steps"]
                                   for k, v in result["branches"].items()},
        "intervention_exposure": {k: v["intervention_exposure"]
                                  for k, v in result["matched_comparison"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
