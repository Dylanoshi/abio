#!/usr/bin/env python3
"""E014 phase 4: preflight check for a real exposure-matched active negative control.

Reads the E014 mechanism trace, identifies target-block suppression events and
locates sham catalytic births from *other* functional organizations at matching
simulation steps. This does NOT execute a new intervention and is not a causal
test on its own.

Candidate controls are selected using the sham trajectory and the target
suppression schedule; this is exploratory and must be preregistered on fresh
independent runs to avoid post-selection bias.
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def control_plan(trace):
    if trace.get("schema") != "abio-e014-mechanism-trace-v1":
        raise ValueError("Expected E014 mechanism trace v1")
    branches = trace["branches"]
    sham = branches["sham"]["rows"]
    targeted = branches["target_block"]["rows"]
    if len(sham) != len(targeted):
        raise ValueError("Matched branches must have aligned steps")
    target_fid = trace["provenance"]["target_flid"]
    motif_events = branches["sham"]["target_motif_births"]
    # Preserve producer identity for every recorded birth event by particle ID.
    producer_by_pid = {int(e["particle_id"]): e["producer_fid"] for e in motif_events}
    suppression = []
    controls_at_step = {}
    for original, blocked in zip(sham, targeted):
        t = int(original["step"])
        if t != int(blocked["step"]):
            raise ValueError("Matched branches are temporally misaligned")
        births = original["new_catalytic_birth_events"]
        controls = []
        for event in births:
            pid = int(event["particle_id"])
            # Exclude all events from the selected target functional identity.
            # Unknown producer identities are not assumed independent controls.
            producer = producer_by_pid.get(pid)
            if producer is None or producer == target_fid:
                continue
            controls.append({
                "step": t,
                "particle_id": pid,
                "catalyst_pair": sorted([int(event["catalyst_a"]), int(event["catalyst_b"])]),
                "producer_fid": producer,
            })
        controls_at_step[t] = sorted(controls, key=lambda e:
                                     (e["producer_fid"], e["catalyst_pair"], e["particle_id"]))
        for event in blocked["new_suppression_events"]:
            suppression.append({
                "step": t,
                "blocked_catalyst_pair": sorted([
                    int(event["catalyst_a"]), int(event["catalyst_b"])
                ]),
                "blocked_product_type": event["product_type"],
            })
    counts = Counter()
    allocations = []
    unmatched = []
    for s in suppression:
        t = s["step"]
        idx = counts[t]
        options = controls_at_step.get(t, [])
        if idx < len(options):
            allocations.append({"target_suppression": s, "candidate_control": options[idx]})
            counts[t] += 1
        else:
            unmatched.append(s)
    return {
        "schema": "abio-e014-active-control-preflight-v1",
        "source": "E014 matched trace; exploratory sham-event selection",
        "target_fid": target_fid,
        "target_suppression_events": len(suppression),
        "exact_step_matched_events": len(allocations),
        "unmatched_target_events": unmatched,
        "matching_possible_at_each_target_step": len(unmatched) == 0 and len(suppression) > 0,
        "proposed_control_events": allocations,
        "alternative_births_per_step": {str(t): len(v) for t,v in controls_at_step.items()},
        "limitations": [
            "Exact-step matching of count alone does not match spatial reach, chemistry or downstream effects.",
            "Intervention exposure must be verified by rerunning the modified dynamics.",
            "Suppressed opportunities in target branch need not correspond to realized sham births after trajectories diverge.",
            "Controls chosen retrospectively on this seed must not establish population-level causal evidence.",
            "Selected functional identity relies on E011's heuristic lineage tracking.",
            "This is a design preflight, not proof of RAF closure or self-maintenance.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trace",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=control_plan(json.loads(a.trace.read_text()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({
        "target_suppression_events": result["target_suppression_events"],
        "exact_step_matched_events": result["exact_step_matched_events"],
        "matching_possible_at_each_target_step": result["matching_possible_at_each_target_step"],
        "unmatched_steps": [x["step"] for x in result["unmatched_target_events"]],
        "proposed_control_events": [x["candidate_control"] for x in result["proposed_control_events"]],
        "out": str(a.out),
    }, indent=2))


if __name__=="__main__":
    main()
