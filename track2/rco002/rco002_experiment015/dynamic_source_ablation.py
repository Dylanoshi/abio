#!/usr/bin/env python3
"""E015 Phase 5: matched dynamic material-bridge protective-source ablation.

All four arms share an identical physical/field state at t=300. The material
bridge is updated after each bond-update, before that tick's catalytic births.
Only field deposition is ablated: catalysis, nutrient use, particles, and
reaction rules are never directly inhibited. The off-target control samples
nonfocal productive births with a PRECHECKPOINT-calibrated fixed probability;
dose matching is audited, not assumed.
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

SCHEMA="abio-e015-dynamic-material-source-ablation-v1"
ARMS={
    "sham":"all",
    "dynamic_self_off":"dynamic_self_off",
    "offtarget_control":"offtarget_rate_control",
    "global_field_off":"none",
}

class MaterialBridge:
    """Single-successor material-overlap tracker; never treats IDs as organisms."""
    def __init__(self,focal):
        self.focal=focal
        self.present=bool(focal)
        self.ids=set(focal["checkpoint_particle_ids"]) if focal else set()
        self.current_fid=focal["fid"] if focal else None
        self.sites=set()
        self.ambiguous_steps=[]
        self.fid_changes=0
        self.first_lost=None
        self.history=[]
        self.births=Counter()
        self.deposits=Counter()
        self.suppressed=Counter()
        self.checkpoint_motif=focal["profile_at_checkpoint"] if focal else {}

    def __call__(self,event,**kw):
        if event=="after_identify":
            self.update(kw["s"],kw["t"])
        elif event=="catalytic_event":
            self.birth(kw)
        elif event=="tick_end":
            self.record(kw["s"],kw["t"])

    def update(self,s,t):
        if not self.present:
            s["e015_focal_fid"]=None
            return
        cand=[]
        for fid,group in s["fmembers"].items():
            overlap=len(self.ids & set(group["ids"]))
            if overlap:
                cand.append((overlap,len(group["ids"]),-fid,fid,group))
        if not cand:
            self.present=False
            self.current_fid=None
            self.ids=set()
            self.sites=set()
            s["e015_focal_fid"]=None
            self.first_lost=t
            return
        cand.sort(key=lambda x:x[:3],reverse=True)
        best=cand[0]
        if len(cand)>1 and cand[1][0]==best[0]:
            self.ambiguous_steps.append(t)
        fid,group=best[3],best[4]
        if fid!=self.current_fid: self.fid_changes+=1
        self.current_fid=fid
        self.ids=set(group["ids"])
        self.sites=set(group["sites"])
        s["e015_focal_fid"]=fid

    def birth(self,kw):
        kind="focal" if self.present and kw["producer_fid"]==self.current_fid else "nonfocal"
        self.births[kind]+=1
        if kw["deposited"]: self.deposits[kind]+=1
        else: self.suppressed[kind]+=1

    def record(self,s,t):
        group=s["fmembers"].get(self.current_fid) if self.present else None
        profile=group["profile"] if group else {}
        similarity=safe_similarity(profile,self.checkpoint_motif)
        self.history.append({
            "step":t,"bridge_present":int(self.present),
            "bridge_size":len(self.ids),
            "bridge_fid":self.current_fid,
            "functional_similarity_to_checkpoint":round(similarity,5),
            "original_ids_in_bridge":len(self.ids &
                 set(self.focal["checkpoint_particle_ids"])) if self.focal else 0,
            "active_motifs":sum(profile.values()) if group else 0,
            "field_at_bridge_sites":round(
                sum(s["e015_field"].get(i,0.) for i in self.sites)/len(self.sites)
                if self.sites else 0.,5),
            "global_bonds":len(s["bonds"]),
        })

def safe_similarity(a,b):
    import math
    keys=set(a)|set(b)
    den=math.sqrt(sum(a.get(k,0)**2 for k in keys)*
                  sum(b.get(k,0)**2 for k in keys))
    return sum(a.get(k,0)*b.get(k,0) for k in keys)/den if den else 0.


def precheckpoint_rate(state,focal,checkpoint):
    """Off-target Bernoulli rate calculated only from t<=checkpoint history."""
    if focal is None: return 0., {"focal":0,"nonfocal":0}
    recent=[e for e in state["motif_events"]
            if checkpoint-40<e["step"]<=checkpoint]
    focal_n=sum(e["producer_fid"]==focal["fid"] for e in recent)
    other_n=len(recent)-focal_n
    return min(1.,focal_n/other_n) if other_n else 0.,{
        "focal":focal_n,"nonfocal":other_n}


def run(sim,params,seeds,checkpoint=300,end=600):
    a=argparse.Namespace(**params)
    if checkpoint<40 or not checkpoint<end<=a.steps:
        raise ValueError("Invalid checkpoint/end")
    if not seeds or len(set(seeds))!=len(seeds):
        raise ValueError("Seeds required and must be unique")
    records=[]
    for seed in seeds:
        base=sim.initialize(seed,a)
        for t in range(1,checkpoint+1):
            sim.tick(base,seed,"local",t,a,[],[])
        focal,selection=choose_focal(base,checkpoint)
        rate,precounts=precheckpoint_rate(base,focal,checkpoint)
        state_hash=physical_signature(base)
        arms={}
        for name,policy in ARMS.items():
            state=copy.deepcopy(base)
            if physical_signature(state)!=state_hash:
                raise AssertionError("Different checkpoint states")
            tracker=MaterialBridge(focal)
            state["e015_audit_hook"]=tracker
            state["e015_deposition_policy"]=policy
            state["e015_offtarget_rate"]=rate
            initial=Counter(state["e015_stats"])
            for t in range(checkpoint+1,end+1):
                sim.tick(state,seed,"local",t,a,[],[])
            state.pop("e015_audit_hook")
            physical_hash=physical_signature(state)
            steps=sum(x["bridge_present"] for x in tracker.history)
            mean_sim=statistics.mean(x["functional_similarity_to_checkpoint"]
                                     for x in tracker.history)
            arms[name]={
                "bridge_present_steps":steps,
                "first_material_bridge_loss":tracker.first_lost,
                "fid_changes":tracker.fid_changes,
                "ambiguous_split_steps":tracker.ambiguous_steps,
                "mean_functional_similarity":round(mean_sim,5),
                "motif_positive_steps":sum(
                    x["bridge_present"] and x["active_motifs"]>0
                    for x in tracker.history),
                "mean_field_at_bridge":round(statistics.mean(
                    x["field_at_bridge_sites"] for x in tracker.history),5),
                "source_focal_births":tracker.births["focal"],
                "source_nonfocal_births":tracker.births["nonfocal"],
                "focal_deposits_prevented":tracker.suppressed["focal"],
                "nonfocal_deposits_prevented":tracker.suppressed["nonfocal"],
                "focal_deposits_allowed":tracker.deposits["focal"],
                "nonfocal_deposits_allowed":tracker.deposits["nonfocal"],
                "postbranch_catalytic_births":
                    state["catalytic_births"]-base["catalytic_births"],
                "end_physical_hash":physical_hash,
                "timeline":tracker.history,
            }
            # Every successful catalytic birth must be classified exactly once
            # and every field deposit either allowed or withheld.
            row=arms[name]
            if row["postbranch_catalytic_births"]!=(
                  row["source_focal_births"]+row["source_nonfocal_births"]):
                raise AssertionError("Birth provenance count mismatch")
            if row["postbranch_catalytic_births"]!=(
                  row["focal_deposits_prevented"]+row["nonfocal_deposits_prevented"]+
                  row["focal_deposits_allowed"]+row["nonfocal_deposits_allowed"]):
                raise AssertionError("Deposition accounting mismatch")
            if policy=="dynamic_self_off" and row["focal_deposits_allowed"]!=0:
                raise AssertionError("Focal source escaped suppression")
            if policy=="offtarget_rate_control" and row["focal_deposits_prevented"]!=0:
                raise AssertionError("Off-target control suppressed focal source")
            if policy=="none" and (row["focal_deposits_allowed"] or row["nonfocal_deposits_allowed"]):
                raise AssertionError("No-field arm still deposited field")
        records.append({
            "seed":seed,"checkpoint_hash":state_hash,
            "focal":focal,"selection":selection,"calibrated_offtarget_rate":rate,
            "precheckpoint_birth_counts":precounts,"by_arm":arms,
            "actual_suppressed_counts_matched":
                arms["dynamic_self_off"]["focal_deposits_prevented"]==
                arms["offtarget_control"]["nonfocal_deposits_prevented"],
        })
        print("RUN",json.dumps({
            "seed":seed,"focal_fid":focal["fid"] if focal else None,
            "precheckpoint_control_rate":round(rate,5),
            "present_steps":{k:arms[k]["bridge_present_steps"] for k in ARMS},
            "self_deposits_blocked":arms["dynamic_self_off"]["focal_deposits_prevented"],
            "offtarget_deposits_blocked":arms["offtarget_control"]["nonfocal_deposits_prevented"],
            "dose_matched":records[-1]["actual_suppressed_counts_matched"],
        }),flush=True)
    measures=("bridge_present_steps","mean_functional_similarity","motif_positive_steps",
              "mean_field_at_bridge","focal_deposits_prevented",
              "nonfocal_deposits_prevented","postbranch_catalytic_births")
    aggregate={name:{key:round(statistics.mean(
        r["by_arm"][name][key] for r in records),5) for key in measures}
        for name in ARMS}
    paired=[{
        "seed":r["seed"],
        "sham_minus_self_removed_steps":
            r["by_arm"]["sham"]["bridge_present_steps"]-
            r["by_arm"]["dynamic_self_off"]["bridge_present_steps"],
        "sham_minus_offtarget_steps":
            r["by_arm"]["sham"]["bridge_present_steps"]-
            r["by_arm"]["offtarget_control"]["bridge_present_steps"],
        "self_suppression_exposed":
            r["by_arm"]["dynamic_self_off"]["focal_deposits_prevented"]>0,
        "offtarget_suppression_exposed":
            r["by_arm"]["offtarget_control"]["nonfocal_deposits_prevented"]>0,
        "dose_matched":r["actual_suppressed_counts_matched"],
    } for r in records]
    return {
        "schema":SCHEMA,"status":"exploratory dynamic field-source ablation",
        "parameters":params,"seeds":list(seeds),
        "checkpoint":checkpoint,"end":end,
        "arm_policy":ARMS,
        "focal_selection":"Prebranch age>=30, size>=3, motif present; rank by prior 40 step catalytic births, age, size, ID",
        "offtarget_calibration":"Fixed Bernoulli fraction focal/nonfocal births over 40 PRECHECKPOINT steps; not guaranteed exposure matched",
        "material_bridge_tracking":"One bonded component with most overlapping particle IDs per step, retained while any overlap exists; per-arm independently tracked",
        "records":records,"aggregate_mean":aggregate,"paired_differences":paired,
        "limitations":[
            "The focal is an observational material-bridge heuristic, not a proved individual.",
            "Full constituent turnover between adjacent ticks ends the trace.",
            "Merges and splits create ambiguous organizational identity.",
            "Offtarget suppression attempts are precheckpoint-calibrated but actual counts, sites and timing are NOT exactly matched.",
            "Causal comparisons are arm-level interventions on a designed stabilizing field, not spontaneous invention of machinery.",
            "The changing focal identity is determined within each arm; trajectories and targets can diverge after treatment.",
            "Material continuity and retained motif similarity do not establish RAF closure, autopoiesis, heredity or reproduction.",
            "Trials within each seed are correlated, not independent replicates.",
        ],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--checkpoint",type=int,default=300)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--seeds",nargs="+",type=int,default=list(range(12)))
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    params=dict(DEFAULTS,steps=max(600,x.end))
    result=run(load_sim(x.sim),params,x.seeds,x.checkpoint,x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "driver_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({
        "schema":SCHEMA,"seeds":result["seeds"],
        "aggregate_mean":result["aggregate_mean"],
        "paired_differences":result["paired_differences"],
        "out":str(x.out)
    },indent=2))

if __name__=="__main__":
    main()
