#!/usr/bin/env python3
"""E015 Phase 4: material-bridge ancestry & catalytic protection exposure.

Pure observational hooks: the E015 physics is unchanged, all runs use local
feedback, and each seed continues its exact state at the 300-step checkpoint.
A selected functional ID is NOT assumed to remain itself after splits/merges.
We infer a conservative one-component material bridge each step; ambiguity,
unbridged disappearances and background field contributions are preserved.
"""
import argparse
import copy
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

from ablation import load_sim, physical_signature
from run import DEFAULTS
from source_ablation import choose_focal

SCHEMA="abio-e015-material-bridge-exposure-audit-v1"
KINDS=("self_bridge","neighboring","external","legacy")

class ExposureRecorder:
    def __init__(self, state, focal, a, detail_limit=80):
        self.a=a
        self.focal=focal
        self.prev_ids=set(focal["checkpoint_particle_ids"]) if focal else set()
        self.bridge_ids=set(self.prev_ids)
        self.bridge_sites=set(state["fmembers"][focal["fid"]]["sites"]) if focal else set()
        self.bridge_fid=focal["fid"] if focal else None
        self.present=bool(focal)
        self.ambiguous_steps=[]
        self.first_unbridged_step=None
        self.provenance={site:{"legacy":float(v)} for site,v in state["e015_field"].items()}
        self.stats=Counter()
        self.by_step=[]
        self.details=[]
        self.detail_limit=detail_limit
        self.step_stats=Counter()
        self.last_event_t=None
        self.last_trace_fid=None

    def __call__(self, event, **kw):
        return getattr(self,"on_"+event)(**kw)

    def on_field_ready(self,s,t):
        # The simulator has ALREADY decayed and pruned field values. Bring
        # observational provenance into agreement without altering substrate.
        next_ledger={}
        for site,field_val in s["e015_field"].items():
            old=self.provenance.get(site,{})
            total=sum(old.values())
            if total>0:
                vals={kind:max(0.,value*field_val/total) for kind,value in old.items()}
            else:
                vals={"legacy":field_val}
            next_ledger[site]=vals
        self.provenance=next_ledger
        self.step_stats=Counter()
        self.stats["ticks"]+=1
        self.last_event_t=t
        self._validate(s)

    def on_bond_trial(self,s,t,sites,particle_ids,draw,threshold,baseline,strength):
        if not self.present or not set(sites)<=self.bridge_sites:
            return
        # These are the bonds of the material-bridge component before breaks.
        x,y=sites
        field=(s["e015_field"].get(x,0.)+s["e015_field"].get(y,0.))/2.
        self.stats["bridge_bond_trials"]+=1
        self.step_stats["bridge_bond_trials"]+=1
        if field>0.01:
            self.stats["bridge_field_exposed_trials"]+=1
            self.step_stats["bridge_field_exposed_trials"]+=1
        if draw<threshold:
            self.stats["bridge_bond_actual_breaks"]+=1
            self.step_stats["bridge_bond_actual_breaks"]+=1
        if threshold<=draw<baseline:
            self.stats["bridge_bond_prevented_vs_baseline"]+=1
            self.step_stats["bridge_bond_prevented_vs_baseline"]+=1
        own=(self.provenance.get(x,{}).get("self_bridge",0.)+
             self.provenance.get(y,{}).get("self_bridge",0.))/2.
        if own>1e-12:
            self.stats["bridge_bond_self_field_trials"]+=1
            self.step_stats["bridge_bond_self_field_trials"]+=1
        # One-step controlled same-draw subtraction, not a dynamic ablation:
        # preserve every other component and hold this state fixed.
        threshold_without_own=baseline/(1.0+strength*max(0.,field-own))
        if threshold<=draw<threshold_without_own:
            self.stats["bridge_bond_self_attributable_prevention"]+=1
            self.step_stats["bridge_bond_self_attributable_prevention"]+=1
            if len(self.details)<self.detail_limit:
                self.details.append({
                    "step":t,"sites":list(sites),"particle_ids":list(particle_ids),
                    "draw":draw,"break_threshold_observed":threshold,
                    "threshold_without_own_provenance":threshold_without_own,
                    "self_field":round(own,5),"total_field":round(field,5),
                    "event":"self_attributable_avoided_break_same_draw",
                })

    def on_after_identify(self,s,t):
        if not self.present:
            self.last_trace_fid=None
            return
        candidates=[]
        for fid,g in s["fmembers"].items():
            overlap=len(set(g["ids"]) & self.prev_ids)
            if overlap:
                candidates.append((overlap,len(g["ids"]),-fid,fid,g))
        if not candidates:
            self.present=False
            self.bridge_fid=None
            self.bridge_sites=set()
            self.bridge_ids=set()
            self.last_trace_fid=None
            self.first_unbridged_step=t
            self.stats["unbridged_disappearances"]+=1
            return
        candidates.sort(reverse=True,key=lambda e:e[:3])
        best=candidates[0]
        if len(candidates)>1 and candidates[1][0]==best[0]:
            self.ambiguous_steps.append(t)
            self.stats["ambiguous_split_steps"]+=1
        fid,g=best[3],best[4]
        if fid != self.bridge_fid:
            self.stats["bridge_fid_changes"]+=1
        self.bridge_fid=fid
        self.bridge_ids=set(g["ids"])
        self.bridge_sites=set(g["sites"])
        self.prev_ids=set(g["ids"])
        self.last_trace_fid=fid
        self.step_stats["bridge_present"]+=1
        self.step_stats["bridge_size"]=len(self.bridge_ids)

    def on_catalytic_event(self,s,t,producer_fid,catalyst_ids,sites,product_id,deposited):
        # Attribution is based on the *current component* traced by material
        # overlap, NOT the original functional ID at step 300.
        if self.present and producer_fid == self.bridge_fid:
            kind="self_bridge"
        elif self.present and (
            any(site in self.bridge_sites or any(
                near in self.bridge_sites for near in s_neighbors(site,self.a.size))
                for site in sites)
        ):
            kind="neighboring"
        else:
            kind="external"
        self.stats["catalytic_births_"+kind]+=1
        self.step_stats["catalytic_births_"+kind]+=1
        if not deposited:
            self.stats["undeposited_births"]+=1
            return
        actual_increment=0.
        for site in sites:
            current=self.provenance.setdefault(site,{})
            physical=float(s["e015_field"][site])
            old=sum(current.values())
            gain=max(0.,physical-old)
            if gain > 1e-9:
                current[kind]=current.get(kind,0.)+gain
            actual_increment+=gain
        self.stats["deposited_field_mass_"+kind]+=actual_increment
        self.step_stats["deposited_field_mass_"+kind]+=actual_increment
        self._validate(s)

    def on_tick_end(self,s,t):
        field_near_bonds=Counter()
        for edge in s["bonds"]:
            if not set(edge)<=self.bridge_sites:
                continue
            for site in edge:
                for kind,v in self.provenance.get(site,{}).items():
                    field_near_bonds[kind]+=v/2.
        snapshot=dict(self.step_stats)
        snapshot.update({
            "step":t,"bridge_present":int(self.present),
            "bridge_fid":self.bridge_fid,
            "bridge_size":len(self.bridge_ids),
            "provenance_at_bridge_bonds":{k:round(field_near_bonds[k],5)
                                           for k in KINDS},
        })
        self.by_step.append(snapshot)
        self._validate(s)

    def _validate(self,s):
        for site,val in s["e015_field"].items():
            actual=sum(self.provenance.get(site,{}).values())
            if abs(actual-val)>1e-7:
                raise AssertionError(
                    f"field provenance mismatch at site {site}: {actual} vs {val}")

