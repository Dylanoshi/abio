#!/usr/bin/env python3
"""E014 phase 1: event-level audit of E011 candidate observations.

Read-only analysis. This is NOT deterministic replay or verification of
organizational self-maintenance. It does not modify E011/E012 simulations.
"""
import argparse
import csv
import json
from pathlib import Path

MODES = ("sham", "target_block", "control_block", "product_scramble")


def rows(path):
    if not path.is_file():
        raise FileNotFoundError(f"Missing evidence: {path}")
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def as_int(record, key):
    try:
        return int(record[key])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid {key}: {record!r}") from exc


def intervals(steps):
    """Consecutive candidate steps; not independent observations."""
    ordered = sorted(set(steps))
    result = []
    for step in ordered:
        if result and step == result[-1][-1] + 1:
            result[-1].append(step)
        else:
            result.append([step])
    return [{"start": x[0], "end": x[-1], "duration_steps": len(x)}
            for x in result]


def audit_regime(folder):
    source = folder / "e011"
    settings = json.loads((source / "settings.json").read_text())
    branch_at = int(int(settings["steps"]) * float(settings["interrupt_fraction"]))
    seed_count = int(settings["seeds"])
    seeds = []
    for seed in range(seed_count):
        by_mode = {}
        for mode in MODES:
            evidence = rows(source / f"exact_network_seed{seed}_{mode}.csv")
            # Compare only after the actual branch point for this regime.
            post = [r for r in evidence if as_int(r, "step") > branch_at]
            candidates = [r for r in post if as_int(r, "strict_candidate") == 1]
            by_mode[mode] = {
                "candidate_steps": len(candidates),
                "candidate_intervals": intervals([as_int(r, "step") for r in candidates]),
                "founder_replacement_motif_steps": sum(
                    as_int(r, "founder_replacement") == 1 and
                    as_int(r, "exact_motif_preservation") == 1 for r in post),
                "max_recent_regenerative_incorporations": max(
                    (as_int(r, "recent_regenerative_incorporations") for r in post),
                    default=0),
            }
        sham = by_mode["sham"]["candidate_steps"]
        seeds.append({
            "seed": seed,
            "by_mode": by_mode,
            "candidate_step_differences_vs_sham": {
                mode: sham - by_mode[mode]["candidate_steps"]
                for mode in MODES if mode != "sham"
            },
            "sham_signal": sham > 0,
            "control_only_signal": sham == 0 and any(
                by_mode[mode]["candidate_steps"] > 0 for mode in MODES if mode != "sham"),
        })
    return {
        "regime": folder.name,
        "parameters": {k: settings.get(k) for k in
                       ("rule_density", "catalysis_rate", "size", "steps",
                        "interrupt_fraction", "decay", "supply", "background_rate")},
        "branch_step": branch_at,
        "seeds": seeds,
        "sham_positive_seeds": sum(x["sham_signal"] for x in seeds),
        "control_only_seeds": sum(x["control_only_signal"] for x in seeds),
    }


def analyze(batch_dir):
    folders = sorted(p for p in batch_dir.glob("regime_*") if p.is_dir())
    if not folders:
        raise ValueError(f"No regime directories under {batch_dir}")
    regimes = [audit_regime(folder) for folder in folders]
    return {
        "schema": "abio-e014-candidate-audit-v1",
        "source_batch": batch_dir.name,
        "analysis_type": "retrospective_event_level_audit",
        "regimes": regimes,
        "interpretation": {
            "verified_organizational_self_maintenance": False,
            "basis": "Not evaluated: event-level audit alone cannot establish spatial "
                     "self-regeneration or matched causal necessity.",
            "limitations": [
                "Candidate-step counts are serially correlated, not independent trials.",
                "Branched runs share a common pre-intervention state; they are not independent seeds.",
                "Branches may diverge after intervention and candidate identity may change.",
                "No complete state checkpoint or organization-specific event identity is exported.",
                "Positive control-only events do not constitute evidence of targeted rescue.",
                "No statistical significance claim is made from these descriptive differences.",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.batch_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"E014 candidate audit: {len(report['regimes'])} regimes; {args.out}")


if __name__ == "__main__":
    main()
