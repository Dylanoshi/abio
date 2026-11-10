#!/usr/bin/env python3
"""RCO-002 E001: minimal local reaction-diffusion particle substrate.
No organism templates, no fitness, no explicit reproduction.
"""
import argparse,csv,json,random
from pathlib import Path
from collections import Counter,deque

# States: 0 vacancy, 1 feedstock F, 2 active A, 3 active B, 4 waste W.
# Local cyclic catalysis: F+A -> B+A; F+B -> A+B. Both conserve occupancy.
# A/B decay to W; W becomes F through environmental recycling.
# Adjacent A/B can form a transient bond; bonded pairs have reduced mobility.
# Reaction, mobility and bonding can be disabled independently as controls.

DIRS=((1,0),(-1,0),(0,1),(0,-1))

def components(grid, w, h):
    seen=set(); sizes=[]; members=[]
    for k,v in enumerate(grid):
        if v not in (2,3) or k in seen: continue
        todo=[k]; seen.add(k); group=[]
        while todo:
            u=todo.pop(); group.append(u); x=u%w;y=u//w
            for dx,dy in DIRS:
                nx=(x+dx)%w;ny=(y+dy)%h;z=ny*w+nx
                if z not in seen and grid[z] in (2,3):seen.add(z);todo.append(z)
        sizes.append(len(group));members.append(group)
    return sizes,members

def run(seed, mode, steps, w, h, initial_density, sample_every):
    rng=random.Random(seed); n=w*h
    grid=[1 if rng.random()<initial_density else 0 for _ in range(n)]
    # Small random A/B inoculum, not a preassembled organization.
    for k in range(n):
        if grid[k]==1 and rng.random()<0.07:grid[k]=rng.choice((2,3))
    bonds=set(); metrics=[]; reaction_count=0; decay_count=0
    def nbr(k):
        x=k%w;y=k//w;dx,dy=rng.choice(DIRS)
        return ((y+dy)%h)*w+(x+dx)%w
    for t in range(steps+1):
        if t%sample_every==0 or t==steps:
            sizes,_=components(grid,w,h); counts=Counter(grid)
            metrics.append(dict(seed=seed,mode=mode,step=t,active=counts[2]+counts[3],a=counts[2],b=counts[3],feedstock=counts[1],waste=counts[4],largest_component=max(sizes,default=0),components=len(sizes),bonds=len(bonds),reactions=reaction_count,decays=decay_count))
        if t==steps:break
        # One sweep is n stochastic local updates.
        for _ in range(n):
            k=rng.randrange(n);j=nbr(k);p,q=grid[k],grid[j]
            # Generic pair transformations. Disabled in reaction-off control.
            if mode!='reaction_off' and ((p==1 and q in (2,3)) or (q==1 and p in (2,3))):
                if rng.random()<0.10:
                    if p==1:grid[k]=3 if q==2 else 2
                    else:grid[j]=3 if p==2 else 2
                    reaction_count+=1
            # Independent decay / recycling.
            if grid[k] in (2,3) and rng.random()<0.0009:
                grid[k]=4;decay_count+=1
            elif grid[k]==4 and rng.random()<0.025:grid[k]=1
            # Feedstock supply and losses are local stochastic environmental processes.
            if grid[k]==0 and rng.random()<0.005:grid[k]=1
            if grid[k]==1 and rng.random()<0.001:grid[k]=0
            # Diffusion: bonded pair slows mobility, but no identity is maintained.
            if rng.random()<0.20:
                if grid[k]!=grid[j] and rng.random()<(0.12 if (grid[k] in (2,3) and grid[j] in (2,3)) else 1):
                    grid[k],grid[j]=grid[j],grid[k]
        # Bonds are not implemented in E001: compositional state is explicitly deferred.
        # The reactive network is the only possible active maintenance mechanism here.
    return metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=5);ap.add_argument('--steps',type=int,default=400);ap.add_argument('--size',type=int,default=32);ap.add_argument('--density',type=float,default=.45);ap.add_argument('--sample-every',type=int,default=10);ap.add_argument('--out',default=str(Path.home()/'abio/track2/rco002/experiment001'))
    args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for seed in range(args.seeds):
        for mode in ('full','reaction_off'):
            rr=run(seed,mode,args.steps,args.size,args.size,args.density,args.sample_every)
            rows+=rr
            print('RESULT',json.dumps(rr[-1]),flush=True)
    with (out/'metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    (out/'config.json').write_text(json.dumps(vars(args),indent=2)+'\n')
    print('SAVED',out/'metrics.csv',flush=True)
if __name__=='__main__':main()
