#!/usr/bin/env python3
"""E014 phase 3: mechanistic event trace of an exposure-positive matched intervention.

Read-only reconstruction of historical E011 dynamics. Does not change E011, E012,
the remote API, or any prior research outputs. Causal claims remain provisional.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from short_horizon import load_sim, physical_hash

MODES = ("sham", "target_block", "control_block", "product_scramble")


def trace(sim, settings, seed, start, end, expected_sham_steps=None):
    a = argparse.Namespace(**settings)
    original_branch = int(a.steps * a.interrupt_fraction)
    if not (original_branch < start <= end <= a.steps):
        raise ValueError("Window must follow E011 branch selection and fit within run")
    base = sim.initialize(seed, a)
    shared_events, shared_lineages = [], []
    for t in range(1, original_branch + 1):
        sim.tick(base, seed, "common", t, a, shared_events, shared_lineages)
    sim.select_target(base, a, seed, shared_events, original_branch)
    for t in range(original_branch + 1, start):
        sim.tick(base, seed, "sham", t, a, shared_events, shared_lineages)
    initial_hash = physical_hash(base)
    branches = {}
    for mode in MODES:
        state = copy.deepcopy(base)
        events, lineages = [], []
        observed = []
        motif_start = len(state["motif_events"])
        uptake_start = len(state["uptake_rows"])
        for t in range(start, end + 1):
            before_event = len(events)
            before_motifs = len(state["motif_events"])
            before_uptake = len(state["uptake_rows"])
            before_cells = dict(state["cells"])
            before_ids = dict(state["ids"])
            sim.tick(state, seed, mode, t, a, events, lineages)
            exact = state["exact_rows"][-1]
            current = state["history"][-1]
            new_events = events[before_event:]
            new_motifs = state["motif_events"][before_motifs:]
            new_uptake = state["uptake_rows"][before_uptake:]
            observed.append({
                "step": t,
                "physical_hash": physical_hash(state),
                "strict_candidate": int(exact["strict_candidate"]),
                "motif_preserved": int(exact["exact_motif_preservation"]),
                "founder_replacement": int(exact["founder_replacement"]),
                "recent_regenerative_incorporations":
                    int(exact["recent_regenerative_incorporations"]),
                "functional_similarity": float(current["target_functional_similarity"]),
                "functional_size": int(current["target_functional_size"]),
                "new_suppression_events": [e for e in new_events if e["event"] == "suppressed"],
                "new_catalytic_birth_events": [e for e in new_events if e["event"] == "catalytic_birth"],
                "new_target_motif_births": [e for e in new_motifs if e["target_producer"]],
                "new_target_uptakes": [e for e in new_uptake if e["entered_target"]],
                "particles_added_since_prev_step": [
                    {"site": k, "particle_id": v} for k, v in sorted(state["ids"].items())
                    if v not in set(before_ids.values())
                ],
                "particles_lost_since_prev_step": [
                    v for v in sorted(before_ids.values()) if v not in set(state["ids"].values())
                ],
            })
        branches[mode] = {
            "rows": observed,
            "target_motif_births": state["motif_events"][motif_start:],
            "uptakes": state["uptake_rows"][uptake_start:],
        }
    sham = branches["sham"]["rows"]
    comparisons = {}
    for mode in MODES[1:]:
        other = branches[mode]["rows"]
        differences = []
        for x,y in zip(sham,other):
            if x["physical_hash"] != y["physical_hash"]:
                differences.append(x["step"])
        comparisons[mode] = {
            "first_physical_divergence_step": differences[0] if differences else None,
            "different_physical_steps": len(differences),
            "suppressed_events": sum(len(x["new_suppression_events"]) for x in other),
            "candidate_steps": sum(x["strict_candidate"] for x in other),
            "final_functional_similarity": other[-1]["functional_similarity"],
            "final_functional_size": other[-1]["functional_size"],
            "final_motif_preserved": other[-1]["motif_preserved"],
            "final_recent_regenerative_incorporations":
                other[-1]["recent_regenerative_incorporations"],
        }
    sham_count = sum(x["strict_candidate"] for x in sham)
    return {
        "schema": "abio-e014-mechanism-trace-v1",
        "provenance": {
            "e011_code_hash_sha256": None,
            "settings_sha256": hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest(),
            "seed": seed, "intervention_start": start, "end": end,
            "original_branch_step": original_branch,
            "identical_initial_state_hash": initial_hash,
            "target_flid": base["target_flid"],
            "target_motifs": sorted(base.get("branch_motifs", set())),
        },
        "historical_sham_reproduced": (None if expected_sham_steps is None
                                      else sham_count == expected_sham_steps),
        "sham_candidate_steps": sham_count,
        "branches": branches,
        "comparisons": comparisons,
        "interpretation": {
            "verified_self_maintenance": False,
            "caveats": [
                "Physical divergence may reflect downstream stochastic amplification.",
                "A catalytic suppression event is not proof that an organizational motif is causal.",
                "Control branch may be entirely inactive; check suppressed_events explicitly.",
                "Functional continuity tracking uses an overlap heuristic, not definitive identity.",
                "This analysis revisits an already-selected event; independent prospective tests required.",
            ],
        },
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--e011",required=True,type=Path)
    p.add_argument("--settings",required=True,type=Path)
    p.add_argument("--seed",required=True,type=int)
    p.add_argument("--start",required=True,type=int)
    p.add_argument("--end",required=True,type=int)
    p.add_argument("--expected-sham-steps",type=int)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    sim=load_sim(a.e011)
    settings=json.loads(a.settings.read_text())
    result=trace(sim,settings,a.seed,a.start,a.end,a.expected_sham_steps)
    result["provenance"]["e011_code_hash_sha256"]=hashlib.sha256(a.e011.read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "historical_sham_reproduced":result["historical_sham_reproduced"],
        "target_motifs":result["provenance"]["target_motifs"],
        "comparisons":result["comparisons"],
        "per_mode_target_motif_birth_steps":{
            mode:sorted(set(e["step"] for e in data["target_motif_births"] if e["target_producer"]))
            for mode,data in result["branches"].items()
        },
        "out":str(a.out)
    },indent=2))


if __name__=="__main__":
    main()
