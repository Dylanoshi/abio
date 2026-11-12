#!/usr/bin/env python3
"""E015 Phase 2: matched interruption of spatially coupled bond stabilization.

Run initial substrate under local-feedback rules to a fixed checkpoint, copy
exact physical/field state, then continue: local, disabled, spatially shuffled.
The pre-intervention history is identical within seed. No target-specific action.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

from run import DEFAULTS

MODES=("local","disabled","shuffled")
SCHEMA="abio-e015-spatial-feedback-ablation-v1"


def load_sim(path):
    spec=importlib.util.spec_from_file_location("e015_ablation_sim",str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def physical_signature(state):
    import hashlib
    data=json.dumps({
        "cells":sorted(state["cells"].items()),
        "ids":sorted(state["ids"].items()),
        "bonds":sorted([list(e) for e in state["bonds"]]),
        "nutrient":sorted(state["nutrient"]),
        "field":sorted(state["e015_field"].items()),
    },sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()


def eligible_groups(state, min_age=30, min_size=3):
    """Existing post-formation functional lineages selected without using outcomes."""
    result=[]
    for fid,group in state["fmembers"].items():
        if len(group["ids"])>=min_size and state["fages"].get(fid,0)>=min_age and group["profile"]:
            result.append({
                "fid":fid,
                "age_at_checkpoint":state["fages"][fid],
                "size_at_checkpoint":len(group["ids"]),
                "profile_at_checkpoint":dict(sorted(group["profile"].items())),
                "checkpoint_particle_ids":sorted(group["ids"]),
            })
    return sorted(result,key=lambda g:(-g["age_at_checkpoint"],-g["size_at_checkpoint"],g["fid"]))


def group_outcomes(state, originals, step, sim):
    active={fid:group for fid,group in state["fmembers"].items()}
    all_ids=set(state["ids"].values())
    outs=[]
    for orig in originals:
        g=active.get(orig["fid"])
        initial=set(orig["checkpoint_particle_ids"])
        retained=len(initial & set(g["ids"])) if g else 0
        # Similarity is descriptive, since original target may have split.
        simval=sim.profile_similarity(g["profile"],orig["profile_at_checkpoint"]) if g else 0.0
        outs.append({
            "fid":orig["fid"],
            "present":bool(g),
            "size":len(g["ids"]) if g else 0,
            "profile_similarity":round(simval,4),
            "original_particle_ids_alive":len(initial&all_ids),
            "original_particle_ids_still_in_fid":retained,
        })
    return outs


def run(sim,parameters,seeds,checkpoint,end):
    a=argparse.Namespace(**parameters)
    if checkpoint<=0 or end<=checkpoint or end>a.steps: raise ValueError("Invalid checkpoint/end")
    all_records=[]
    for seed in seeds:
        root=sim.initialize(seed,a)
        ev=[];lineages=[]
        for t in range(1,checkpoint+1):
            sim.tick(root,seed,"local",t,a,ev,lineages)
        originals=eligible_groups(root)
        signature=physical_signature(root)
        modes={}
        for mode in MODES:
            branch=copy.deepcopy(root)
            if physical_signature(branch)!=signature:
                raise AssertionError("Initial state mismatch")
            timeline=[]
            for t in range(checkpoint+1,end+1):
                sim.tick(branch,seed,mode,t,a,[],[])
                tracked=group_outcomes(branch,originals,t,sim)
                timeline.append({
                    "step":t,
                    "original_fids_present":sum(x["present"] for x in tracked),
                    "original_fids_with_original_motif":
                        sum(x["present"] and x["profile_similarity"]>0 for x in tracked),
                    "original_fids_with_some_checkpoint_particles":
                        sum(x["original_particle_ids_still_in_fid"]>0 for x in tracked),
                    "mean_bonds":len(branch["bonds"]),
                })
            # Count matched, checkpoint-selected functional identities at
            # each post-intervention step; report their fate independently
            # of subsequent newly generated components.
            modes[mode]={
                "checkpoint_group_count":len(originals),
                "mean_original_fids_present":round(statistics.mean(x["original_fids_present"] for x in timeline),3),
                "mean_original_motifs_present":round(statistics.mean(x["original_fids_with_original_motif"] for x in timeline),3),
                "mean_original_fids_with_initial_particles":round(statistics.mean(x["original_fids_with_some_checkpoint_particles"] for x in timeline),3),
                "mean_bonds_postbranch":round(statistics.mean(x["mean_bonds"] for x in timeline),3),
                "final_checkpoint_group_fates":group_outcomes(branch,originals,end,sim),
                "timeline":timeline,
                "postbranch_break_trials":branch["e015_stats"]["break_trials"]-root["e015_stats"]["break_trials"],
                "postbranch_exposed_trials":branch["e015_stats"]["exposed_trials"]-root["e015_stats"]["exposed_trials"],
                "postbranch_prevented_breaks":branch["e015_stats"]["prevented_breaks"]-root["e015_stats"]["prevented_breaks"],
            }
        entry={
            "seed":seed,"checkpoint_physical_field_hash":signature,
            "checkpoint_groups":originals,"by_mode":modes,
        }
        all_records.append(entry)
        print("RUN",json.dumps({
            "seed":seed,"checkpoint_groups":len(originals),
            "mean_fids_present":{m:modes[m]["mean_original_fids_present"] for m in MODES},
            "postbranch_exposed":{m:modes[m]["postbranch_exposed_trials"] for m in MODES}
        }),flush=True)
    aggregate={
        mode:{
            key:round(statistics.mean(rec["by_mode"][mode][key] for rec in all_records),4)
            for key in ("mean_original_fids_present","mean_original_motifs_present",
                        "mean_original_fids_with_initial_particles","mean_bonds_postbranch",
                        "postbranch_exposed_trials","postbranch_prevented_breaks")
        }
        for mode in MODES
    }
    return {
        "schema":SCHEMA,
        "parameters":parameters,
        "seeds":list(seeds),
        "checkpoint":checkpoint,"end":end,
        "conditions":{
            "local":"unchanged ongoing locally coupled feedback",
            "disabled":"continue recording catalytic field, but turn off its effect on bond break threshold",
            "shuffled":"continue effect after spatially redistributing field strengths across lattice each tick"
        },
        "prespecified_selection":{
            "checkpoint":checkpoint,"min_age":30,"min_size":3,
            "catalytic_profile_required":True,
            "group_identity":"pre-existing heuristic functional ID; splitting can terminate it"
        },
        "records":all_records,
        "aggregate":aggregate,
        "limitations":[
            "Original functional IDs are heuristic, not validated individual organisms.",
            "Groups are selected from the same checkpoint without looking at post-checkpoint outcomes.",
            "Disabled and shuffled treatments change global field coupling, not only selected groups.",
            "The designed feedback law is external and no energy/cost conservation is imposed.",
            "All post-branch comparisons within a seed share past state and random draws.",
            "More persistent motifs do not prove self-maintenance, RAF closure or heredity."
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--seeds",nargs="+",type=int,default=list(range(12)))
    p.add_argument("--checkpoint",type=int,default=300)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    if len(set(x.seeds))!=len(x.seeds) or x.end<=x.checkpoint:
        p.error("Invalid seed list or checkpoint window")
    params=dict(DEFAULTS,steps=max(600,x.end))
    result=run(load_sim(x.sim),params,x.seeds,x.checkpoint,x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "driver_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({
        "schema":SCHEMA,
        "seeds":result["seeds"],
        "checkpoint":x.checkpoint,
        "aggregate":result["aggregate"],
        "out":str(x.out)
    },indent=2))


if __name__=="__main__":
    main()
