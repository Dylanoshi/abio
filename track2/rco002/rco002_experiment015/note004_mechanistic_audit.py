#!/usr/bin/env python3
"""E015 Note 004 final mechanistic audit: descriptive, matched-arm dynamics.

All parameter choices and metrics defined in the README BEFORE new results.
Replays historical held-out seeds 12-23, not new replication. Tracks:
  * material replacement and functional profile continuity
  * original and new members, catalytic productivity
  * bond turnover and bridge-internal bond survival
  * source-specific deposits and protection at bridge sites
  * near-resource occupancy (not metabolic uptake)
  * bond-break risk-set exposure / same-draw counterfactual protection
The measurement hook is observational only and is checked against the
uncoupled, uninstrumented original local sham dynamics.
"""
import argparse
import copy
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

from ablation import load_sim, physical_signature
from dynamic_source_ablation import MaterialBridge
from run import DEFAULTS
from source_ablation import choose_focal

SCHEMA="abio-e015-note004-mechanistic-audit-v1"
ARMS={"sham":"all","self_removed":"dynamic_self_off"}
EXPLORATORY_SEEDS=list(range(12,24))

class Mechanics(MaterialBridge):
    """Instrument a single dynamically tracked material bridge, per arm."""
    def __init__(self,focal,size):
        super().__init__(focal)
        self.side=size
        self.prior_ids=set(self.ids)
        self.prior_bonds=set()
        self.current_bonds=set()
        self.cumulative_entered=0
        self.cumulative_exited=0
        self.pretrial=Counter()
        self.per_tick=Counter()
        self.protective_events=[]
        self.monitor=[]

    def __call__(self,event,**kw):
        if event=="field_ready":
            self.per_tick=Counter()
        elif event=="bond_trial":
            self.bond_trial(kw)
        elif event=="after_identify":
            self.update_bridge(kw["s"],kw["t"])
        elif event=="catalytic_event":
            self.observe_birth(kw)
        elif event=="tick_end":
            self.finish(kw["s"],kw["t"])

    def bond_trial(self,kw):
        # At bond-trial time the current target is still the preceding tick's
        # material bridge. Only measure a bond if BOTH endpoint PIDs were
        # present in the previous material-bridge component.
        s=kw["s"]
        ids=set(kw["particle_ids"])
        if not self.present or not ids<=self.prior_ids:return
        x,y=kw["sites"]
        field=(s["e015_last_field"].get(x,0.)+
               s["e015_last_field"].get(y,0.))/2.
        self.per_tick["focal_bond_trials"]+=1
        if field>.01:self.per_tick["focal_field_exposed_trials"]+=1
        if kw["draw"]<kw["threshold"]:
            self.per_tick["focal_actual_break_trials"]+=1
        if kw["threshold"]<=kw["draw"]<kw["baseline"]:
            self.per_tick["focal_baseline_avoided_break_trials"]+=1
            if len(self.protective_events)<50:
                self.protective_events.append(dict(
                    step=kw["t"],sites=list(kw["sites"]),
                    particle_ids=list(kw["particle_ids"]),
                    draw=kw["draw"],threshold=kw["threshold"],
                    baseline=kw["baseline"],field=field))
        self.per_tick["field_sum_at_trial"]+=field

    def update_bridge(self,s,t):
        old=set(self.ids)
        self.update(s,t)
        if self.present:
            entered=len(self.ids-old)
            departed=len(old-self.ids)
            self.cumulative_entered+=entered
            self.cumulative_exited+=departed
            self.per_tick["entered"]=entered
            self.per_tick["departed"]=departed
        else:
            self.per_tick["departed"]=len(old)
            self.cumulative_exited+=len(old)
        self.prior_ids=set(self.ids)
        edges=set()
        for x,y in s["bonds"]:
            if x in self.sites and y in self.sites:
                edges.add(tuple(sorted((s["ids"][x],s["ids"][y]))))
        self.current_bonds=edges
        self.per_tick["internal_bonds"]=len(edges)
        self.per_tick["bond_formed_or_gained"]=len(edges-self.prior_bonds)
        self.per_tick["bond_lost"]=len(self.prior_bonds-edges)
        self.prior_bonds=edges

    def observe_birth(self,kw):
        self.birth(kw)
        if self.present and kw["producer_fid"]==self.current_fid:
            self.per_tick["focal_births"]+=1
            if kw["deposited"]:self.per_tick["focal_deposits"]+=1
            else:self.per_tick["focal_deposits_blocked"]+=1
        elif kw["deposited"] and self.present:
            if any(site in self.sites for site in kw["sites"]):
                self.per_tick["nonfocal_deposits_direct_at_focal_site"]+=1

    def finish(self,s,t):
        self.record(s,t)
        row=self.history[-1]
        nearby=set(self.sites)
        for i in list(self.sites):
            nearby.update(self.neighbors(i))
        resource_near=sum(i in s["nutrient"] for i in nearby) if nearby else 0
        field_at_bridge=[s["e015_field"].get(i,0.) for i in self.sites]
        self.monitor.append({
            "step":t,
            "bridge_present":row["bridge_present"],
            "bridge_fid":row["bridge_fid"],
            "bridge_size":row["bridge_size"],
            "profile_similarity_to_checkpoint":row["functional_similarity_to_checkpoint"],
            "active_motifs":row["active_motifs"],
            "original_ids_in_bridge":row["original_ids_in_bridge"],
            "bridge_internal_bonds":self.per_tick["internal_bonds"],
            "internal_bond_gain":self.per_tick["bond_formed_or_gained"],
            "internal_bond_loss":self.per_tick["bond_lost"],
            "material_entered":self.per_tick["entered"],
            "material_departed":self.per_tick["departed"],
            "focal_catalytic_births":self.per_tick["focal_births"],
            "focal_field_deposits":self.per_tick["focal_deposits"],
            "focal_deposits_blocked":self.per_tick["focal_deposits_blocked"],
            "other_deposits_at_focal_sites":self.per_tick[
                "nonfocal_deposits_direct_at_focal_site"],
            "field_at_focal_mean":round(statistics.mean(field_at_bridge),7)
                if field_at_bridge else 0.,
            "nutrient_sites_in_bridge_and_one_hop":resource_near,
            "focal_bond_break_trials":self.per_tick["focal_bond_trials"],
            "focal_bond_exposed_trials":self.per_tick["focal_field_exposed_trials"],
            "focal_bond_actual_break_trials":self.per_tick["focal_actual_break_trials"],
            "focal_bond_baseline_avoided_break_trials":
                self.per_tick["focal_baseline_avoided_break_trials"],
            "field_sum_at_focal_bond_trials":round(
                self.per_tick["field_sum_at_trial"],7),
        })

    def neighbors(self,i):
        x,y=i%self.side,i//self.side
        if x:yield i-1
        if x+1<self.side:yield i+1
        if y:yield i-self.side
        if y+1<self.side:yield i+self.side

