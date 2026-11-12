#!/usr/bin/env python3
"""E014: trace loss of a selected functional identity near step 543.

Paired sham/target-block/off-target-block trajectories, reconstructing from E013.
Never conflate loss of an assigned lineage ID with physical extinction.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from active_control_run import load_schedule
from short_horizon import load_sim, physical_hash


def component_records(sim, s):
    groups=[]
    for sites in sim.components(s["cells"],s["bonds"]):
        if len(sites)<2: continue
        site_set=set(sites)
        pids={s["ids"][i] for i in site_set}
        profile=sim.functional_profile(s,site_set)
        fid=s["site_flid"].get(next(iter(site_set)))
        groups.append({
            "fid":fid,
            "sites":sorted(site_set),
            "particle_ids":sorted(pids),
            "size":len(pids),
            "profile":dict(sorted(profile.items())),
        })
    return groups


def local_state(sim,s,step):
    target=s["target_flid"]
    desc=s["fmembers"].get(target)
    groups=component_records(sim,s)
    # Keep an exact identity census only at the transition of interest.
    # Unlike bonded components, this includes isolated surviving particles.
    identity_census = {}
    if step in (542, 543):
        degree = {pid: 0 for pid in s["ids"].values()}
        for u, v in s["bonds"]:
            degree[s["ids"][u]] += 1
            degree[s["ids"][v]] += 1
        identity_census = {
            str(pid): {"site": site, "type": s["cells"][site],
                       "degree": degree[pid]}
            for site, pid in sorted(s["ids"].items())
        }
    return {
        "step":step,
        "particle_identity_census":identity_census,
        "physical_hash":physical_hash(s),
        "target_fid":target,
        "target_present":bool(desc),
        "target_group":next((g for g in groups if g["fid"]==target),None),
        "groups":groups,
        "particle_count":len(s["cells"]),
        "bond_count":len(s["bonds"]),
        "nutrient_count":len(s["nutrient"]),
        "strict_candidate":int(s["exact_rows"][-1]["strict_candidate"]),
        "original_motifs_preserved":int(s["exact_rows"][-1]["exact_motif_preservation"]),
    }


def successor_candidates(sim, previous, current):
    """Rank physical successor possibilities independently of assigned ID."""
    old=previous.get("target_group")
    if not old: return []
    a=set(old["sites"]); b=set(old["particle_ids"])
    out=[]
    for g in current["groups"]:
        spatial=len(a & set(g["sites"]))
        particle=len(b & set(g["particle_ids"]))
        profile=sim.profile_similarity(g["profile"],old["profile"])
        if not (spatial or particle or profile): continue
        score=max(spatial/max(len(a),len(g["sites"])),
                  particle/max(len(b),len(g["particle_ids"])))+0.25*profile
        out.append({
            "new_fid":g["fid"],
            "new_size":g["size"],
            "spatial_overlap":spatial,
            "particle_overlap":particle,
            "profile_similarity":round(profile,4),
            "tracking_score":round(score,4),
            "new_profile":g["profile"],
        })
    return sorted(out,key=lambda x:(x["tracking_score"],x["particle_overlap"],x["spatial_overlap"]),reverse=True)[:8]


def audit(sim,settings,preflight,seed,start,inspect_start,inspect_end):
    a=argparse.Namespace(**settings)
    branch_at=int(a.steps*a.interrupt_fraction)
    if not branch_at<start<=inspect_start<=543<=inspect_end<=a.steps:
        raise ValueError("Inspection must include step 543 after intervention start")
    schedule=load_schedule(preflight)
    base=sim.initialize(seed,a); events=[]; lineages=[]
    for t in range(1,branch_at+1):
        sim.tick(base,seed,"common",t,a,events,lineages)
    sim.select_target(base,a,seed,events,branch_at)
    for t in range(branch_at+1,start):
        sim.tick(base,seed,"sham",t,a,events,lineages)
    initial_hash=physical_hash(base)
    branches={}
    for mode in ("sham","target_block","offtarget_block"):
        s=copy.deepcopy(base)
        s["e014_control_schedule"]=schedule if mode=="offtarget_block" else {}
        if physical_hash(s)!=initial_hash: raise AssertionError("Initial physical states differ")
        ev=[]; ln=[]; snapshots=[]
        for t in range(start,inspect_end+1):
            sim.tick(s,seed,mode,t,a,ev,ln)
            if t>=inspect_start:
                snapshots.append(local_state(sim,s,t))
        pair=next(((x,y) for x,y in zip(snapshots,snapshots[1:])
                   if x["step"]==542 and y["step"]==543),None)
        if pair is None: raise AssertionError("Missing 542->543 transition")
        prev,now=pair
        before=set(prev["target_group"]["particle_ids"]) if prev["target_group"] else set()
        post_ids={pid for group in now["groups"] for pid in group["particle_ids"]}
        census_542 = prev["particle_identity_census"]
        census_543 = now["particle_identity_census"]
        fates = []
        for pid in sorted(before):
            p = str(pid)
            old = census_542.get(p)
            new = census_543.get(p)
            fates.append({
                "particle_id": pid,
                "present_at_542": old is not None,
                "survived_to_543": new is not None,
                "site_at_542": old["site"] if old else None,
                "site_at_543": new["site"] if new else None,
                "type_at_542": old["type"] if old else None,
                "type_at_543": new["type"] if new else None,
                "bond_degree_542": old["degree"] if old else None,
                "bond_degree_543": new["degree"] if new else None,
            })
        branches[mode]={
            "target_particle_fates_542_to_543": fates,
            "target_survivors_anywhere_543": sum(x["survived_to_543"] for x in fates),
            "target_survivors_isolated_543": sum(
                x["survived_to_543"] and x["bond_degree_543"] == 0 for x in fates
            ),
            "target_particles_disappeared_543": sum(
                not x["survived_to_543"] for x in fates
            ),
            "target_fid":s["target_flid"],
            "target_present_542":prev["target_present"],
            "target_present_543":now["target_present"],
            "target_size_542":prev["target_group"]["size"] if prev["target_group"] else 0,
            "target_particle_ids_still_in_bonded_groups_543":len(before&post_ids),
            "candidate_successors_543":successor_candidates(sim,prev,now),
            "global_particles_542":prev["particle_count"],
            "global_particles_543":now["particle_count"],
            "global_bonds_542":prev["bond_count"],
            "global_bonds_543":now["bond_count"],
            "snapshots":snapshots,
        }
    return {
        "schema":"abio-e014-fate-audit-v1",
        "seed":seed,
        "initial_matched_physical_hash":initial_hash,
        "intervention_start":start,
        "inspection_window":[inspect_start,inspect_end],
        "branches":branches,
        "interpretation":{
            "verified_extinction":False,
            "limitations":[
                "Loss of original tracked ID need not mean physical death.",
                "Successor rankings use post-hoc overlap and functional profile similarity.",
                "A split/merge can assign the original ID to only one child.",
                "Fixed rule table and spatial heuristics are not a formal RAF proof."
            ],
        },
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",type=Path,required=True)
    p.add_argument("--settings",type=Path,required=True)
    p.add_argument("--preflight",type=Path,required=True)
    p.add_argument("--seed",type=int,default=3)
    p.add_argument("--start",type=int,default=513)
    p.add_argument("--inspect-start",type=int,default=538)
    p.add_argument("--inspect-end",type=int,default=548)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    result=audit(load_sim(x.sim),json.loads(x.settings.read_text()),
                 json.loads(x.preflight.read_text()),x.seed,x.start,
                 x.inspect_start,x.inspect_end)
    result["provenance"]={
        "sim_sha256":hashlib.sha256(x.sim.read_bytes()).hexdigest(),
        "settings_sha256":hashlib.sha256(x.settings.read_bytes()).hexdigest(),
        "preflight_sha256":hashlib.sha256(x.preflight.read_bytes()).hexdigest(),
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "schema":result["schema"],
        "by_mode":{mode:{
            "target_present_542":v["target_present_542"],
            "target_present_543":v["target_present_543"],
            "target_size_542":v["target_size_542"],
            "target_particles_in_bonded_groups_543":v["target_particle_ids_still_in_bonded_groups_543"],
            "target_survivors_anywhere_543":v["target_survivors_anywhere_543"],
            "target_survivors_isolated_543":v["target_survivors_isolated_543"],
            "target_particles_disappeared_543":v["target_particles_disappeared_543"],
            "target_particle_fates":v["target_particle_fates_542_to_543"],
            "best_successors":v["candidate_successors_543"][:3],
            "global_particles_542":v["global_particles_542"],
            "global_particles_543":v["global_particles_543"],
            "global_bonds_542":v["global_bonds_542"],
            "global_bonds_543":v["global_bonds_543"]
        } for mode,v in result["branches"].items()},
        "output":str(x.out)
    },indent=2))


if __name__=="__main__": main()
