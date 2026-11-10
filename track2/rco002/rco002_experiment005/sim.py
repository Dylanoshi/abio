#!/usr/bin/env python3
"""RCO-002 E005: stochastic compositional chemistry, not a protocell model."""
import argparse,csv,json,random,collections
from pathlib import Path

TYPES='ABC'
NEIGH=((1,0),(-1,0),(0,1),(0,-1))

def components(bonds,types):
    adj={i:set() for i in types}
    for a,b in bonds:
        adj[a].add(b);adj[b].add(a)
    seen=set();out=[]
    for i in types:
        if i in seen:continue
        stack=[i];seen.add(i);part=set()
        while stack:
            v=stack.pop();part.add(v)
            for j in adj[v]-seen:seen.add(j);stack.append(j)
        out.append(part)
    return out

def run(seed,mode,steps,size,out,save_every):
    rng=random.Random(seed);n=size*size
    # one element per site, three inert types, plus empty sites; no organisms seeded
    cells={i:rng.choice(TYPES) for i in range(n) if rng.random()<0.28}
    ids={i:i+1 for i in cells};next_id=n+1
    bonds=set();events=[];metrics=[];frames=[]
    # Random interaction lookup tables, shared across conditions.
    rr=random.Random(seed+202605)
    pairs=[(a,b) for a in TYPES for b in TYPES]
    affinity={p:rr.random()<0.55 for p in pairs}
    # Generic neighbor transformations depend on whether a unit belongs to a complex.
    # A random table, not engineered for reciprocal closure.
    rules={(a,b,linked):rr.choice(TYPES) for a in TYPES for b in TYPES for linked in (0,1)}
    def neigh(i):
        x,y=i%size,i//size
        for dx,dy in NEIGH:
            xx,yy=x+dx,y+dy
            if 0<=xx<size and 0<=yy<size:yield yy*size+xx
    def degree(i):return sum(i in e for e in bonds)
    def snapshot(t):
        comps=components(bonds,cells)
        multi=[c for c in comps if len(c)>1]
        largest=max(map(len,comps),default=0)
        # only identity and composition tracked; spatial overlap is NOT lineage
        metrics.append(dict(step=t,mode=mode,particles=len(cells),bonds=len(bonds),complexes=len(multi),largest_complex=largest,
                            reactions=sum(e['event']=='transform' for e in events),formations=sum(e['event']=='bond' for e in events),
                            breakages=sum(e['event']=='break' for e in events)))
        if t%save_every==0 or t==steps:
            frames.append(dict(step=t,cells=[[i,cells[i],ids[i]] for i in sorted(cells)],bonds=[list(e) for e in sorted(bonds)]))
    snapshot(0)
    for t in range(1,steps+1):
        # Finite occupancy; random local exchanges conserve all particle material.
        for _ in range(n//3):
            i=rng.randrange(n);js=list(neigh(i));j=rng.choice(js)
            if i not in cells or j in cells or degree(i):continue
            cells[j]=cells.pop(i);ids[j]=ids.pop(i)
        # reversible bonds form between adjacent unbonded sites, degree capped at 2
        for _ in range(n//2):
            i=rng.randrange(n);js=list(neigh(i));j=rng.choice(js)
            if i not in cells or j not in cells:continue
            e=tuple(sorted((i,j)))
            if e in bonds:
                if rng.random()<0.018:
                    bonds.remove(e);events.append(dict(step=t,event='break',site=i,other=j,mode=mode))
            elif degree(i)<2 and degree(j)<2 and affinity[cells[i],cells[j]] and rng.random()<0.07:
                bonds.add(e);events.append(dict(step=t,event='bond',site=i,other=j,mode=mode))
        # Composition changes reaction products; disabled or randomized controls
        for _ in range(n//2):
            i=rng.randrange(n);js=list(neigh(i));j=rng.choice(js)
            if i not in cells or j not in cells:continue
            linked=int(degree(i)>0 or degree(j)>0)
            if mode=='composition_off':linked=0
            elif mode=='composition_shuffled':linked=rng.randrange(2)
            if rng.random()<0.035:
                old=cells[i];new=rules[(cells[i],cells[j],linked)]
                if new!=old:
                    cells[i]=new;events.append(dict(step=t,event='transform',site=i,other=j,mode=mode,old=old,new=new))
        # bond edges must still be valid adjacency and occupied
        bonds={e for e in bonds if all(k in cells for k in e) and e[1] in set(neigh(e[0]))}
        # Random spontaneous bond loss / environmental disturbances, no survival reward
        if t%40==0:
            for e in list(bonds):
                if rng.random()<0.08:
                    bonds.remove(e);events.append(dict(step=t,event='break',site=e[0],other=e[1],mode=mode))
        snapshot(t)
    return metrics,frames,events,dict(seed=seed,mode=mode,size=size,steps=steps,affinity={str(k):v for k,v in affinity.items()},rules={str(k):v for k,v in rules.items()},caveat='No material turnover or reproduction: only bond turnover and identity-preserving movement. No demonstrated organizational closure.')

def write_csv(path,rows):
    if not rows:return
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=5);p.add_argument('--steps',type=int,default=400);p.add_argument('--size',type=int,default=32);p.add_argument('--save-every',type=int,default=8);p.add_argument('--out',default='track2/rco002/experiment005/results');a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    allm=[];alle=[];summ=[]
    for seed in range(a.seeds):
        for mode in ('full','composition_off','composition_shuffled'):
            m,frames,events,cfg=run(seed,mode,a.steps,a.size,out,a.save_every)
            allm.extend([dict(seed=seed,**r) for r in m]);alle.extend([dict(seed=seed,**r) for r in events]);summ.append(dict(seed=seed,**m[-1]))
            if seed==0:
                (out/f'frames_{mode}.json').write_text(json.dumps(frames))
                (out/f'config_{mode}.json').write_text(json.dumps(cfg,indent=2))
            print('RESULT',json.dumps(dict(seed=seed,mode=mode,particles=m[-1]['particles'],bonds=m[-1]['bonds'],complexes=m[-1]['complexes'],largest_complex=m[-1]['largest_complex'])),flush=True)
    write_csv(out/'metrics.csv',allm);write_csv(out/'events.csv',alle);write_csv(out/'summary.csv',summ)
    print('OUTPUT',out.resolve())
if __name__=='__main__':main()
