#!/usr/bin/env python3
"""E015 Phase 6: timed shadow-sham exposure control and first-divergence audit.

Exploratory diagnostic on historical seeds 2,3, then prospective new seeds.
A deterministic shadow-sham is evolved FIRST from the shared checkpoint solely
to prescribe the focal-source deposit count at each future tick, without
using its eventual survival to choose targets. The control blocks the same
per-step count of NONFOCAL actual birth deposits when available.
This matches intended *count and time*, not site, mass or realized exposures.
"""
import argparse
import copy
import hashlib
import json
import statistics
from collections import Counter,defaultdict
from pathlib import Path
from ablation import load_sim,physical_signature
from dynamic_source_ablation import MaterialBridge, safe_similarity
from run import DEFAULTS
from source_ablation import choose_focal

SCHEMA="abio-e015-timed-offtarget-first-divergence-v1"
ARMS=("sham","self_removed","timed_offtarget")

class Trace(MaterialBridge):
    def __init__(self,focal):
        super().__init__(focal)
        self.birth_rows=[]
        self.bond_rows=defaultdict(list)
        self.field_rows={}
        self.physical_rows={}
        self.ledger=Counter()
    def __call__(self,event,**kw):
        if event=="bond_trial":
            self.bond(kw)
        elif event=="field_ready":
            pass
        else:
            super().__call__(event,**kw)
        if event=="tick_end":
            s=kw["s"];t=kw["t"]
            self.physical_rows[t]={
                "physical_hash":physical_signature(s),
                "cells_hash":digest(sorted(s["cells"].items())),
                "ids_hash":digest(sorted(s["ids"].items())),
                "bonds_hash":digest(sorted(map(list,s["bonds"]))),
                "field_hash":digest(sorted(s["e015_field"].items())),
                "global_bonds":len(s["bonds"]),
                "catalytic_births":s["catalytic_births"],
                "bridge_fid":self.current_fid,
                "bridge_size":len(self.ids),
                "bridge_present":self.present,
                "bridge_sites":sorted(self.sites),
                "bridge_ids":sorted(self.ids),
            }
    def bond(self,kw):
        s=kw["s"];t=kw["t"]
        e=tuple(kw["sites"])
        self.bond_rows[t].append({
            "sites":e,"ids":tuple(kw["particle_ids"]),
            "draw":kw["draw"],"threshold":kw["threshold"],
            "actual_broken":kw["draw"]<kw["threshold"],
            "baseline":kw["baseline"],
            "current_bridge_edge":self.present and set(e)<=self.sites,
        })
    def birth(self,kw):
        super().birth(kw)
        focal=bool(self.present and
                   kw["producer_fid"]==self.current_fid)
        self.birth_rows.append({
            "step":kw["t"],"source_focal":focal,
            "producer_fid":kw["producer_fid"],
            "catalyst_ids":list(kw["catalyst_ids"]),
            "sites":list(kw["sites"]),
            "product_id":kw["product_id"],
            "deposited":bool(kw["deposited"]),
        })
        key="focal" if focal else "nonfocal"
        self.ledger[(kw["t"],key,"births")]+=1
        if not kw["deposited"]:
            self.ledger[(kw["t"],key,"blocked")]+=1

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,
        separators=(",",":")).encode()).hexdigest()

