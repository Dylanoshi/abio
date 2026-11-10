#!/usr/bin/env python3
"""RCO-002 E002: resource-limited catalytic lattice; no predefined organisms.
Modes: full, reaction_off, shuffled (active positions randomized each sweep).
Shuffled control preserves active A/B counts but destroys spatial continuity.
"""
import argparse,csv,json,random
from pathlib import Path
from collections import Counter
DIRS=((1,0),(-1,0),(0,1),(0,-1))

def component_stats(g,w):
    seen=set(); sizes=[]
    for i,v in enumerate(g):
        if v not in (2,3) or i in seen:continue
        todo=[i];seen.add(i);size=0
        while todo:
            u=todo.pop();size+=1;x=u%w;y=u//w
            for dx,dy in DIRS:
                j=((y+dy)%w)*w+(x+dx)%w
                if j not in seen and g[j] in (2,3):seen.add(j);todo.append(j)
        sizes.append(size)
    return max(sizes,default=0),len(sizes)

def run(seed,mode,steps,w,density,supply,decay,diffusion,sample_every,out):
    rng=random.Random(seed);n=w*w
    g=[1 if rng.random()<density else 0 for _ in range(n)]
    for k in range(n):
        if g[k]==1 and rng.random()<.07:g[k]=rng.choice((2,3))
    rows=[];reactions=0;decays=0
    frames={0,steps//4,steps//2,3*steps//4,steps}
    def neighbor(k):
        x=k%w;y=k//w;dx,dy=rng.choice(DIRS)
        return ((y+dy)%w)*w+(x+dx)%w
    for t in range(steps+1):
        if t in frames:
            (out/f'grid_{mode}_seed{seed}_step{t:04d}.txt').write_text(''.join(str(x) for x in g)+'\n')
        if t%sample_every==0 or t==steps:
            c=Counter(g);big,num=component_stats(g,w)
            rows.append(dict(seed=seed,mode=mode,step=t,active=c[2]+c[3],a=c[2],b=c[3],feedstock=c[1],waste=c[4],empty=c[0],largest_component=big,components=num,reactions=reactions,decays=decays))
        if t==steps:break
        for _ in range(n):
            k=rng.randrange(n);j=neighbor(k);p,q=g[k],g[j]
            if mode!='reaction_off' and ((p==1 and q in (2,3)) or (q==1 and p in (2,3))) and rng.random()<.10:
                if p==1:g[k]=3 if q==2 else 2
                else:g[j]=3 if p==2 else 2
                reactions+=1
            if g[k] in (2,3) and rng.random()<decay:g[k]=4;decays+=1
            elif g[k]==4 and rng.random()<.012:g[k]=0
            if g[k]==0 and rng.random()<supply:g[k]=1
            if g[k]==1 and rng.random()<.004:g[k]=0
            if rng.random()<diffusion and g[k]!=g[j]:g[k],g[j]=g[j],g[k]
        if mode=='shuffled':
            # Relocate all active particles among all lattice sites, preserving counts.
            active=[v for v in g if v in (2,3)]
            other=[v for v in g if v not in (2,3)]
            g=active+other;rng.shuffle(g)
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',type=int,default=5);p.add_argument('--steps',type=int,default=500)
    p.add_argument('--size',type=int,default=32);p.add_argument('--density',type=float,default=.20)
    p.add_argument('--supply',type=float,default=.0007);p.add_argument('--decay',type=float,default=.006)
    p.add_argument('--diffusion',type=float,default=.30);p.add_argument('--sample-every',type=int,default=10)
    p.add_argument('--out',default='track2/rco002/experiment002/results')
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for seed in range(a.seeds):
        for mode in ('full','reaction_off','shuffled'):
            rr=run(seed,mode,a.steps,a.size,a.density,a.supply,a.decay,a.diffusion,a.sample_every,out)
            rows.extend(rr);print('RESULT',json.dumps(rr[-1]),flush=True)
    with (out/'metrics.csv').open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=rows[0]);wr.writeheader();wr.writerows(rows)
    (out/'config.json').write_text(json.dumps(vars(a),indent=2)+'\n')
    print('SAVED',out/'metrics.csv',flush=True)
if __name__=='__main__':main()
