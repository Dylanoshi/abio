#!/usr/bin/env python3
"""ABIO RCO-002 E009: paired-branch causal tests of bonded catalytic lineages.
Research instrument, NOT a demonstration of life, autopoiesis, or RAF closure.
"""
import argparse, copy, csv, json, random
from collections import Counter
from pathlib import Path

TYPES = 'ABCD'
MASK = (1 << 64) - 1

def mix(*xs):
    x = 0x9E3779B97F4A7C15
    for v in xs:
        x = (x ^ (int(v) + 0x9E3779B97F4A7C15 + ((x << 6) & MASK) + (x >> 2))) & MASK
    return x

def rng_for(seed, step, phase):
    return random.Random(mix(seed + 12345, step, phase))

def neighbors(i, side):
    x,y= i%side, i//side
    if x: yield i-1
    if x+1<side: yield i+1
    if y: yield i-side
    if y+1<side: yield i+side

def components(cells, bonds):
    adj={k:[] for k in cells}
    for a,b in bonds:
        if a in adj and b in adj:
            adj[a].append(b); adj[b].append(a)
    seen=set(); ans=[]
    for i in sorted(cells):
        if i in seen: continue
        stack=[i]; seen.add(i); group=[]
        while stack:
            j=stack.pop(); group.append(j)
            for k in adj[j]:
                if k not in seen: seen.add(k); stack.append(k)
        ans.append(group)
    return ans

def write_csv(path, rows):
    if not rows: return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def initialize(seed, a):
    n=a.size*a.size
    init=random.Random(seed+171); chem=random.Random(seed+202607)
    cells={i:init.choice(TYPES) for i in range(n) if init.random()<a.initial_density}
    ids={i:i+1 for i in cells}
    nutrient={i for i in range(n) if i not in cells and init.random()<.45}
    rule={(x,y):(chem.choice(TYPES) if chem.random()<a.rule_density else None)
          for x in TYPES for y in TYPES}
    return dict(cells=cells,ids=ids,nutrient=nutrient,bonds=set(),next_id=n+1,
                rule=rule,births=0,deaths=0,catalytic_births=0,background_births=0,
                suppressed=0,prev={},ages={},next_lid=1,site_lid={},members={},
                target_lid=None,control_lid=None,target_anchor=set(),control_anchor=set(),
                lineage_events=Counter(),incorporated=Counter(),products={},seen_uptake=set(),
                history=[])

def identify(s, seed, mode, t, event_rows, lineage_rows):
    curr=[]
    for sites in components(s['cells'],s['bonds']):
        if len(sites)>1:
            curr.append((set(s['ids'][i] for i in sites), sites))
    old=s['prev']
    owner={pid:lid for lid,m in old.items() for pid in m}
    candidates=[]
    for gi,(pids,_) in enumerate(curr):
        for lid,num in Counter(owner[p] for p in pids if p in owner).items():
            union=len(old[lid]|pids)
            candidates.append((num,num/union,-gi,-lid,gi,lid))
    matches={}; used=set()
    for n,sim,_,__,gi,lid in sorted(candidates,reverse=True):
        if gi not in matches and lid not in used:
            matches[gi]=(lid,n,sim); used.add(lid)
    new={}; site_lid={}
    for gi,(pids,sites) in enumerate(curr):
        if gi in matches:
            lid,ret,jac=matches[gi]; s['ages'][lid]+=1
        else:
            lid=s['next_lid']; s['next_lid']+=1
            s['ages'][lid]=1; ret=0; jac=0
        new[lid]=pids
        for i in sites: site_lid[i]=lid
        old_set=old.get(lid,set())
        types=Counter(s['cells'][i] for i in sites)
        pairs=Counter(''.join(sorted((s['cells'][u],s['cells'][v])))
                      for u,v in s['bonds'] if u in sites and v in sites)
        lineage_rows.append(dict(seed=seed,mode=mode,step=t,lineage_id=lid,
                size=len(pids),age=s['ages'][lid],retained=ret,
                entered=len(pids-old_set) if ret else 0,
                departed=len(old_set-pids) if ret else 0,
                jaccard=round(jac,4),types=json.dumps(dict(types),sort_keys=True),
                bond_pair_profile=json.dumps(dict(pairs),sort_keys=True),
                catalytic_births=s['lineage_events'][lid],
                incorporated_products=s['incorporated'][lid],
                is_target=int(lid==s['target_lid']),is_control=int(lid==s['control_lid'])))
    # Incorporation is counted only after a produced constituent joins a bonded
    # descendant carrying the producing lineage's persistent overlap identity.
    for lid,pids in new.items():
        for pid in pids:
            if pid not in s['seen_uptake'] and s['products'].get(pid)==lid:
                s['incorporated'][lid]+=1; s['seen_uptake'].add(pid)
                event_rows.append(dict(seed=seed,mode=mode,step=t,event='incorporation',
                    lineage_id=lid,particle_id=pid))
    s['prev']=new; s['members']=new; s['site_lid']=site_lid

