#!/usr/bin/env python3
"""E015 Phase 3: does a catalytic component's OWN activity sustain its field?

Same locally evolved seed/step-300 state, four counterfactual continuations:
all field deposits; no fresh deposits; only focal sources blocked; only focal
sources allowed. Catalysis and birth rules remain untouched in every arm.

Selection at checkpoint uses PAST catalytic activity only. The focal lineage
is a heuristic connected-component ID, not a pre-programmed organism.
"""
import argparse
import copy
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

from ablation import eligible_groups, group_outcomes, load_sim, physical_signature
from run import DEFAULTS

SCHEMA="abio-e015-source-dependent-regeneration-v1"
ARMS={
    "all":"all",
    "no_new_field":"none",
    "remove_focal_source":"nonfocal_only",
    "focal_source_only":"focal_only",
}

def choose_focal(state, checkpoint, lookback=40):
    """Predeclared ranking: prior realized catalytic births, then age/size/ID."""
    candidates=eligible_groups(state,min_age=30,min_size=3)
    past=Counter(e["producer_fid"] for e in state["motif_events"]
                 if checkpoint-lookback < e["step"] <= checkpoint
                 and e.get("producer_fid") is not None)
    if not candidates:
        return None, {"eligible":0,"focal_prior_births":0}
    # Highest recent catalytic activity, then age, size, lowest ID.
    chosen=max(candidates,key=lambda x:(
        past[x["fid"]],x["age_at_checkpoint"],x["size_at_checkpoint"],-x["fid"]))
    return chosen, {
        "eligible":len(candidates),
        "focal_prior_births":past[chosen["fid"]],
        "prior_window":[checkpoint-lookback+1,checkpoint],
        "ranking":"descending focal realized catalytic births, age, size; ascending fid",
    }


def focus_metrics(sim,state,focal):
    if not focal: return {"present":0,"motif_similarity":0.0,
                          "retained_ids":0,"founder_replaced":False,
                          "size":0,"near_field":0.0}
    entry=group_outcomes(state,[focal],0,sim)[0]
    current=state["fmembers"].get(focal["fid"])
    field=state["e015_field"]
    nearby=sum(field.get(i,0.0) for i in current["sites"])/len(current["sites"]) if current else 0.0
    return {
        "present":int(entry["present"]),
        "motif_similarity":entry["profile_similarity"],
        "retained_ids":entry["original_particle_ids_still_in_fid"],
        "founder_replaced":bool(current and
                              entry["original_particle_ids_still_in_fid"]==0),
        "size":entry["size"],
        "near_field":round(nearby,5),
    }


