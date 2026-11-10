#!/usr/bin/env python3
"""RCO-002 E006: compositional turnover screening; NOT an abiogenesis demonstration."""
import argparse, csv, json, random
from pathlib import Path
from collections import defaultdict
TYPES='ABC'
DIRECTIONS=((1,0),(-1,0),(0,1),(0,-1))
def neighbors(i,s):
 x,y=i%s,i//s
 for dx,dy in DIRECTIONS:
  xx,yy=x+dx,y+dy
  if 0<=xx<s and 0<=yy<s:yield yy*s+xx
def groups(cells,bonds):
 adj={i:set() for i in cells}
 for a,b in bonds:
  if a in adj and b in adj:adj[a].add(b);adj[b].add(a)
 seen=set();ans=[]
 for i in cells:
  if i in seen:continue
  stack=[i];seen.add(i);g=set()
  while stack:
   k=stack.pop();g.add(k)
   for j in adj[k]-seen:seen.add(j);stack.append(j)
  ans.append(g)
 return ans
def write_csv(path,rows):
 if not rows:return
 with open(path,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run(seed,mode,steps,size,save_every,decay,supply):
 rng=random.Random(seed+171); rr=random.Random(seed+202605);n=size*size
 cells={i:rng.choice(TYPES) for i in range(n) if rng.random()<0.20}
 ids={i:i+1 for i in cells}; next_id=n+1
 nutrient={i:1 for i in range(n) if i not in cells and rng.random()<0.22}
 bonds=set();events=[];frames=[];metrics=[];births=deaths=0
 affinity={(a,b):rr.random()<0.55 for a in TYPES for b in TYPES}
 rules={(a,b,c):rr.choice(TYPES) for a in TYPES for b in TYPES for c in (0,1)}
 # Random tables are fixed across modes. A bond-sensitive resource conversion is an imposed affordance.
 produce={(a,b,c):rr.random() < (0.12 if c else 0.035) for a in TYPES for b in TYPES for c in (0,1)}
 product_type={(a,b):rr.choice(TYPES) for a in TYPES for b in TYPES}
 def deg(i):return sum(i in e for e in bonds)
 def record(t):
  gs=groups(cells,bonds); multi=[g for g in gs if len(g)>1]
  metrics.append(dict(seed=seed,mode=mode,step=t,particles=len(cells),bonds=len(bonds),complexes=len(multi),largest=max(map(len,gs),default=0),nutrient=len(nutrient),births=births,deaths=deaths))
  if t%save_every==0 or t==steps:
   frames.append(dict(step=t,cells=[[i,cells[i],ids[i]] for i in sorted(cells)],bonds=[list(e) for e in sorted(bonds)],nutrient=sorted(nutrient)))
 record(0)
 for t in range(1,steps+1):
  # Nutrient supply: spatially uniform, finite per site. Environmental resource not a biological goal.
  for _ in range(int(n*supply)):
   i=rng.randrange(n)
   if i not in cells:nutrient[i]=1
  # Diffusion of unbonded particles, IDs conserved on movement.
  for _ in range(n//3):
   i=rng.randrange(n);j=rng.choice(tuple(neighbors(i,size)))
   if i in cells and j not in cells and not deg(i):
    cells[j]=cells.pop(i);ids[j]=ids.pop(i)
  # Bonds between adjacent particles, maximum degree 2.
  for _ in range(n//2):
   i=rng.randrange(n);j=rng.choice(tuple(neighbors(i,size)))
   if i not in cells or j not in cells:continue
   e=tuple(sorted((i,j)))
   if e in bonds:
    if rng.random()<0.018:bonds.remove(e)
   elif deg(i)<2 and deg(j)<2 and affinity[(cells[i],cells[j])] and rng.random()<0.07:bonds.add(e)
  # Reactions: type transformation and nutrient-to-component conversion.
  for _ in range(n//2):
   i=rng.randrange(n);j=rng.choice(tuple(neighbors(i,size)))
   if i not in cells or j not in cells:continue
   context=int(deg(i)>0 or deg(j)>0)
   if mode=='composition_off':context=0
   if mode=='composition_shuffled':context=rng.randrange(2)
   if rng.random()<0.035:cells[i]=rules[(cells[i],cells[j],context)]
   if mode!='production_off' and rng.random()<0.12:
    options=[k for k in neighbors(i,size) if k not in cells and k in nutrient]
    if options and produce[(cells[i],cells[j],context)]:
     k=rng.choice(options);nutrient.pop(k,None);cells[k]=(product_type[(cells[i],cells[j])] if mode=='structured' and tuple(sorted((i,j))) in bonds else rng.choice(TYPES));ids[k]=next_id;next_id+=1;births+=1
     events.append(dict(step=t,mode=mode,event='birth',site=k,particle_id=ids[k],parent_site=i))
  # Constituent degradation; bonded and unbonded constituents have identical baseline hazard.
  for i in list(cells):
   if rng.random()<decay:
    events.append(dict(step=t,mode=mode,event='death',site=i,particle_id=ids[i]))
    cells.pop(i);ids.pop(i);deaths+=1
  bonds={e for e in bonds if e[0] in cells and e[1] in cells and e[1] in set(neighbors(e[0],size))}
  if t%40==0:
   bonds={e for e in bonds if rng.random()>=0.08}
  record(t)
 return metrics,frames,events,dict(seed=seed,mode=mode,size=size,steps=steps,decay=decay,supply=supply,affinity={str(k):v for k,v in affinity.items()},rules={str(k):v for k,v in rules.items()},production={str(k):v for k,v in produce.items()},caveats=['Bond-dependent production is a designed affordance, not emergent metabolism.','Births are resource conversion by an imposed local rule, not autonomous reproduction.','Cluster tracking by graph connectivity is not organizational lineage.','Randomized-context control changes the distribution of reaction opportunities.'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=5);p.add_argument('--steps',type=int,default=400);p.add_argument('--size',type=int,default=32);p.add_argument('--save-every',type=int,default=8);p.add_argument('--decay',type=float,default=0.007);p.add_argument('--supply',type=float,default=0.018);p.add_argument('--out',default='track2/rco002/experiment006b/results');a=p.parse_args()
 if a.size<4 or not (0<=a.decay<=1) or not (0<=a.supply<=1):p.error('Invalid size, decay, or supply')
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 allm=[];alle=[];summary=[]
 for seed in range(a.seeds):
  for mode in ('full','composition_off','composition_shuffled','production_off','structured'):
   m,frames,events,config=run(seed,mode,a.steps,a.size,a.save_every,a.decay,a.supply)
   allm.extend(m);alle.extend(events);last=m[-1];summary.append(last)
   if seed==0:
    with open(out/f'frames_{mode}.json','w') as f:json.dump(frames,f)
   with open(out/f'config_seed{seed}_{mode}.json','w') as f:json.dump(config,f,indent=2)
   print('RESULT',json.dumps(last),flush=True)
 write_csv(out/'metrics.csv',allm);write_csv(out/'summary.csv',summary);write_csv(out/'events.csv',alle)
 print('OUTPUT',out.resolve())
if __name__=='__main__':main()