def select_target(s, a, seed, event_rows, t):
    eligible=[(s['ages'][lid],len(ps),-lid,lid) for lid,ps in s['members'].items()
              if len(ps)>=a.min_target_size]
    if not eligible: return
    target=max(eligible)[-1]
    others=[(abs(len(p)-len(s['members'][target])), -s['ages'][lid], lid)
            for lid,p in s['members'].items() if lid!=target and len(p)>=a.min_target_size]
    control=min(others)[-1] if others else None
    s['target_lid']=target; s['target_anchor']=set(s['members'][target])
    s['control_lid']=control
    s['control_anchor']=set(s['members'].get(control,()))
    event_rows.append(dict(seed=seed,mode='common',step=t,event='selection',
        target_lineage=target,target_size=len(s['target_anchor']),
        control_lineage=control,control_size=len(s['control_anchor'])))

def tick(s,seed,mode,t,a,events,lineage_rows):
    n=a.size*a.size
    cells=s['cells']; ids=s['ids']; nut=s['nutrient']; bonds=s['bonds']
    rng=rng_for(seed,t,1)
    for _ in range(int(n*a.supply)):
        k=rng.randrange(n)
        if k not in cells: nut.add(k)
    rng=rng_for(seed,t,2)
    degree=Counter(i for e in bonds for i in e)
    for _ in range(n//2):
        i=rng.randrange(n)
        if i not in cells or degree[i]: continue
        j=rng.choice(tuple(neighbors(i,a.size)))
        if j not in cells:
            cells[j]=cells.pop(i);ids[j]=ids.pop(i)
    rng=rng_for(seed,t,3)
    degree=Counter(i for e in bonds for i in e)
    for _ in range(n):
        i=rng.randrange(n);j=rng.choice(tuple(neighbors(i,a.size)))
        if i not in cells or j not in cells:continue
        e=tuple(sorted((i,j)))
        if e in bonds:
            if rng.random()<a.bond_break:
                bonds.remove(e);degree[i]-=1;degree[j]-=1
        elif degree[i]<2 and degree[j]<2 and rng.random()<a.bond_form:
            bonds.add(e);degree[i]+=1;degree[j]+=1
    identify(s,seed,mode,t,events,lineage_rows)
    # Use stable pair-ID keyed random streams. In both branches every identical
    # catalyst pair sees the same activation and product-site draws; suppressing
    # a birth never consumes downstream unrelated random numbers.
    for x,y in sorted(bonds):
        if x not in cells or y not in cells:continue
        ia,ib=sorted((ids[x],ids[y]))
        r=random.Random(mix(seed+12345,t,4,ia,ib))
        if r.random()>=a.catalysis_rate:continue
        product=s['rule'][(cells[x],cells[y])]
        if product is None:continue
        candidates=sorted({k for endpoint in (x,y) for k in neighbors(endpoint,a.size)
                           if k not in cells and k in nut})
        if not candidates:continue
        chosen=r.choice(candidates)
        lid=s['site_lid'].get(x)
        if lid!=s['site_lid'].get(y):lid=None
        blocked=((mode=='target_block' and lid==s['target_lid']) or
                 (mode=='control_block' and lid==s['control_lid']))
        # No branch is blocked until the common branch point.
        if blocked:
            s['suppressed']+=1
            events.append(dict(seed=seed,mode=mode,step=t,event='suppressed',
                               lineage_id=lid,catalyst_a=ia,catalyst_b=ib,
                               product_type=product,site=chosen))
            continue
        nut.remove(chosen);cells[chosen]=product;ids[chosen]=s['next_id']
        pid=s['next_id'];s['next_id']+=1;s['births']+=1;s['catalytic_births']+=1
        if lid is not None:
            s['lineage_events'][lid]+=1;s['products'][pid]=lid
        events.append(dict(seed=seed,mode=mode,step=t,event='catalytic_birth',
            lineage_id=lid,particle_id=pid,particle_type=product,site=chosen,
            catalyst_a=ia,catalyst_b=ib))
    rng=rng_for(seed,t,5)
    for _ in range(n//2):
        if rng.random()>=a.background_rate or not cells:continue
        i=rng.choice(sorted(cells))
        avail=[k for k in neighbors(i,a.size) if k not in cells and k in nut]
        if not avail:continue
        k=rng.choice(avail);nut.remove(k);cells[k]=rng.choice(TYPES)
        ids[k]=s['next_id'];s['next_id']+=1;s['births']+=1;s['background_births']+=1
    # ID-keyed degradation: a constituent common to two branches has the same
    # baseline degradation draw in both branches at the same time.
    for i in sorted(list(cells)):
        if random.Random(mix(seed+12345,t,6,ids[i])).random()<a.decay:
            del cells[i];del ids[i];s['deaths']+=1
    s['bonds']={e for e in bonds if e[0] in cells and e[1] in cells}
    target=s['members'].get(s['target_lid'],set())
    control=s['members'].get(s['control_lid'],set())
    row=dict(seed=seed,mode=mode,step=t,particles=len(cells),bonds=len(s['bonds']),
        nutrient=len(nut),births=s['births'],deaths=s['deaths'],
        catalytic_births=s['catalytic_births'],background_births=s['background_births'],
        suppressed=s['suppressed'],target_lid=s['target_lid'] or '',
        target_size=len(target),target_original_retained=len(target&s['target_anchor']),
        target_incorporated=s['incorporated'][s['target_lid']],
        target_catalytic_births=s['lineage_events'][s['target_lid']],
        control_lid=s['control_lid'] or '',control_size=len(control))
    s['history'].append(row)

def simulate(seed, a, out):
    base=initialize(seed,a); common_events=[]; common_lineages=[]
    branch_at=int(a.steps*a.interrupt_fraction)
    for t in range(1,branch_at+1):
        tick(base,seed,'common',t,a,common_events,common_lineages)
    select_target(base,a,seed,common_events,branch_at)
    records=[]; summaries=[]; all_events=[]
    for mode in ('sham','target_block','control_block'):
        s=copy.deepcopy(base)
        events=[dict(e,mode=mode) for e in common_events]
        lineage_rows=[dict(e,mode=mode) for e in common_lineages]
        for row in s['history']:row['mode']=mode
        for t in range(branch_at+1,a.steps+1):
            tick(s,seed,mode,t,a,events,lineage_rows)
        write_csv(out/f'timeseries_seed{seed}_{mode}.csv',s['history'])
        write_csv(out/f'lineages_seed{seed}_{mode}.csv',lineage_rows)
        summary=dict(s['history'][-1],target_age=s['ages'].get(s['target_lid'],0),
              target_selected=s['target_lid'] or '',control_selected=s['control_lid'] or '',
              target_ever_incorporated=s['incorporated'][s['target_lid']])
        summaries.append(summary);all_events.extend(events)
        print('RESULT',json.dumps(summary),flush=True)
    (out/f'rules_seed{seed}.json').write_text(json.dumps({x+y:v for (x,y),v in base['rule'].items()},indent=2))
    return summaries,all_events

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=5)
    p.add_argument('--steps',type=int,default=600)
    p.add_argument('--size',type=int,default=24)
    p.add_argument('--initial-density',type=float,default=.20)
    p.add_argument('--decay',type=float,default=.008)
    p.add_argument('--supply',type=float,default=.018)
    p.add_argument('--bond-form',type=float,default=.075)
    p.add_argument('--bond-break',type=float,default=.018)
    p.add_argument('--rule-density',type=float,default=.65)
    p.add_argument('--catalysis-rate',type=float,default=.14)
    p.add_argument('--background-rate',type=float,default=.0015)
    p.add_argument('--interrupt-fraction',type=float,default=.60)
    p.add_argument('--min-target-size',type=int,default=3)
    p.add_argument('--out',default='track2/rco002/experiment009/results')
    a=p.parse_args()
    if a.seeds<1 or a.steps<2 or a.size<4 or a.min_target_size<2 or not 0<a.interrupt_fraction<1 or any(not 0<=v<=1 for v in (a.initial_density,a.decay,a.supply,a.bond_form,a.bond_break,a.rule_density,a.catalysis_rate,a.background_rate)):
        p.error('Invalid parameter range')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    summaries=[];events=[]
    for seed in range(a.seeds):
        ss,ee=simulate(seed,a,out);summaries.extend(ss);events.extend(ee)
    write_csv(out/'summary.csv',summaries);write_csv(out/'events.csv',events)
    (out/'settings.json').write_text(json.dumps(vars(a),indent=2))
    print('OUTPUT',out.resolve(),flush=True)
if __name__=='__main__':main()