def evaluate(sim,params,seeds,checkpoint=300,end=600):
    a=argparse.Namespace(**params)
    if checkpoint<40 or end<=checkpoint or end>a.steps:
        raise ValueError("Invalid checkpoint/end")
    if len(set(seeds))!=len(seeds) or not seeds:
        raise ValueError("Duplicate/empty seeds")
    entries=[]
    for seed in seeds:
        base=sim.initialize(seed,a)
        events=[];lineages=[]
        for t in range(1,checkpoint+1):
            sim.tick(base,seed,"local",t,a,events,lineages)
        focal,selection=choose_focal(base,checkpoint)
        key=physical_signature(base)
        arms={}
        for name,policy in ARMS.items():
            state=copy.deepcopy(base)
            if physical_signature(state)!=key: raise AssertionError("Checkpoint state mismatch")
            state["e015_deposition_policy"]=policy
            state["e015_focal_fid"]=focal["fid"] if focal else None
            start_stats=Counter(state["e015_stats"])
            history=[]
            for t in range(checkpoint+1,end+1):
                sim.tick(state,seed,"local",t,a,[],[])
                metric=focus_metrics(sim,state,focal)
                history.append(dict(step=t,**metric))
            means={
                "mean_focal_present":round(statistics.mean(x["present"] for x in history),5),
                "mean_focal_motif_similarity":round(statistics.mean(x["motif_similarity"] for x in history),5),
                "mean_focal_retained_ids":round(statistics.mean(x["retained_ids"] for x in history),5),
                "mean_near_field":round(statistics.mean(x["near_field"] for x in history),5),
                "focal_present_steps":sum(x["present"] for x in history),
                "focal_motif_similarity_positive_steps":
                    sum(x["motif_similarity"]>0 for x in history),
                "first_focal_absent":next((x["step"] for x in history if not x["present"]),None),
                "postbranch_focal_catalytic_births":
                    state["e015_stats"]["catalytic_births_focal"]-start_stats["catalytic_births_focal"],
                "postbranch_nonfocal_catalytic_births":
                    state["e015_stats"]["catalytic_births_nonfocal"]-start_stats["catalytic_births_nonfocal"],
                "postbranch_focal_field_deposits":
                    state["e015_stats"]["deposited_births_focal"]-start_stats["deposited_births_focal"],
                "postbranch_nonfocal_field_deposits":
                    state["e015_stats"]["deposited_births_nonfocal"]-start_stats["deposited_births_nonfocal"],
                "postbranch_focal_blocked_deposits":
                    state["e015_stats"]["blocked_deposits_focal"]-start_stats["blocked_deposits_focal"],
                "postbranch_nonfocal_blocked_deposits":
                    state["e015_stats"]["blocked_deposits_nonfocal"]-start_stats["blocked_deposits_nonfocal"],
                "final_focal":history[-1],
                "timeline":history,
            }
            arms[name]=means
        entries.append({
            "seed":seed,"checkpoint_hash":key,
            "focal":focal,"selection":selection,
            "arms":arms,
            "focal_deposition_ablated_exposure":
                arms["remove_focal_source"]["postbranch_focal_blocked_deposits"]>0,
        })
        print("RUN",json.dumps({
            "seed":seed,
            "focal_fid":focal["fid"] if focal else None,
            "prior_focal_births":selection["focal_prior_births"],
            "focal_present_steps":{k:arms[k]["focal_present_steps"] for k in ARMS},
            "focal_deposits_suppressed":
                arms["remove_focal_source"]["postbranch_focal_blocked_deposits"],
            "other_deposits_suppressed":
                arms["focal_source_only"]["postbranch_nonfocal_blocked_deposits"],
        }),flush=True)
    keys=("mean_focal_present","mean_focal_motif_similarity","mean_focal_retained_ids",
          "mean_near_field","focal_present_steps","postbranch_focal_catalytic_births",
          "postbranch_focal_field_deposits","postbranch_nonfocal_field_deposits")
    summary={arm:{
        metric:round(statistics.mean(entry["arms"][arm][metric] for entry in entries),5)
        for metric in keys} for arm in ARMS}
    paired=[{
        "seed":e["seed"],"focal_fid":e["focal"]["fid"] if e["focal"] else None,
        "all_minus_remove_focal_present_steps":
            e["arms"]["all"]["focal_present_steps"]-
            e["arms"]["remove_focal_source"]["focal_present_steps"],
        "all_minus_no_new_present_steps":
            e["arms"]["all"]["focal_present_steps"]-
            e["arms"]["no_new_field"]["focal_present_steps"],
        "all_minus_focal_only_present_steps":
            e["arms"]["all"]["focal_present_steps"]-
            e["arms"]["focal_source_only"]["focal_present_steps"],
        "focal_suppression_exposed":e["focal_deposition_ablated_exposure"],
    } for e in entries]
    result={
        "schema":SCHEMA,
        "status":"exploratory, source-sensitive follow-up, no established life",
        "parameters":params,"seeds":list(seeds),"checkpoint":checkpoint,"end":end,
        "arms":ARMS,
        "predeclared_focal_selection":{
            "eligible":"fage >=30, size>=3, nonempty catalytic bond profile",
            "ranking":"past 40 step realized focal catalytic births desc, age desc, size desc, fid asc",
            "outcomes_blinded":True,
        },
        "individual":entries,"aggregate":summary,"paired_differences":paired,
        "limitations":[
            "Only the field-deposition effect is ablated; catalytic births remain active.",
            "The focusing intervention is experimenter-chosen, not an evolved life process.",
            "A focal source is classified by a heuristic functional ID assigned before the birth event.",
            "A lineage split or changed ID can cause source reassignment and apparent focal extinction.",
            "Focal and nonfocal deposit schedules are not number- or location-matched.",
            "Past catalytic births may be zero even for an eligible motif-bearing component.",
            "If focal deposit suppression never actually occurs, its comparison has no mechanistic exposure.",
            "All paired branches share the same initial state and stochastic schedule.",
            "Feedback law remains a designed substrate property, not spontaneously invented machinery.",
            "No claims of RAF closure, autonomous self-maintenance or reproduction.",
        ]
    }
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--checkpoint",type=int,default=300)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--seeds",nargs="+",type=int,default=list(range(12)))
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    sim=load_sim(x.sim)
    params=dict(DEFAULTS,steps=max(600,x.end))
    result=evaluate(sim,params,x.seeds,x.checkpoint,x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "driver_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({
        "schema":result["schema"],
        "seeds":result["seeds"],
        "focal_deposition_suppression_exposed_seeds":
            sum(e["focal_deposition_ablated_exposure"] for e in result["individual"]),
        "aggregate":result["aggregate"],
        "paired_differences":result["paired_differences"],
        "out":str(x.out),
    },indent=2))


if __name__=="__main__":
    main()
