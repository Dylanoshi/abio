#!/usr/bin/env python3
"""E014 CONTROL VARIANT (single guarded off-target inhibition hook); based on E011: explicit reaction-motif continuity and causal product tracing.
E015 isolated mechanism variant: optional locally generated bond stabilization.\nNOT a demonstration of life, autopoiesis, or RAF closure.
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

def effective_break_rate(baseline, strength, local_value):
    """Global baseline modified by a nonnegative local catalytic activity field."""
    return baseline/(1.0+max(0.0,strength)*max(0.0,local_value))

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
                history=[],fprev={},fnext=1,fages={},site_flid={},fmembers={},fprofiles={},target_flid=None,control_flid=None,original_ids=set(),fseen=set(),fentered=Counter(),fdeparted=Counter(),functional_rows=[], motif_events=[], product_ancestry={}, incorporation_seen=set(), uptake_rows=[], exact_rows=[], e015_field={}, e015_stats=Counter(), e015_last_field={})

def functional_profile(s, sites):
    siteset=set(sites)
    counts=Counter()
    for u,v in s['bonds']:
        if u in siteset and v in siteset:
            x,y=s['cells'][u],s['cells'][v]
            # Functional fingerprint: only productive bonded catalyst pair types.
            prod=s['rule'].get((x,y))
            if prod is not None:
                counts[x+y+">"+prod]+=1
    return counts

def profile_similarity(p,q):
    import math
    keys=set(p)|set(q)
    if not keys:return 0.0
    den=math.sqrt(sum(v*v for v in p.values())*sum(v*v for v in q.values()))
    return sum(p.get(k,0)*q.get(k,0) for k in keys)/den if den else 0.0

def identify_functional(s,seed,mode,t):
    # Independent, heuristic tracking based on spatial adjacency, particle overlap,
    # and catalytic-bond signature, never requiring retention of founding IDs.
    current=[]
    for sites in components(s['cells'],s['bonds']):
        if len(sites)>1:
            ps={s['ids'][i] for i in sites}
            current.append((set(sites),ps,functional_profile(s,sites)))
    candidates=[]
    for gi,(site,ps,prof) in enumerate(current):
        for fid,old in s['fprev'].items():
            spatial=len(site & old['sites'])
            particle=len(ps & old['ids'])
            sim=profile_similarity(prof,old['profile'])
            # Continue only through a directly observable spatial or material bridge.
            # Motif similarity alone is insufficient for identity.
            if not spatial and not particle:continue
            overlap=max(spatial/max(len(site),len(old['sites'])),
                        particle/max(len(ps),len(old['ids'])))
            score=overlap+0.25*sim
            candidates.append((score,sim,spatial+particle,gi,fid))
    matched={}; used=set()
    for score,sim,overlap,gi,fid in sorted(candidates,reverse=True):
        if gi not in matched and fid not in used:
            matched[gi]=fid;used.add(fid)
    new={}; site_flid={}
    for gi,(site,ps,prof) in enumerate(current):
        fid=matched.get(gi)
        if fid is None:
            fid=s['fnext'];s['fnext']+=1;s['fages'][fid]=0
        old=s['fprev'].get(fid)
        s['fages'][fid]+=1
        if old:
            s['fentered'][fid]+=len(ps-old['ids'])
            s['fdeparted'][fid]+=len(old['ids']-ps)
        new[fid]=dict(sites=site,ids=ps,profile=prof)
        for i in site:site_flid[i]=fid
        is_target=fid==s['target_flid']
        s['functional_rows'].append(dict(seed=seed,mode=mode,step=t,
          functional_id=fid,age=s['fages'][fid],size=len(ps),
          original_retained=len(ps & s['original_ids']) if is_target else '',
          founding_particles_replaced=int(not bool(ps & s['original_ids'])) if is_target and s['original_ids'] else '',
          entered_cumulative=s['fentered'][fid],departed_cumulative=s['fdeparted'][fid],
          active_catalytic_motifs=sum(prof.values()),
          functional_similarity_to_branch=round(profile_similarity(prof,s['target_profile']),4) if is_target and s.get('target_profile') else '',
          fingerprint=json.dumps(dict(sorted(prof.items()))),is_target=int(is_target)))
    s['fprev']=new;s['fmembers']=new;s['site_flid']=site_flid

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
    identify_functional(s,seed,mode,t)
    # Detect actual product entry into a bonded component. A product only counts
    # as regenerative when it joins a component carrying the founding target
    # and participates in a BRANCH-DEFINED catalyst motif (not merely its vicinity).
    for pid, ancestor in list(s['product_ancestry'].items()):
        if pid in s['incorporation_seen']: continue
        pos=next((site for site,particle in s['ids'].items() if particle==pid),None)
        if pos is None: continue
        fid=s['site_flid'].get(pos)
        if fid is None: continue
        profile=s['fmembers'][fid]['profile']
        related=any(pos in edge and all(site in s['fmembers'][fid]['sites'] for site in edge)
                    and (s['cells'][edge[0]]+s['cells'][edge[1]]+'>'+str(s['rule'].get((s['cells'][edge[0]],s['cells'][edge[1]])))) in s.get('branch_motifs',set())
                    for edge in s['bonds'])
        s['incorporation_seen'].add(pid)
        s['uptake_rows'].append(dict(seed=seed,mode=mode,step=t,particle_id=pid,
            producer_fid=ancestor['producer_fid'],receiver_fid=fid,
            source_motif=ancestor['motif'],product_type=ancestor['type'],
            entered_target=int(fid==s['target_flid']),
            entered_branch_motif=int(fid==s['target_flid'] and related and ancestor['producer_fid']==s['target_flid'] and ancestor['motif'] in s.get('branch_motifs',set()))))

def select_target(s, a, seed, event_rows, t):
    eligible=[(s['ages'][lid],len(ps),-lid,lid) for lid,ps in s['members'].items()
              if len(ps)>=a.min_target_size and any(
                  functional_profile(s,sites).get(k,0)>0
                  for fid, info in s['fmembers'].items()
                  for sites in [info['sites']] if info['ids']==ps
                  for k in functional_profile(s,sites))]
    if not eligible: return
    target=max(eligible)[-1]
    others=[(abs(len(p)-len(s['members'][target])), -s['ages'][lid], lid)
            for lid,p in s['members'].items() if lid!=target and len(p)>=a.min_target_size]
    control=min(others)[-1] if others else None
    s['target_lid']=target; s['target_anchor']=set(s['members'][target])
    s['original_ids']=set(s['members'][target])
    s['target_flid']=next((fid for fid,m in s['fmembers'].items() if m['ids'] & s['original_ids']),None)
    s['target_profile']=dict(s['fmembers'][s['target_flid']]['profile']) if s['target_flid'] is not None else {}
    s['branch_motifs']=set(s['target_profile'])
    s['control_lid']=control
    s['control_anchor']=set(s['members'].get(control,()))
    s['control_flid']=next((fid for fid,m in s['fmembers'].items() if m['ids'] & s['control_anchor']),None)
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
    # E015: Past catalytic births accumulate a local, finite-lived state field.
    # ALL rules remain local and type-agnostic; no organism ID is privileged.
    old_field=s.get('e015_field',{})
    decay_factor=getattr(a,'field_retention',.80)
    s['e015_field']={i:v*decay_factor for i,v in old_field.items()
                     if v*decay_factor>=.01}
    active_field=s['e015_field']
    audit=s.get('e015_audit_hook')
    if audit is not None:
        audit('field_ready',s=s,t=t)
    if mode=='shuffled':
        # Permute the SAME accumulated field strengths to randomized locations,
        # preserving global protection mass while breaking spatial association.
        values=list(active_field.values())
        # Select uniformly from all lattice sites rather than permuting only
        # among already active locations, which would preserve spatial hotspots.
        positions=list(range(n))
        shuffle_rng=rng_for(seed,t,91)
        shuffle_rng.shuffle(positions)
        active_field=dict(zip(positions[:len(values)],values))
    elif mode=='disabled':
        active_field={}
    s['e015_last_field']=active_field
    rng=rng_for(seed,t,3)
    degree=Counter(i for e in bonds for i in e)
    for _ in range(n):
        i=rng.randrange(n);j=rng.choice(tuple(neighbors(i,a.size)))
        if i not in cells or j not in cells:continue
        e=tuple(sorted((i,j)))
        if e in bonds:
            draw=rng.random()
            strength=max(0.0,getattr(a,'protection_strength',3.0))
            local_value=(active_field.get(i,0.0)+active_field.get(j,0.0))/2.0
            effective_break=effective_break_rate(a.bond_break,strength,local_value)
            s['e015_stats']['break_trials']+=1
            if audit is not None:
                audit('bond_trial',s=s,t=t,sites=e,particle_ids=(ids[e[0]],ids[e[1]]),
                      draw=draw,threshold=effective_break,baseline=a.bond_break,
                      strength=strength)
            if local_value>.01:
                s['e015_stats']['exposed_trials']+=1
                if effective_break<=draw<a.bond_break:
                    s['e015_stats']['prevented_breaks']+=1
            if draw<effective_break:
                bonds.remove(e);degree[i]-=1;degree[j]-=1
                s['e015_stats']['actual_breaks']+=1
        elif degree[i]<2 and degree[j]<2 and rng.random()<a.bond_form:
            bonds.add(e);degree[i]+=1;degree[j]+=1
    identify(s,seed,mode,t,events,lineage_rows)
    if audit is not None:
        audit('after_identify',s=s,t=t)
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
        flid=s['site_flid'].get(x)
        if flid!=s['site_flid'].get(y):flid=None
        blocked=((mode=='target_block' and flid is not None and flid==s['target_flid']) or
                 (mode=='control_block' and flid is not None and flid==s['control_flid']))
        # E014-only active negative control: at scheduled steps suppress the
        # exactly identified off-target catalyst pair. The schedule is set
        # only in the new E014 counterfactual driver; E011 never sees it.
        if mode=='offtarget_block':
            scheduled=s.get('e014_control_schedule',{}).get(t,set())
            if (ia,ib) in scheduled and flid!=s.get('target_flid'):
                blocked=True
        # No branch is blocked until the common branch point.
        if mode=='product_scramble' and flid is not None and flid==s['target_flid']:
            # Preserve birth opportunity, site, timing and nutrient consumption,
            # but alter product identity; avoid inadvertently leaving it unchanged.
            product=TYPES[(TYPES.index(product)+1+mix(seed,t,ia,ib)% (len(TYPES)-1))%len(TYPES)]
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
        motif=cells[x]+cells[y]+'>'+product
        s['product_ancestry'][pid]=dict(producer_fid=flid,motif=motif,type=product)
        # E015 Phase 3: observational source tagging and *experiment-only*
        # ablation of activity-field deposits. Successful catalytic births
        # themselves still happen, with identical reaction rules and draws.
        # When absent, the policy is the exact historical all-deposit behavior.
        policy=s.get('e015_deposition_policy','all')
        focal=s.get('e015_focal_fid')
        source_is_focal=(focal is not None and flid==focal)
        if policy not in ('all','none','nonfocal_only','focal_only'):
            raise ValueError('Unknown E015 deposition policy')
        deposit=(policy=='all' or
                 (policy=='focal_only' and source_is_focal) or
                 (policy=='nonfocal_only' and not source_is_focal))
        source_key='focal' if source_is_focal else 'nonfocal'
        s['e015_stats']['catalytic_births_'+source_key]+=1
        if deposit:
            gain=getattr(a,'field_gain',1.0)
            cap=getattr(a,'field_cap',4.0)
            for site in (x,y,chosen):
                s['e015_field'][site]=min(cap,s['e015_field'].get(site,0.0)+gain)
            s['e015_stats']['deposited_births_'+source_key]+=1
        else:
            s['e015_stats']['blocked_deposits_'+source_key]+=1
        if audit is not None:
            audit('catalytic_event',s=s,t=t,producer_fid=flid,
                  catalyst_ids=(ia,ib),sites=(x,y,chosen),product_id=pid,
                  deposited=deposit)
        s['motif_events'].append(dict(seed=seed,mode=mode,step=t,producer_fid=flid,
            target_producer=int(flid is not None and flid==s['target_flid']),
            exact_branch_motif=int(motif in s.get('branch_motifs',set())),
            motif=motif,particle_id=pid,product_type=product))
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
        target_functional_id=s['target_flid'] if s['target_flid'] is not None else '',
        target_functional_size=len(s['fmembers'].get(s['target_flid'],{}).get('ids',())),
        target_functional_age=s['fages'].get(s['target_flid'],0),
        target_functional_original_retained=len(s['fmembers'].get(s['target_flid'],{}).get('ids',set()) & s['original_ids']),
        target_functional_similarity=round(profile_similarity(s['fmembers'].get(s['target_flid'],{}).get('profile',{}),s.get('target_profile',{})),4),
        target_functional_entered=s['fentered'][s['target_flid']],
        target_functional_departed=s['fdeparted'][s['target_flid']],
        control_lid=s['control_lid'] or '',control_size=len(control))
    s['history'].append(row)
    fid=s['target_flid']
    desc=s['fmembers'].get(fid)
    current=dict(desc['profile']) if desc else {}
    branch=s.get('branch_motifs',set())
    exact=branch & set(current)
    latest=[e for e in s['motif_events'] if e['target_producer'] and
            e['exact_branch_motif'] and t-a.activity_window < e['step'] <= t]
    uptake=[e for e in s['uptake_rows'] if e['entered_branch_motif'] and
            t-a.activity_window < e['step'] <= t]
    retained=len(desc['ids'] & s['original_ids']) if desc else 0
    strict=bool(desc and branch and exact==branch and retained==0 and latest and uptake)
    s['exact_rows'].append(dict(seed=seed,mode=mode,step=t,
        target_functional_id=fid or '',descendant_present=int(bool(desc)),
        branch_motifs=len(branch),preserved_motifs=len(exact),
        exact_motif_preservation=int(bool(branch) and exact==branch),
        original_retained=retained,founder_replacement=int(bool(desc) and retained==0),
        recent_branch_motif_births=len(latest),recent_regenerative_incorporations=len(uptake),
        strict_candidate=int(strict),
        current_fingerprint=json.dumps(current,sort_keys=True)))
    if audit is not None:
        audit('tick_end',s=s,t=t)

def simulate(seed, a, out):
    base=initialize(seed,a); common_events=[]; common_lineages=[]
    branch_at=int(a.steps*a.interrupt_fraction)
    for t in range(1,branch_at+1):
        tick(base,seed,'common',t,a,common_events,common_lineages)
    select_target(base,a,seed,common_events,branch_at)
    records=[]; summaries=[]; all_events=[]
    for mode in ('sham','target_block','control_block','product_scramble'):
        s=copy.deepcopy(base)
        events=[dict(e,mode=mode) for e in common_events]
        lineage_rows=[dict(e,mode=mode) for e in common_lineages]
        for row in s['history']:row['mode']=mode
        for t in range(branch_at+1,a.steps+1):
            tick(s,seed,mode,t,a,events,lineage_rows)
        write_csv(out/f'timeseries_seed{seed}_{mode}.csv',s['history'])
        write_csv(out/f'lineages_seed{seed}_{mode}.csv',lineage_rows)
        write_csv(out/f'functional_seed{seed}_{mode}.csv',s['functional_rows'])
        write_csv(out/f'exact_network_seed{seed}_{mode}.csv',s['exact_rows'])
        write_csv(out/f'product_ancestry_seed{seed}_{mode}.csv',s['motif_events'])
        write_csv(out/f'uptake_seed{seed}_{mode}.csv',s['uptake_rows'])
        summary=dict(s['history'][-1],target_functional_ever_full_replacement=int(any(r.get('is_target')==1 and r.get('founding_particles_replaced')==1 and r.get('active_catalytic_motifs',0)>0 for r in s['functional_rows'] if r.get('step',0)>branch_at)),target_age=s['ages'].get(s['target_lid'],0),
              target_selected=s['target_lid'] or '',control_selected=s['control_lid'] or '',
              target_ever_incorporated=s['incorporated'][s['target_lid']])
        post=[r for r in s['exact_rows'] if r['step']>branch_at]
        summary.update(strict_candidate_steps=sum(r['strict_candidate'] for r in post),
            exact_motif_full_replacement_steps=sum(r['founder_replacement'] and r['exact_motif_preservation'] for r in post),
            postbranch_target_motif_births=sum(e['target_producer'] and e['exact_branch_motif'] and e['step']>branch_at for e in s['motif_events']),
            postbranch_regenerative_incorporations=sum(e['entered_branch_motif'] and e['step']>branch_at for e in s['uptake_rows']),
            branch_motifs=len(s.get('branch_motifs',set())))
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
    p.add_argument('--activity-window',type=int,default=50)
    p.add_argument('--out',default='track2/rco002/experiment011/results')
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