def s_neighbors(i,side):
    x,y=i%side,i//side
    if x: yield i-1
    if x+1<side: yield i+1
    if y: yield i-side
    if y+1<side: yield i+side


def audit(sim,params,seeds,checkpoint,end):
    a=argparse.Namespace(**params)
    if checkpoint<40 or end<=checkpoint or end>a.steps:
        raise ValueError("Bad checkpoint/end")
    results=[]
    for seed in seeds:
        original=sim.initialize(seed,a)
        for t in range(1,checkpoint+1):
            sim.tick(original,seed,"local",t,a,[],[])
        focal,selection=choose_focal(original,checkpoint)
        checkpoint_hash=physical_signature(original)
        traced=copy.deepcopy(original)
        recorder=ExposureRecorder(traced,focal,a)
        traced["e015_audit_hook"]=recorder
        for t in range(checkpoint+1,end+1):
            sim.tick(traced,seed,"local",t,a,[],[])
        traced.pop("e015_audit_hook")
        # Independent comparator replays original E015 physics without ANY hooks.
        baseline=copy.deepcopy(original)
        for t in range(checkpoint+1,end+1):
            sim.tick(baseline,seed,"local",t,a,[],[])
        if physical_signature(traced)!=physical_signature(baseline):
            raise AssertionError(f"Observational tracing changed physics for seed {seed}")
        entry={
            "seed":seed,"checkpoint_physical_field_hash":checkpoint_hash,
            "final_physical_field_hash":physical_signature(traced),
            "focal":focal,"selection":selection,
            "focal_trace":{
                "first_unbridged_step":recorder.first_unbridged_step,
                "ambiguous_split_steps":recorder.ambiguous_steps,
                "bridge_fid_changes":recorder.stats["bridge_fid_changes"],
                "ticks_with_bridge":sum(r["bridge_present"] for r in recorder.by_step),
            },
            "stats":dict(recorder.stats),
            "notable_events":recorder.details,
            "per_step":recorder.by_step,
        }
        results.append(entry)
        print("RUN",json.dumps({
            "seed":seed,"focal_fid":focal["fid"] if focal else None,
            "first_unbridged":recorder.first_unbridged_step,
            "bridge_fid_changes":recorder.stats["bridge_fid_changes"],
            "self_source_births":recorder.stats["catalytic_births_self_bridge"],
            "neighbor_births":recorder.stats["catalytic_births_neighboring"],
            "bridge_field_trials":recorder.stats["bridge_field_exposed_trials"],
            "bridge_self_field_trials":recorder.stats["bridge_bond_self_field_trials"],
            "own_field_avoided_breaks":recorder.stats["bridge_bond_self_attributable_prevention"],
            "physics_hash_equal":True,
        }),flush=True)
    keys=(
        "catalytic_births_self_bridge","catalytic_births_neighboring",
        "catalytic_births_external","deposited_field_mass_self_bridge",
        "bridge_bond_trials","bridge_field_exposed_trials",
        "bridge_bond_self_field_trials",
        "bridge_bond_prevented_vs_baseline",
        "bridge_bond_self_attributable_prevention",
        "ambiguous_split_steps","bridge_fid_changes"
    )
    aggregate={k:round(statistics.mean(e["stats"].get(k,0) for e in results),5)
               for k in keys}
    return {
        "schema":SCHEMA,"seeds":list(seeds),"parameters":params,
        "checkpoint":checkpoint,"end":end,
        "selection":"Identical to E015 Phase 3: prior-40-step catalytic activity, age, size, fid",
        "ancestry_rule":"At each tick choose bonded group with strongest material overlap with previous traced group; no matching material bridge => trace ends; report tied splits",
        "counterfactual":"Same-draw one-step removal of source-attributed field only; NOT a dynamic intervention",
        "records":results,"aggregate_mean":aggregate,
        "limitations":[
            "Tracing is a one-component material overlap heuristic and misses identity after complete constituent turnover in a single tick.",
            "Source classification uses heuristic component ID; can be wrong on merges/splits.",
            "Initial checkpoint field provenance is unknown and explicitly labeled legacy.",
            "Field provenance attribution under capping assigns only net deposited gain.",
            "The one-step break attribution holds state/draws fixed; it is not a multi-step causal removal intervention.",
            "Bond stability need not imply regeneration, autopoiesis, RAF closure or reproduction.",
            "All trials within each seed are serially correlated and not independent samples.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--seeds",nargs="+",type=int,default=list(range(12)))
    p.add_argument("--checkpoint",type=int,default=300)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    params=dict(DEFAULTS,steps=max(600,x.end))
    sim=load_sim(x.sim)
    result=audit(sim,params,x.seeds,x.checkpoint,x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "driver_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({
        "schema":SCHEMA,"seeds":result["seeds"],
        "aggregate_mean":result["aggregate_mean"],"out":str(x.out)
    },indent=2))

if __name__=="__main__":
    main()
