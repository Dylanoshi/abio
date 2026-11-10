#!/usr/bin/env python3
"""E012 posthoc closure search: network possibility versus realized catalytic ancestry.
Does NOT claim RAF, autopoiesis, or life. Uses E011 result files without modifying dynamics.
"""
import argparse, csv, json, itertools
from pathlib import Path
from collections import defaultdict, Counter

TYPES='ABCD'
def read_csv(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def write_csv(p, rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def scc(graph):
    idx=0;indices={};low={};stack=[];on=set();ans=[]
    def visit(v):
        nonlocal idx
        indices[v]=low[v]=idx;idx+=1;stack.append(v);on.add(v)
        for w in graph[v]:
            if w not in indices:visit(w);low[v]=min(low[v],low[w])
            elif w in on:low[v]=min(low[v],indices[w])
        if low[v]==indices[v]:
            group=[]
            while True:
                w=stack.pop();on.remove(w);group.append(w)
                if w==v:break
            ans.append(group)
    for v in graph:
        if v not in indices:visit(v)
    return ans

def rule_candidates(rules,seed):
    rx=[(key[0],key[1],product) for key,product in rules.items() if product is not None and product in TYPES]
    edges={i:set() for i in range(len(rx))}
    for i,(_,_,p) in enumerate(rx):
        for j,(a,b,_) in enumerate(rx):
            if p in (a,b):edges[i].add(j)
    rows=[]
    for component in scc(edges):
        if len(component)<2:continue
        reactants={x for i in component for x in rx[i][:2]}
        products={rx[i][2] for i in component}
        # Strongly connected reaction dependency does not imply fully supplied inputs.
        covered=reactants<=products
        rows.append(dict(seed=seed,rule_count=len(component),types=len(reactants|products),
                         reactants=''.join(sorted(reactants)),products=''.join(sorted(products)),
                         input_covered=int(covered),reactions=';'.join(sorted(''.join(rx[i][:2])+'>'+rx[i][2] for i in component))))
    # Search within SCCs too: a larger SCC can contain a closed subnetwork.
    for component in scc(edges):
        if len(component)<2 or len(component)>16: continue
        candidates=[]
        for n in range(2,len(component)+1):
            for subset in itertools.combinations(component,n):
                reagents={x for i in subset for x in rx[i][:2]}
                products={rx[i][2] for i in subset}
                if reagents <= products:
                    candidates.append(subset)
            if candidates:break
        for sub in candidates[:5]:
            rr={x for i in sub for x in rx[i][:2]};pp={rx[i][2] for i in sub}
            rows.append(dict(seed=seed,rule_count=len(sub),types=len(rr|pp),reactants=''.join(sorted(rr)),products=''.join(sorted(pp)), input_covered=1,reactions=';'.join(sorted(''.join(rx[i][:2])+'>'+rx[i][2] for i in sub)),subnetwork=1))
    return rows

def realized(events,seed,mode):
    births=sorted([r for r in events if r['seed']==str(seed) and r['mode']==mode and r['event']=='catalytic_birth'],key=lambda r:(int(r['step']),int(r['particle_id'])))
    producers={int(r['particle_id']):r for r in births}
    parents=defaultdict(list);children=defaultdict(list)
    for r in births:
        target=int(r['particle_id']);t=int(r['step'])
        for key in ('catalyst_a','catalyst_b'):
            pid=int(r[key])
            if pid in producers and int(producers[pid]['step'])<t:
                parents[target].append(pid);children[pid].append(target)
    # Actual catalytic lineages: descendants from produced particles used as catalysts.
    depth={};root={}
    for r in births:
        pid=int(r['particle_id']);pp=parents[pid]
        depth[pid]=1+max((depth.get(p,0) for p in pp),default=0)
        root[pid]=min((root.get(p,p) for p in pp),default=pid)
    reused={pid for pid in children}
    # Count ancestral feedback of *types*, not literal cycles in birth DAG.
    # Example: product of A-producing event later catalyzes another A-producing event.
    feedback=[]
    for child,pp in parents.items():
        for parent in pp:
            if producers[parent]['particle_type']==producers[child]['particle_type']:
                feedback.append((parent,child))
    return dict(seed=seed,mode=mode,catalytic_births=len(births),
                catalytically_born_particles_reused=len(reused),
                reuse_fraction=round(len(reused)/len(births),4) if births else 0,
                downstream_births_using_products=sum(bool(parents[int(r['particle_id'])]) for r in births),
                longest_catalytic_ancestry=max(depth.values(),default=0),
                same_type_regeneration_links=len(feedback),
                possible_self_regeneration_not_verified='yes')

def main():
    p=argparse.ArgumentParser();p.add_argument('--e011',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    source=Path(a.e011);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rulesfiles=sorted(source.glob('rules_seed*.json'))
    if not rulesfiles:raise SystemExit('No E011 rule files found. Run E011 first.')
    all_events=read_csv(source/'events.csv')
    network=[];activity=[];audit=[]
    summary=read_csv(source/'summary.csv')
    modes=sorted(set(row['mode'] for row in summary))
    for f in rulesfiles:
        seed=int(f.stem.split('seed')[1]); rules=json.loads(f.read_text())
        matches=rule_candidates(rules,seed);network.extend(matches)
        for mode in modes:
            act=realized(all_events,seed,mode);activity.append(act)
            exactfile=source/f'exact_network_seed{seed}_{mode}.csv'
            if exactfile.exists():
                exact=read_csv(exactfile)
                post=[r for r in exact if int(r['step'])>360]
                audit.append(dict(seed=seed,mode=mode,
                    strict_candidate_steps=sum(int(r['strict_candidate']) for r in post),
                    full_replacement_and_motifs=sum(int(r['founder_replacement']) and int(r['exact_motif_preservation']) for r in post),
                    verified_regenerative_incorporations=max((int(r['recent_regenerative_incorporations']) for r in post),default=0)))
    write_csv(out/'potential_cycles.csv',network)
    write_csv(out/'realized_ancestry.csv',activity)
    write_csv(out/'strict_e011_audit.csv',audit)
    eligible=sum(r['input_covered'] for r in network)
    stats=dict(seeds=len(rulesfiles),conditions=modes,structural_cycle_groups=len(network),
               input_covered_cycle_groups=eligible,
               maximal_realized_catalytic_ancestry=max((r['longest_catalytic_ancestry'] for r in activity),default=0),
               strict_candidate_steps_total=sum(r['strict_candidate_steps'] for r in audit),
               caveats=['Rule cycles are only possible reaction dependencies, not RAF sets or realized closure.',
                        'Event ancestry establishes actual product reuse but not continuous functional organization.',
                        'E011 selected-lineage criterion may miss a closure elsewhere in the system.',
                        'Seed0 full and sham may be identical; evaluate independent seeds, not conditions as independent trials.'])
    (out/'report.json').write_text(json.dumps(stats,indent=2))
    print('E012 REPORT',json.dumps(stats))
    print('POTENTIAL CLOSED RULE GROUPS')
    for r in network[:8]:print('CYCLE',json.dumps(r))
    for r in activity:print('ACTIVITY',json.dumps(r))
    print('OUTPUT',out.resolve())
if __name__=='__main__':main()