def calculate_differences(sham,arm,start,end,detail_limit=60):
    first_field=None;first_bonds=None;first_cells=None
    first_organization=None;first_full=None
    differing=[]
    # Every step is compared, not only the first one.
    for t in range(start+1,end+1):
        a=sham.physical_rows[t];b=arm.physical_rows[t]
        if first_full is None and a["physical_hash"]!=b["physical_hash"]:first_full=t
        if first_field is None and a["field_hash"]!=b["field_hash"]:first_field=t
        if first_bonds is None and a["bonds_hash"]!=b["bonds_hash"]:first_bonds=t
        if first_cells is None and a["cells_hash"]!=b["cells_hash"]:first_cells=t
        if first_organization is None and (a["bridge_present"],a["bridge_fid"],a["bridge_size"])!=(
                b["bridge_present"],b["bridge_fid"],b["bridge_size"]):
            first_organization=t
    for t in range(start+1,end+1):
        # Site/particle-pair indexed trials, not naive list position;
        # repeated trials on the same bond can exist within a tick.
        a=defaultdict(list);b=defaultdict(list)
        for x in sham.bond_rows.get(t,[]): a[(x["sites"],x["ids"])].append(x)
        for x in arm.bond_rows.get(t,[]): b[(x["sites"],x["ids"])].append(x)
        for key in sorted(set(a)&set(b)):
            for j,(x,y) in enumerate(zip(a[key],b[key])):
                if x["actual_broken"]!=y["actual_broken"]:
                    differing.append({
                        "step":t,"sites":list(key[0]),"particle_ids":list(key[1]),
                        "trial_repetition_index":j,
                        "sham_draw":x["draw"],"arm_draw":y["draw"],
                        "same_draw":x["draw"]==y["draw"],
                        "sham_threshold":x["threshold"],"arm_threshold":y["threshold"],
                        "sham_broken":x["actual_broken"],
                        "arm_broken":y["actual_broken"],
                        "sham_bridge_edge_at_trial":x["current_bridge_edge"],
                        "arm_bridge_edge_at_trial":y["current_bridge_edge"],
                    })
                if len(differing)>=detail_limit:break
            if len(differing)>=detail_limit:break
        if len(differing)>=detail_limit:break
    first_source={
        "sham":next((b for b in sham.birth_rows if b["source_focal"] and b["deposited"]
                     and b["step"]>start),None),
        "arm":next((b for b in arm.birth_rows if b["source_focal"] and not b["deposited"]
                    and b["step"]>start),None),
    }
    return {
        "first_physical_divergence":first_full,
        "first_field_divergence":first_field,
        "first_bond_set_divergence":first_bonds,
        "first_cell_population_divergence":first_cells,
        "first_bridge_descriptor_divergence":first_organization,
        "first_source_events":first_source,
        "first_changed_common_bond_trial":differing[0] if differing else None,
        "changed_common_bond_trials_sample":differing,
        "first_unbridged_sham":sham.first_lost,
        "first_unbridged_arm":arm.first_lost,
    }

