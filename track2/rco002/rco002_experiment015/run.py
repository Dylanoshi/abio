#!/usr/bin/env python3
"""E015: preregistered substrate-level local stabilization comparative sweep.

Three paired conditions per seed: disabled, spatially coupled local feedback,
and spatially shuffled feedback with the same accumulated activity strengths.
No privileged organism, reproduction rule, fitness function, or target selection.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import statistics
from collections import defaultdict
from pathlib import Path

DEFAULTS = {
    "size":24,"steps":600,"initial_density":.20,
    "decay":.008,"supply":.018,"bond_form":.075,"bond_break":.018,
    "rule_density":.85,"catalysis_rate":.14,"background_rate":.0015,
    "interrupt_fraction":.60,"min_target_size":3,"activity_window":50,
    "field_retention":.8,"field_gain":1.0,"field_cap":4.0,
    "protection_strength":3.0,
}
CONDITIONS=("disabled","local","shuffled")
CRITERIA={"min_consecutive_functional_age":30,
          "min_cumulative_entries":3,
          "min_cumulative_departures":3,
          "min_active_catalytic_motifs":1}
EXPERIMENT_SCHEMA="abio-e015-local-structural-feedback-v1"


def load_sim(path):
    spec=importlib.util.spec_from_file_location("e015_sim",str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_summary(sim, state, seed, mode, parameters, window_start):
    history=[row for row in state["history"] if row["step"]>=window_start]
    functional=[row for row in state["functional_rows"] if row["step"]>=window_start]
    candidates=[
        row for row in functional
        if row["age"]>=CRITERIA["min_consecutive_functional_age"]
        and row["entered_cumulative"]>=CRITERIA["min_cumulative_entries"]
        and row["departed_cumulative"]>=CRITERIA["min_cumulative_departures"]
        and row["active_catalytic_motifs"]>=CRITERIA["min_active_catalytic_motifs"]
    ]
    # Linear-time per-step maxima; functional_rows may contain many components.
    max_by_step={}
    for row in functional:
        t=row["step"]
        max_by_step[t]=max(max_by_step.get(t,0),row["size"])
    max_sizes=list(max_by_step.values())
    start=state["history"][0]
    end=state["history"][-1]
    activity_field=state["e015_field"]
    score={
        "seed":seed,"condition":mode,
        "time_window_start":window_start,
        "window_steps":len(history),
        "mean_particles":round(statistics.mean(r["particles"] for r in history),3),
        "mean_bonds":round(statistics.mean(r["bonds"] for r in history),3),
        "mean_largest_bonded_component":round(statistics.mean(max_sizes),3) if max_sizes else 0,
        "max_functional_age":max((r["age"] for r in functional),default=0),
        "turnover_motif_candidate_steps":len(candidates),
        "distinct_candidate_lineages":len({r["functional_id"] for r in candidates}),
        "catalytic_births":end["catalytic_births"],
        "background_births":end["background_births"],
        "deaths":end["deaths"],
        "actual_bond_breaks":state["e015_stats"]["actual_breaks"],
        "field_exposed_break_trials":state["e015_stats"]["exposed_trials"],
        "prevented_breaks_against_same_draw_baseline":state["e015_stats"]["prevented_breaks"],
        "final_field_mass":round(sum(activity_field.values()),5),
    }
    # A candidate is just an overlap-heuristic bonded component with documented
    # changes in constituent membership and at least one productive pair.
    return score


def execute(sim,parameters,seeds,out):
    a=argparse.Namespace(**parameters)
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    per_seed_rows=[]
    for seed in seeds:
        for mode in CONDITIONS:
            state=sim.initialize(seed,a)
            events=[];lineages=[]
            for t in range(1,a.steps+1):
                sim.tick(state,seed,mode,t,a,events,lineages)
            row=state_summary(sim,state,seed,mode,parameters,a.steps//2+1)
            records.append(row)
            per_seed_rows.append({
                "seed":seed,
                "condition":mode,
                "timeseries":[{
                    "step":r["step"],"particles":r["particles"],
                    "bonds":r["bonds"],"catalytic_births":r["catalytic_births"],
                    "background_births":r["background_births"],"deaths":r["deaths"]
                } for r in state["history"][::10]]
            })
            print("RUN",json.dumps({
                "seed":seed,"condition":mode,
                "candidate_steps":row["turnover_motif_candidate_steps"],
                "mean_bonds":row["mean_bonds"],
                "exposed_trials":row["field_exposed_break_trials"]
            }),flush=True)
    fields=["mean_bonds","mean_largest_bonded_component",
            "turnover_motif_candidate_steps","distinct_candidate_lineages",
            "max_functional_age","catalytic_births",
            "actual_bond_breaks","field_exposed_break_trials"]
    aggregate={}
    for mode in CONDITIONS:
        subset=[r for r in records if r["condition"]==mode]
        aggregate[mode]={key:round(statistics.mean(r[key] for r in subset),4)
                         for key in fields}
    delta={}
    for mode in ("local","shuffled"):
        delta[mode]={key:round(aggregate[mode][key]-aggregate["disabled"][key],4)
                     for key in fields}
    paired=[]
    for seed in seeds:
        group={r["condition"]:r for r in records if r["seed"]==seed}
        paired.append({
            "seed":seed,
            "local_minus_disabled_candidate_steps":
                group["local"]["turnover_motif_candidate_steps"]-
                group["disabled"]["turnover_motif_candidate_steps"],
            "local_minus_shuffled_candidate_steps":
                group["local"]["turnover_motif_candidate_steps"]-
                group["shuffled"]["turnover_motif_candidate_steps"],
            "local_minus_shuffled_mean_bonds":
                round(group["local"]["mean_bonds"]-group["shuffled"]["mean_bonds"],4),
        })
    result={
        "schema":EXPERIMENT_SCHEMA,
        "status":"exploratory; no verified life, RAF closure or endogenous autonomy",
        "parameters":parameters,
        "predefined_seeds":list(seeds),
        "conditions":{
            "disabled":"catalytic activity produces a field but field is ignored for bond breaking",
            "local":"bond breaking is reduced by previous catalysis at local endpoints",
            "shuffled":"same field strength multiset at randomized positions each step",
        },
        "prespecified_criteria":CRITERIA,
        "measurement_window":[a.steps//2+1,a.steps],
        "individual_records":records,
        "aggregate_mean":aggregate,
        "mean_differences_vs_disabled":delta,
        "paired_differences":paired,
        "limitations":[
            "The designer provides generic catalysis-to-bond-strength feedback, so its existence is not emergent.",
            "The experiment tests whether non-targeted spatial self-reinforcement selects lasting components.",
            "Tracker uses material/spatial overlap, not independently validated organizational individuality.",
            "Motif-bearing turnover candidates are NOT formal RAFs or verified self-maintenance.",
            "Local field is generated by realized catalysis and shuffled control preserves field mass but not spatial correlation.",
            "Longer bonds alone do not establish autoregulation, regeneration or reproduction.",
            "Paired conditions share seeds and are not independent biological samples.",
            "No inferential significance/novel life claim is made from the exploratory stage.",
        ],
    }
    (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"timeseries_10step.json").write_text(json.dumps(per_seed_rows)+"\n")
    with (out/"per_seed.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]))
        writer.writeheader();writer.writerows(records)
    print("SUMMARY",json.dumps({
        "schema":EXPERIMENT_SCHEMA,
        "seeds":list(seeds),
        "aggregate_mean":aggregate,
        "paired_differences":paired,
        "out":str(out)
    },indent=2))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,
                   default=Path(__file__).with_name("e015_sim.py"))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--seeds",nargs="+",type=int,default=list(range(12)))
    p.add_argument("--steps",type=int,default=600)
    p.add_argument("--size",type=int,default=24)
    x=p.parse_args()
    if x.steps<100 or x.size<8 or len(set(x.seeds))!=len(x.seeds):
        p.error("Invalid steps, grid size or duplicate seeds")
    pars=dict(DEFAULTS,steps=x.steps,size=x.size)
    result=execute(load_sim(x.sim),pars,x.seeds,x.out)
    result_path=x.out/"results.json"
    result["provenance"]={"sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
                          "driver_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result_path.write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    main()