def summarize(rows,first_lost):
    total=len(rows)
    present=[r for r in rows if r["bridge_present"]]
    f=lambda key:sum(r[key] for r in rows)
    avg=lambda key:(sum(r[key] for r in present)/len(present)
                    if present else 0.)
    return {
        "bridge_present_steps":len(present),
        "first_loss":first_lost,
        "mean_motif_similarity_all_steps":round(
            statistics.mean(r["profile_similarity_to_checkpoint"]
                            for r in rows),5),
        "mean_motif_similarity_when_present":round(
            avg("profile_similarity_to_checkpoint"),5),
        "mean_active_motifs_when_present":round(avg("active_motifs"),5),
        "mean_size_when_present":round(avg("bridge_size"),5),
        "total_material_entered":f("material_entered"),
        "total_material_departed":f("material_departed"),
        "total_internal_bond_gains":f("internal_bond_gain"),
        "total_internal_bond_losses":f("internal_bond_loss"),
        "total_focal_catalytic_births":f("focal_catalytic_births"),
        "total_self_field_deposits":f("focal_field_deposits"),
        "total_self_deposits_blocked":f("focal_deposits_blocked"),
        "total_other_deposits_at_focal_sites":f("other_deposits_at_focal_sites"),
        "mean_field_when_present":round(avg("field_at_focal_mean"),5),
        "mean_near_resource_count_when_present":
            round(avg("nutrient_sites_in_bridge_and_one_hop"),5),
        "focal_bond_break_trials":f("focal_bond_break_trials"),
        "focal_bond_exposed_trials":f("focal_bond_exposed_trials"),
        "focal_bond_actual_break_trials":f("focal_bond_actual_break_trials"),
        "focal_baseline_avoided_break_trials":
            f("focal_bond_baseline_avoided_break_trials"),
        "mean_field_per_focal_break_trial":
            round(f("field_sum_at_focal_bond_trials")/
                  f("focal_bond_break_trials"),6)
            if f("focal_bond_break_trials") else 0.,
        "original_retained_at_end":
            rows[-1]["original_ids_in_bridge"] if rows else 0,
        "bridge_end_present":bool(rows[-1]["bridge_present"]) if rows else False,
    }