def execute(sim,params,seeds,checkpoint,end):
    a=argparse.Namespace(**params)
    if checkpoint<40 or end<=checkpoint or end>a.steps:raise ValueError("Bad window")
    if not seeds or len(set(seeds))!=len(seeds):raise ValueError("Invalid seeds")
    records=[]
    for seed in seeds:
        base=sim.initialize(seed,a)
        for t in range(1,checkpoint+1):
            sim.tick(base,seed,"local",t,a,[],[])
        focal,sel=choose_focal(base,checkpoint)
        common_hash=physical_signature(base)
        trace_by={}
        final_states={}
        # SHAM FIRST: its post-checkpoint focal-source event counts establish
        # an ex ante fixed per-step budget for the off-target branch. No
        # survivor/non-survivor outcomes or arm comparisons choose that budget.
        for arm in ARMS:
            state=copy.deepcopy(base)
            if physical_signature(state)!=common_hash:raise AssertionError("Checkpoint mismatch")
            tracer=Trace(focal)
            state["e015_audit_hook"]=tracer
            if arm=="sham":
                state["e015_deposition_policy"]="all"
            elif arm=="self_removed":
                state["e015_deposition_policy"]="dynamic_self_off"
            elif arm=="timed_offtarget":
                state["e015_deposition_policy"]="offtarget_step_budget"
                state["e015_offtarget_step_budget"]=sham_schedule
            for t in range(checkpoint+1,end+1):
                sim.tick(state,seed,"local",t,a,[],[])
            state.pop("e015_audit_hook")
            trace_by[arm]=tracer
            final_states[arm]=physical_signature(state)
            if arm=="sham":
                sham_schedule={t:tracer.ledger[(t,"focal","births")]
                               for t in range(checkpoint+1,end+1)}
                # All focal sham births deposit; use observed focal birth
                # opportunities to define time-specific control dose.
        sham=trace_by["sham"]
        selfarm=trace_by["self_removed"]
        ctrl=trace_by["timed_offtarget"]
        budget=sum(sham_schedule.values())
        ctrl_blocked=ctrl.suppressed["nonfocal"]
        self_blocked=selfarm.suppressed["focal"]
        stats={
            arm:{
                "bridge_present_steps":sum(r["bridge_present"] for r in trace_by[arm].history),
                "first_bridge_loss":trace_by[arm].first_lost,
                "mean_checkpoint_function_similarity":round(statistics.mean(
                    r["functional_similarity_to_checkpoint"] for r in trace_by[arm].history),5),
                "motif_positive_steps":sum(r["active_motifs"]>0 and r["bridge_present"]
                                           for r in trace_by[arm].history),
                "focal_births":trace_by[arm].births["focal"],
                "nonfocal_births":trace_by[arm].births["nonfocal"],
                "focal_suppressed":trace_by[arm].suppressed["focal"],
                "nonfocal_suppressed":trace_by[arm].suppressed["nonfocal"],
                "focal_deposited":trace_by[arm].deposits["focal"],
                "nonfocal_deposited":trace_by[arm].deposits["nonfocal"],
            } for arm in ARMS
        }
        per_tick={
            str(t):{
                "sham_focal_birth_budget":sham_schedule[t],
                "self_focal_blocked":selfarm.ledger[(t,"focal","blocked")],
                "control_nonfocal_blocked":ctrl.ledger[(t,"nonfocal","blocked")],
            } for t in range(checkpoint+1,end+1)
        }
        mismatched_steps=sum(v["sham_focal_birth_budget"]!=v["control_nonfocal_blocked"]
                             for v in per_tick.values())
        records.append({
            "seed":seed,"checkpoint_hash":common_hash,"focal":focal,
            "selection":sel,"arms":stats,
            "sham_prescribed_focal_suppression_count":budget,
            "actual_self_suppression_count":self_blocked,
            "actual_offtarget_suppression_count":ctrl_blocked,
            "offtarget_vs_sham_budget_count_matched":budget==ctrl_blocked,
            "offtarget_vs_self_count_matched":self_blocked==ctrl_blocked,
            "offtarget_per_step_budget_unmet_steps":mismatched_steps,
            "per_tick_exposure":per_tick,
            "divergence_self":calculate_differences(sham,selfarm,checkpoint,end),
            "divergence_offtarget":calculate_differences(sham,ctrl,checkpoint,end),
            "final_physical_hashes":final_states,
        })
        print("RUN",json.dumps({
            "seed":seed,"focal_fid":focal["fid"] if focal else None,
            "present":{arm:stats[arm]["bridge_present_steps"] for arm in ARMS},
            "sham_prescribed":budget,"self_blocked":self_blocked,
            "control_blocked":ctrl_blocked,"unmet_steps":mismatched_steps,
            "first_field_difference":records[-1]["divergence_self"]["first_field_divergence"],
            "first_bond_difference":records[-1]["divergence_self"]["first_bond_set_divergence"],
            "first_changed_common_trial":records[-1]["divergence_self"]["first_changed_common_bond_trial"],
        }),flush=True)
    aggregate={
        arm:{k:round(statistics.mean(r["arms"][arm][k] for r in records),4)
              for k in ("bridge_present_steps","mean_checkpoint_function_similarity",
                        "motif_positive_steps","focal_suppressed","nonfocal_suppressed")}
        for arm in ARMS
    }
    return {
        "schema":SCHEMA,
        "status":"exploratory historical diagnostics; fresh seeds separately assess generalization",
        "parameters":params,"seeds":list(seeds),
        "checkpoint":checkpoint,"end":end,
        "design":"Matched common state. Shadow sham per-tick focal birth counts prescribe control nonfocal suppression quotas; counts/timing attempted, space/field mass not matched.",
        "records":records,"aggregate_mean":aggregate,
        "limitations":[
            "Shadow sham schedule is derived from sham future activity, but NOT from its survival outcome or intervention effect.",
            "Matching intended per-tick counts does not equate field gain due to capping, spatial distance or protection at bridge bonds.",
            "Actual focal suppression events may diverge from sham after treatment, so self/control counts can remain unequal.",
            "Trial keys can repeat, so common-trial first divergence is approximate with repetition indexing.",
            "Material bridge chosen by particle overlap remains heuristic and can survive only a finite turnover/split structure.",
            "Historical seeds 2 and 3 were chosen after observing large effects; they are NOT independent confirmatory evidence.",
            "Structural survival and motif similarity cannot establish regenerative closure or computational life.",
        ],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--checkpoint",type=int,default=300)
    p.add_argument("--end",type=int,default=600)
    p.add_argument("--seeds",nargs="+",type=int,default=[2,3])
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    params=dict(DEFAULTS,steps=max(600,x.end))
    result=execute(load_sim(x.sim),params,x.seeds,x.checkpoint,x.end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "driver_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({
        "schema":SCHEMA,"seeds":result["seeds"],
        "aggregate_mean":result["aggregate_mean"],
        "count_matched_to_sham_seeds":sum(
            r["offtarget_vs_sham_budget_count_matched"] for r in result["records"]),
        "count_matched_to_actual_self_seeds":sum(
            r["offtarget_vs_self_count_matched"] for r in result["records"]),
        "out":str(x.out),
    },indent=2))
if __name__=="__main__":
    main()
