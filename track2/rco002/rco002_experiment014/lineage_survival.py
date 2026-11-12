#!/usr/bin/env python3
"""E014: audit duration/disappearance of selected *tracked* functional lineage.

Input: previously generated active_control_run.py versioned JSON.
No new simulation, no causal claim, no assumption size=0 means all particles died.
"""
import argparse
import json
from pathlib import Path


def spans(steps):
    result=[]
    for step in sorted(set(steps)):
        if result and step==result[-1][-1]+1: result[-1].append(step)
        else: result.append([step])
    return [{"start":x[0],"end":x[-1],"duration":len(x)} for x in result]


def summarize_rows(rows):
    if not rows: raise ValueError("No timeseries rows")
    observed=sorted(rows,key=lambda x:int(x["step"]))
    steps=[int(r["step"]) for r in observed]
    if steps!=list(range(steps[0],steps[-1]+1)):
        raise ValueError("Noncontiguous or duplicate step data")
    present=[int(r["step"]) for r in observed if int(r["target_functional_size"])>0]
    absent=[int(r["step"]) for r in observed if int(r["target_functional_size"])==0]
    motif=[int(r["step"]) for r in observed if int(r["exact_motif_preservation"])==1]
    active=[int(r["step"]) for r in observed if int(r["recent_regenerative_incorporations"])>0]
    candidate=[int(r["step"]) for r in observed if int(r["strict_candidate"])==1]
    disappear=next((int(r["step"]) for r in observed if int(r["target_functional_size"])==0),None)
    recover=next((int(r["step"]) for r in observed
                  if disappear is not None and int(r["step"])>disappear
                  and int(r["target_functional_size"])>0),None)
    return {
        "initial_step":steps[0],"last_step":steps[-1],
        "present_steps":len(present),
        "first_absent_step":disappear,
        "first_reappearance_after_absence":recover,
        "present_intervals":spans(present),
        "absent_intervals":spans(absent),
        "exact_motif_intervals":spans(motif),
        "regenerative_indicator_intervals":spans(active),
        "strict_candidate_intervals":spans(candidate),
        "final_functional_size":int(observed[-1]["target_functional_size"]),
        "max_functional_size":max(int(r["target_functional_size"]) for r in observed),
        "final_functional_similarity":float(observed[-1]["target_functional_similarity"]),
    }


def audit(result):
    if result.get("schema")!="abio-e014-active-control-intervention-v1":
        raise ValueError("Not an E014 active-control intervention report")
    return {
        "schema":"abio-e014-lineage-survival-audit-v1",
        "seed":result["provenance"]["seed"],
        "window":[result["provenance"]["start"],result["provenance"]["end"]],
        "modes":{k:summarize_rows(v["rows"]) for k,v in result["branches"].items()},
        "caveats":[
            "A missing original E011 functional lineage ID is not proof all particles are extinct.",
            "Lineage identity is tracked by a spatial/material overlap heuristic.",
            "Regenerative indicators have finite memory windows; counts are not independent events.",
            "This is a retrospectively selected candidate with no long-term establishment demonstrated."
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(json.loads(a.input.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "window":result["window"],
        "by_mode":{mode:{
            "present_steps":x["present_steps"],
            "first_absent_step":x["first_absent_step"],
            "first_reappearance_after_absence":x["first_reappearance_after_absence"],
            "exact_motif_intervals":x["exact_motif_intervals"],
            "strict_candidate_intervals":x["strict_candidate_intervals"],
        } for mode,x in result["modes"].items()},
        "output":str(a.out)},indent=2))


if __name__=="__main__": main()