def paired_audit(sim,params,seeds,checkpoint=300,end=600,verify_sham=True):
    a=argparse.Namespace(**params)
    if checkpoint<40 or not checkpoint<end<=a.steps:
        raise ValueError("Invalid checkpoint/end")
    if not seeds or len(seeds)!=len(set(seeds)):
        raise ValueError("Seeds must be unique and nonempty")
    records=[]
    for seed in seeds:
        root=sim.initialize(seed,a)
        for t in range(1,checkpoint+1):
            sim.tick(root,seed,"local",t,a,[],[])
        selected,criterion=choose_focal(root,checkpoint)
        checkpoint_hash=physical_signature(root)
        arms={}
        for arm,policy in ARMS.items():
            state=copy.deepcopy(root)
            if physical_signature(state)!=checkpoint_hash:
                raise AssertionError("Checkpoint mismatch")
            trace=Mechanics(selected,a.size)
            state["e015_audit_hook"]=trace
            state["e015_deposition_policy"]=policy
            for t in range(checkpoint+1,end+1):
                sim.tick(state,seed,"local",t,a,[],[])
            state.pop("e015_audit_hook")
            summary=summarize(trace.monitor,trace.first_lost)
            arms[arm]={
                "summary":summary,
                "first_50_prevented_bond_breaks":trace.protective_events,
                "timeline":trace.monitor,
                "final_physics_hash":physical_signature(state),
                "ambiguous_split_steps":trace.ambiguous_steps,
                "functional_id_changes":trace.fid_changes,
            }
            if arm=="sham" and verify_sham:
                baseline=copy.deepcopy(root)
                for t in range(checkpoint+1,end+1):
                    sim.tick(baseline,seed,"local",t,a,[],[])
                if physical_signature(baseline)!=physical_signature(state):
                    raise AssertionError(f"Instrumentation changed sham physics on seed {seed}")
        comparison={
            "sham_minus_self_removed_steps":
                arms["sham"]["summary"]["bridge_present_steps"]-
                arms["self_removed"]["summary"]["bridge_present_steps"],
            "sham_minus_self_removed_motif_similarity":
                round(arms["sham"]["summary"]["mean_motif_similarity_all_steps"]-
                      arms["self_removed"]["summary"]["mean_motif_similarity_all_steps"],5),
        }
        records.append({
            "seed":seed,
            "checkpoint_hash":checkpoint_hash,
            "checkpoint_selection":selected,
            "selection_evidence":criterion,
            "arms":arms,"paired":comparison,
        })
        print("RUN",json.dumps({
            "seed":seed,
            "duration":{arm:arms[arm]["summary"]["bridge_present_steps"] for arm in ARMS},
            "delta":comparison["sham_minus_self_removed_steps"],
            "births":{arm:arms[arm]["summary"]["total_focal_catalytic_births"]
                      for arm in ARMS},
            "material_turnover":{arm:[
                arms[arm]["summary"]["total_material_entered"],
                arms[arm]["summary"]["total_material_departed"]] for arm in ARMS},
            "break_trials":{arm:arms[arm]["summary"]["focal_bond_break_trials"]
                            for arm in ARMS},
            "sham_physics_verified":verify_sham,
        }),flush=True)
    features=(
        "bridge_present_steps",
        "mean_motif_similarity_all_steps",
        "mean_motif_similarity_when_present",
        "mean_active_motifs_when_present",
        "total_material_entered","total_material_departed",
        "total_internal_bond_gains","total_internal_bond_losses",
        "total_focal_catalytic_births",
        "mean_field_when_present",
        "focal_bond_break_trials","focal_bond_exposed_trials",
        "focal_bond_actual_break_trials",
        "focal_baseline_avoided_break_trials",
        "mean_near_resource_count_when_present",
    )
    aggregate={arm:{k:round(statistics.mean(
        r["arms"][arm]["summary"][k] for r in records),5)
        for k in features} for arm in ARMS}
    effects=[r["paired"]["sham_minus_self_removed_steps"] for r in records]
    return {
        "schema":SCHEMA,
        "status":"descriptive mechanistic audit of previously observed cohort; not confirmation",
        "parameters":params,"seeds":list(seeds),
        "checkpoint":checkpoint,"end":end,
        "selection":"Precheckpoint 40-step birth activity, then age, size, ID. No retuning.",
        "groups":"zero, positive and negative effects retained in same dataset; no outcome-based filtering",
        "records":records,"aggregate_mean":aggregate,
        "paired_duration_effects":effects,
        "limitations":[
            "This replays the SAME prior cohort; any feature associations are explanatory hypotheses, not independent replication.",
            "Material-bridge tracing is a one-successor overlap heuristic, not validated functional identity.",
            "Per-tick bond gain/loss includes group merger and membership reclassification, not just physical formation/breakage.",
            "Material entry and exit are observed between identify() calls and are not independently proven regenerative incorporation.",
            "Nutrient near the component measures resource availability, not resource use or energetic closure.",
            "Protective field at selected sites may be supplied by nonfocal catalysis; it is NOT self-only provenance.",
            "Baseline avoided break-trial count is same-draw fixed-state accounting, not a dynamic causal outcome.",
            "Post-intervention fields and organizational features are both treatment effects; correlating them with survival is not baseline causal prediction.",
            "A trace with no matched material component ends permanently; total turnover or branching can create a false loss.",
            "Repeat ticks/trials within a seed are serially correlated; treat seed as unit of replication.",
            "Does not establish RAF closure, self-maintenance, reproduction or computational abiogenesis.",
        ],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--checkpoint",type=int,default=300)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--seeds",nargs="+",type=int,default=EXPLORATORY_SEEDS)
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    params=dict(DEFAULTS,steps=max(600,x.end))
    sim=load_sim(x.sim)
    result=paired_audit(sim,params,x.seeds,x.checkpoint,x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "audit_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({
        "schema":SCHEMA,"seeds":result["seeds"],
        "aggregate_mean":result["aggregate_mean"],
        "paired_duration_effects":result["paired_duration_effects"],
        "out":str(x.out)
    },indent=2))

if __name__=="__main__":
    main()
