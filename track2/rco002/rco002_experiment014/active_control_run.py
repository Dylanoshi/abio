#!/usr/bin/env python3
"""E014 phase 5: execute a scheduled off-target active control.

Exploratory retrospective-control design, NOT independent confirmation.
Uses isolated E014 simulator variant; production runner remains unchanged.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from short_horizon import load_sim, physical_hash

MODES=("sham","target_block","offtarget_block")

def load_schedule(preflight):
    if preflight.get("schema")!="abio-e014-active-control-preflight-v1":
        raise ValueError("Unexpected preflight schema")
    if not preflight.get("matching_possible_at_each_target_step"):
        raise ValueError("Preflight did not identify all exact-step matches")
    selected=preflight.get("proposed_control_events",[])
    if not selected: raise ValueError("No controls scheduled")
    schedule={}
    for entry in selected:
        c=entry["candidate_control"]
        t=int(c["step"])
        if t!=int(entry["target_suppression"]["step"]):
            raise ValueError("Unmatched suppression step")
        pair=tuple(sorted(map(int,c["catalyst_pair"])))
        if len(pair)!=2 or pair[0]==pair[1]:
            raise ValueError("Invalid catalyst pair")
        schedule.setdefault(t,set()).add(pair)
    return schedule

def run(sim,settings,seed,start,end,preflight,expected_sham_steps=None):
    a=argparse.Namespace(**settings)
    branch_at=int(a.steps*a.interrupt_fraction)
    if not branch_at<start<=end<=a.steps: raise ValueError("Invalid window")
    schedule=load_schedule(preflight)
    if any(not start<=t<=end for t in schedule):
        raise ValueError("Control schedule outside replay window")
    base=sim.initialize(seed,a)
    events,lineages=[],[]
    for t in range(1,branch_at+1):
        sim.tick(base,seed,"common",t,a,events,lineages)
    sim.select_target(base,a,seed,events,branch_at)
    for t in range(branch_at+1,start):
        sim.tick(base,seed,"sham",t,a,events,lineages)
    start_hash=physical_hash(base)
    branches={}
    for mode in MODES:
        state=copy.deepcopy(base)
        state["e014_control_schedule"]=schedule if mode=="offtarget_block" else {}
        if physical_hash(state)!=start_hash:
            raise AssertionError("Initial physical state mismatch")
        ev,ln=[],[]
        suppressed=[]
        step_rows=[]
        for t in range(start,end+1):
            prev=len(ev)
            sim.tick(state,seed,mode,t,a,ev,ln)
            found=state["exact_rows"][-1]
            history=state["history"][-1]
            just_suppressed=[dict(e) for e in ev[prev:] if e["event"]=="suppressed"]
            suppressed.extend(just_suppressed)
            step_rows.append({
                "step":t,
                "physical_hash":physical_hash(state),
                "strict_candidate":int(found["strict_candidate"]),
                "founder_replacement":int(found["founder_replacement"]),
                "exact_motif_preservation":int(found["exact_motif_preservation"]),
                "recent_regenerative_incorporations":int(found["recent_regenerative_incorporations"]),
                "target_functional_similarity":float(history["target_functional_similarity"]),
                "target_functional_size":int(history["target_functional_size"]),
                "target_functional_age":int(history["target_functional_age"]),
                "suppressed":just_suppressed,
            })
        branches[mode]={
            "candidate_steps":sum(r["strict_candidate"] for r in step_rows),
            "suppressed_total":len(suppressed),
            "suppression_steps":[int(e["step"]) for e in suppressed],
            "suppressed_events":suppressed,
            "rows":step_rows,
            "final_similarity":step_rows[-1]["target_functional_similarity"],
            "final_size":step_rows[-1]["target_functional_size"],
            "final_motif_preserved":step_rows[-1]["exact_motif_preservation"],
            "final_regenerative_incorporations":step_rows[-1]["recent_regenerative_incorporations"],
        }
    sham=branches["sham"]
    compare={}
    for mode in MODES[1:]:
        other=branches[mode]
        steps=[x["step"] for x,y in zip(sham["rows"],other["rows"])
               if x["physical_hash"]!=y["physical_hash"]]
        compare[mode]={
            "first_physical_divergence":steps[0] if steps else None,
            "divergent_steps":len(steps),
            "candidate_difference":sham["candidate_steps"]-other["candidate_steps"],
            "exposure_verified":other["suppressed_total"]>0,
        }
    expected_events=[(t,pair) for t,pairs in schedule.items() for pair in pairs]
    realized_pairs=[(int(e["step"]),tuple(sorted([int(e["catalyst_a"]),int(e["catalyst_b"])])))
                    for e in branches["offtarget_block"]["suppressed_events"]]
    return {
        "schema":"abio-e014-active-control-intervention-v1",
        "provenance":{"seed":seed,"start":start,"end":end,
                      "initial_physical_hash":start_hash,"original_branch_step":branch_at},
        "historical_sham_reproduced":(
            None if expected_sham_steps is None
            else sham["candidate_steps"]==expected_sham_steps),
        "planned_offtarget_suppressions":len(expected_events),
        "realized_scheduled_offtarget_suppressions":sum(x in realized_pairs for x in expected_events),
        "all_offtarget_events_realized":all(x in realized_pairs for x in expected_events),
        "branches":branches,
        "comparisons":compare,
        "interpretation":{
            "verified_self_maintenance":False,
            "note":"Exposure-matched in event count and timing only if explicitly verified. "
                   "Not matched for spatial effects, local chemistry or causal centrality.",
            "caveats":[
                "Control events were retrospectively chosen after inspecting the sham/target histories.",
                "Target and off-target inhibition may alter future reaction opportunities.",
                "Outcome is based on one previously selected seed, not independent replication.",
                "A tracked functional lineage is not proof of an autopoietic individual or formal RAF.",
            ],
        },
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,required=True)
    p.add_argument("--settings",type=Path,required=True)
    p.add_argument("--preflight",type=Path,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--start",type=int,required=True)
    p.add_argument("--end",type=int,required=True)
    p.add_argument("--expected-sham-steps",type=int)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=run(load_sim(a.sim),json.loads(a.settings.read_text()),a.seed,a.start,a.end,
               json.loads(a.preflight.read_text()),a.expected_sham_steps)
    result["provenance"]["sim_sha256"]=hashlib.sha256(a.sim.read_bytes()).hexdigest()
    result["provenance"]["preflight_sha256"]=hashlib.sha256(a.preflight.read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "historical_sham_reproduced":result["historical_sham_reproduced"],
        "planned_offtarget_suppressions":result["planned_offtarget_suppressions"],
        "realized_scheduled_offtarget_suppressions":result["realized_scheduled_offtarget_suppressions"],
        "all_offtarget_events_realized":result["all_offtarget_events_realized"],
        "by_mode":{mode:{
            "suppressed":x["suppressed_total"],
            "candidate_steps":x["candidate_steps"],
            "final_similarity":x["final_similarity"],
            "final_size":x["final_size"],
            "final_motif_preserved":x["final_motif_preserved"],
            "final_regenerative_incorporations":x["final_regenerative_incorporations"],
        } for mode,x in result["branches"].items()},
        "first_divergence":{mode:x["first_physical_divergence"]
                            for mode,x in result["comparisons"].items()},
        "output":str(a.out),
    },indent=2))

if __name__=="__main__":
    main()
