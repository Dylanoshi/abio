#!/usr/bin/env python3
"""E014 exposure audit for an E013 regime/seed, using saved E011 event files.

This only inspects existing records. It does not establish causal necessity
or change the simulator. It distinguishes intervention *attempt* from exposure.
"""
import argparse
import csv
import json
from pathlib import Path


def read(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def integer(row, key, default=0):
    value = row.get(key)
    return int(value) if value not in (None, "") else default


def window_stats(rows, start, end, predicate=None):
    qualifying = [r for r in rows if start <= integer(r, "step") <= end and
                  (predicate is None or predicate(r))]
    return {"count": len(qualifying),
            "steps": sorted(set(integer(r, "step") for r in qualifying))}


def audit(e011, seed, start=530, end=535, radius=100):
    settings = json.loads((e011 / "settings.json").read_text())
    branch_at = int(int(settings["steps"]) * float(settings["interrupt_fraction"]))
    events = read(e011 / "events.csv")
    records = {}
    for mode in ("sham", "target_block", "control_block", "product_scramble"):
        branch_events = [r for r in events if integer(r, "seed", -1) == seed and r.get("mode") == mode]
        suppression = [r for r in branch_events if r.get("event") == "suppressed"]
        births = [r for r in branch_events if r.get("event") == "catalytic_birth"]
        traces = read(e011 / f"product_ancestry_seed{seed}_{mode}.csv")
        target_traces = [r for r in traces if integer(r, "target_producer") == 1]
        exact_target_traces = [r for r in target_traces if integer(r, "exact_branch_motif") == 1]
        time = read(e011 / f"timeseries_seed{seed}_{mode}.csv")
        by_step = {integer(r, "step"): r for r in time}
        records[mode] = {
            "suppression_over_entire_postbranch": window_stats(suppression, branch_at + 1, int(settings["steps"])),
            "suppression_near_candidate": window_stats(suppression, max(branch_at+1,start-radius), min(int(settings["steps"]),end+radius)),
            "suppression_during_candidate": window_stats(suppression, start, end),
            "catalytic_births_during_candidate": window_stats(births, start, end),
            "target_producer_births_near_candidate": window_stats(target_traces, max(branch_at+1,start-radius), min(int(settings["steps"]),end+radius)),
            "exact_target_motif_births_near_candidate": window_stats(exact_target_traces, max(branch_at+1,start-radius), min(int(settings["steps"]),end+radius)),
            "target_at_window_start": {
                k: (by_step.get(start, {}).get(k, None)) for k in (
                    "target_functional_id", "target_functional_size",
                    "target_functional_age", "target_functional_similarity",
                    "target_functional_original_retained")
            },
        }
    return {
        "schema": "abio-e014-exposure-audit-v1",
        "source": "retrospective E011 event files",
        "regime_dir": str(e011.parent.name),
        "seed": seed,
        "event_window": [start, end],
        "original_branch_step": branch_at,
        "modes": records,
        "interpretation": {
            "verified_self_maintenance": False,
            "note": "Historical branch interventions began at the original branch step; "
                    "these exposures cannot substitute for a new late matched intervention.",
            "product_scramble_warning": "Product scrambling does not log suppressed events. "
                    "Exposure requires comparing targeted product identities under matched replay.",
            "next_gate": "Identify actual candidate-producing reactions, then place and verify "
                         "a short intervention during those reactions; check immediate state divergence.",
        },
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--e011", required=True, type=Path)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--start", type=int, default=530)
    p.add_argument("--end", type=int, default=535)
    p.add_argument("--radius", type=int, default=100)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.start < 1 or a.end < a.start or a.radius < 0:
        p.error("invalid event window or radius")
    result = audit(a.e011, a.seed, a.start, a.end, a.radius)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "schema": result["schema"],
        "historical_branch_step": result["original_branch_step"],
        "per_mode": {
            name: {
                "suppressed_during_candidate": value["suppression_during_candidate"]["count"],
                "suppressed_postbranch": value["suppression_over_entire_postbranch"]["count"],
                "target_birth_steps_near_candidate": value["exact_target_motif_births_near_candidate"]["steps"]
            } for name,value in result["modes"].items()
        },
        "out": str(a.out),
    }, indent=2))


if __name__ == "__main__":
    main()
