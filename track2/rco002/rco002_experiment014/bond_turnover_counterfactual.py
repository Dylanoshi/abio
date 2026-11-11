#!/usr/bin/env python3
"""E014 Phase 9: matched global bond-turnover interventions at step 543.

Reconstructs one E013 sham trajectory to the end of step 542, then varies only
the global bond-break probability either for step 543 alone (pulse) or from
543 through the run endpoint (sustained). This is a MECHANISTIC counterfactual,
not evidence of spontaneous organizational repair or RAF closure.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from short_horizon import load_sim, physical_hash


def target_bonded_ids(sim, s):
    target = s["fmembers"].get(s["target_flid"])
    if not target:
        return set()
    site_set = set(target["sites"])
    return {s["ids"][i] for edge in s["bonds"] if set(edge)<=site_set for i in edge}


def anchor_component(sim, state, anchor_id):
    location = next((site for site,pid in state["ids"].items() if pid==anchor_id),None)
    if location is None: return set()
    for sites in sim.components(state["cells"],state["bonds"]):
        if location in sites:
            return {state["ids"][site] for site in sites}
    return set()


def replay(sim, settings, seed=3, checkpoint=542, rates=(0.0, .002, .004, .018),
           end=600):
    a=argparse.Namespace(**settings)
    original_rate=float(a.bond_break)
    branch_at=int(a.steps*a.interrupt_fraction)
    if not branch_at<checkpoint<end<=a.steps:
        raise ValueError("Invalid checkpoint/end")
    if any(not 0<=float(rate)<=1 for rate in rates):
        raise ValueError("Bond-break rates must lie in [0,1]")
    s=sim.initialize(seed,a)
    ev=[];ln=[]
    for t in range(1,branch_at+1):
        sim.tick(s,seed,"common",t,a,ev,ln)
    sim.select_target(s,a,seed,ev,branch_at)
    if s["target_flid"] is None:
        raise ValueError("No target functional lineage selected")
    for t in range(branch_at+1,checkpoint+1):
        sim.tick(s,seed,"sham",t,a,ev,ln)
    group=s["fmembers"].get(s["target_flid"])
    if not group:
        raise ValueError("No tracked target at checkpoint")
    anchor_ids=target_bonded_ids(sim,s)
    if not anchor_ids:
        raise ValueError("Tracked target has no bonded constituents")
    # Select a stable ID from the entire connected organization as witness.
    central_id=min(anchor_ids)
    original_sites=set(group["sites"])
    original_bonds=sorted(
        [list(e) for e in s["bonds"] if set(e)<=original_sites]
    )
    initial_hash=physical_hash(s)
    branches={}
    for treatment in ("pulse","sustained"):
        for rate in rates:
            rate=float(rate)
            state=copy.deepcopy(s)
            if physical_hash(state)!=initial_hash:
                raise AssertionError("Starting physical state mismatch")
            per_step=[]
            initial=set(anchor_ids)
            for t in range(checkpoint+1,end+1):
                a_step=copy.copy(a)
                a_step.bond_break = rate if (t==checkpoint+1 or treatment=="sustained") else original_rate
                sim.tick(state,seed,"sham",t,a_step,[],[])
                tracked=state["fmembers"].get(state["target_flid"])
                members=anchor_component(sim,state,central_id)
                alive=sum(pid in state["ids"].values() for pid in initial)
                per_step.append({
                    "step":t,
                    "bond_break_rate":a_step.bond_break,
                    "target_tracked_size":len(tracked["ids"]) if tracked else 0,
                    "anchor_component_size":len(members),
                    "initial_ids_still_alive":alive,
                    "initial_ids_still_together":initial.issubset(members),
                    "strict_candidate":int(state["exact_rows"][-1]["strict_candidate"]),
                    "target_similarity":float(state["history"][-1]["target_functional_similarity"]),
                    "target_motifs_preserved":int(state["exact_rows"][-1]["exact_motif_preservation"]),
                })
            key=f"{treatment}_{rate:.4f}"
            first_target_absent=next((r["step"] for r in per_step
                                     if r["target_tracked_size"]==0),None)
            first_original_split=next((r["step"] for r in per_step
                                      if not r["initial_ids_still_together"]),None)
            branches[key]={
                "treatment":treatment,
                "bond_break_rate":rate,
                "first_target_absent_after_checkpoint":first_target_absent,
                "first_three_constituents_disconnected":first_original_split,
                "tracked_present_steps_after_checkpoint":sum(r["target_tracked_size"]>0 for r in per_step),
                "candidate_steps_after_checkpoint":sum(r["strict_candidate"] for r in per_step),
                "final_target_tracked_size":per_step[-1]["target_tracked_size"],
                "final_anchor_component_size":per_step[-1]["anchor_component_size"],
                "rows":per_step,
            }
    return {
        "schema":"abio-e014-bond-turnover-counterfactual-v1",
        "seed":seed,
        "checkpoint_step":checkpoint,
        "end_step":end,
        "original_bond_break_rate":original_rate,
        "initial_physical_hash":initial_hash,
        "selected_target_flid":s["target_flid"],
        "target_bonded_particle_ids":sorted(anchor_ids),
        "selected_witness_particle_id":central_id,
        "target_original_bond_sites":original_bonds,
        "branches":branches,
        "caveats":[
            "Global bond-break perturbation modifies the entire substrate, not only target bonds.",
            "A one-step rescue is an imposed intervention, not endogenous self-repair.",
            "This is a post-selected single-seed, matched counterfactual experiment.",
            "Fixed site-keyed random draws correlate branch outcomes.",
            "Functional lineage ID may not capture physically similar successor organizations.",
            "Original group constituent cohesion need not imply catalytic closure, self-maintenance or life.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",required=True,type=Path)
    p.add_argument("--settings",required=True,type=Path)
    p.add_argument("--seed",type=int,default=3)
    p.add_argument("--checkpoint",type=int,default=542)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--rates",nargs="+",type=float,default=[0,.002,.004,.018])
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    result=replay(load_sim(x.sim),json.loads(x.settings.read_text()),
                  seed=x.seed,checkpoint=x.checkpoint,rates=x.rates,end=x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "settings_sha256":hashlib.sha256(x.settings.read_bytes()).hexdigest(),
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "schema":result["schema"],
        "checkpoint":result["checkpoint_step"],
        "original_bond_break":result["original_bond_break_rate"],
        "target_original_bond_sites":result["target_original_bond_sites"],
        "by_regime":{key:{
            "first_target_absent":r["first_target_absent_after_checkpoint"],
            "first_original_split":r["first_three_constituents_disconnected"],
            "tracked_present_steps":r["tracked_present_steps_after_checkpoint"],
            "final_target_size":r["final_target_tracked_size"],
            "final_anchor_component_size":r["final_anchor_component_size"],
        } for key,r in result["branches"].items()},
        "out":str(x.out),
    },indent=2))


if __name__=="__main__":
    main()
