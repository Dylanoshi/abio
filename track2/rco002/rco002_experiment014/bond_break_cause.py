#!/usr/bin/env python3
"""E014 phase 8: cause-level audit of target bond loss at simulation step 543.

Read-only matched reconstruction except an opt-in instrumentation hook:
captures the original RNG draw when an existing bond is tested for breakage.
No transition rules, random streams, or production E011 code are changed.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from active_control_run import load_schedule
from short_horizon import load_sim, physical_hash


def target_edges(s):
    target = s["fmembers"].get(s["target_flid"])
    if not target:
        return []
    sites = target["sites"]
    return [
        {"sites": list(edge), "particle_ids": sorted([s["ids"][p] for p in edge])}
        for edge in sorted(s["bonds"])
        if set(edge) <= sites
    ]


def analyze_step_543(sim, s, seed, mode, a):
    before_edges = target_edges(s)
    all_before_bonds = set(s["bonds"])
    before_ids = {str(pid): pos for pos,pid in s["ids"].items()}
    trace = []
    s["e014_trace_bonds"] = trace
    s["e014_trace_step"] = 543
    sim.tick(s, seed, mode, 543, a, [], [])
    s.pop("e014_trace_bonds", None)
    s.pop("e014_trace_step", None)
    after_bonds = set(s["bonds"])
    after_ids = {str(pid): pos for pos,pid in s["ids"].items()}
    detail = []
    for bond in before_edges:
        e = tuple(bond["sites"])
        events = [x for x in trace if x["sites"] == bond["sites"]]
        pids = bond["particle_ids"]
        detail.append({
            **bond,
            "present_after_step": e in after_bonds,
            "constituent_survival": {str(pid):str(pid) in after_ids for pid in pids},
            "break_trials": events,
            "explicit_break_trial_succeeded": any(x["broken"] for x in events),
            "classification": (
                "still_bonded" if e in after_bonds
                else "explicit_stochastic_break" if any(x["broken"] for x in events)
                else "not_explained_by_observed_break_trial"
            ),
        })
    return {
        "pre_step_target_edges": before_edges,
        "target_edges": detail,
        "global_bonds_before": len(all_before_bonds),
        "global_bonds_after": len(after_bonds),
        "global_particle_count_before": len(before_ids),
        "global_particle_count_after": len(after_ids),
        "total_break_trials_during_step": len(trace),
        "total_successful_break_trials_during_step":sum(x["broken"] for x in trace),
        "target_present_after": s["target_flid"] in s["fmembers"],
        "target_size_after":len(s["fmembers"].get(s["target_flid"],{}).get("ids",[])),
    }


def audit(sim, settings, preflight, seed, start):
    a = argparse.Namespace(**settings)
    branch_at = int(a.steps*a.interrupt_fraction)
    if not branch_at < start <= 543 <= a.steps:
        raise ValueError("Invalid replay window")
    base = sim.initialize(seed,a)
    events=[];lineages=[]
    for t in range(1, branch_at+1):
        sim.tick(base,seed,"common",t,a,events,lineages)
    sim.select_target(base,a,seed,events,branch_at)
    for t in range(branch_at+1,start):
        sim.tick(base,seed,"sham",t,a,events,lineages)
    initial_hash=physical_hash(base)
    schedule=load_schedule(preflight)
    modes={}
    for mode in ("sham","target_block","offtarget_block"):
        s=copy.deepcopy(base)
        s["e014_control_schedule"]=schedule if mode=="offtarget_block" else {}
        if physical_hash(s)!=initial_hash: raise AssertionError("Initial physical state mismatch")
        ev=[];ln=[]
        for t in range(start,543):
            sim.tick(s,seed,mode,t,a,ev,ln)
        modes[mode]=analyze_step_543(sim,s,seed,mode,a)
    return {
        "schema":"abio-e014-bond-break-cause-audit-v1",
        "seed":seed,
        "intervention_start":start,
        "inspection_step":543,
        "initial_matched_physical_hash":initial_hash,
        "by_mode":modes,
        "interpretation":{
            "verified_self_maintenance":False,
            "notes":[
                "Trial events report actual sampled random draws for present bonds.",
                "Bond loss and shared stochastic scheduling do not establish independent mechanism replication.",
                "An explicit break event is not proof that local catalysis could not repair the bond.",
                "This is one post-selected regime-seed trajectory and does not establish RAF closure.",
            ],
        },
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",required=True,type=Path)
    p.add_argument("--settings",required=True,type=Path)
    p.add_argument("--preflight",required=True,type=Path)
    p.add_argument("--seed",type=int,default=3)
    p.add_argument("--start",type=int,default=513)
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    result=audit(load_sim(x.sim),json.loads(x.settings.read_text()),
                 json.loads(x.preflight.read_text()),x.seed,x.start)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "settings_sha256":hashlib.sha256(x.settings.read_bytes()).hexdigest(),
        "preflight_sha256":hashlib.sha256(x.preflight.read_bytes()).hexdigest(),
    }
    x.out.parent.mkdir(parents=True, exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "schema":result["schema"],
        "by_mode":{mode:{
            "pre_step_target_bonds":len(r["pre_step_target_edges"]),
            "bond_fates":[{
                "particle_ids":e["particle_ids"],
                "sites":e["sites"],
                "classification":e["classification"],
                "break_trials":e["break_trials"]
            } for e in r["target_edges"]],
            "global_bonds_before":r["global_bonds_before"],
            "global_bonds_after":r["global_bonds_after"],
            "target_size_after":r["target_size_after"],
        } for mode,r in result["by_mode"].items()},
        "output":str(x.out),
    },indent=2))


if __name__=="__main__":
    main()
