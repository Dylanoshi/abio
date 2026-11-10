#!/usr/bin/env python3
"""RCO-002 E003: random catalytic networks, spatial controls, IDs and visualization."""
import argparse,csv,json,random,collections,math
from pathlib import Path

EMPTY,FEED,WASTE=0,1,2
ACTIVE=(3,4,5)

def components(grid,n):
    seen=set(); groups=[]
    for p,v in enumerate(grid):
        if v not in ACTIVE or p in seen: continue
        q=[p]; seen.add(p); group=[]
        for x in q:
            group.append(x)
            r,c=divmod(x,n)
            for y in ((r-1)%n*n+c,(r+1)%n*n+c,r*n+(c-1)%n,r*n+(c+1)%n):
                if y not in seen and grid[y] in ACTIVE: seen.add(y);q.append(y)
        groups.append(group)
    return sorted(groups,key=len,reverse=True)

def run(seed,mode,steps,n,rate,edges,snap_steps):
    rng=random.Random(seed*100003+91)
    N=n*n; grid=[EMPTY]*N; ids=[0]*N; nextid=1
    # Same initial configuration for all modes.
    sites=list(range(N));rng.shuffle(sites)
    for p in sites[:int(N*.16)]:grid[p]=FEED
    for p in sites[int(N*.16):int(N*.16)+18]:
        grid[p]=rng.choice(ACTIVE);ids[p]=nextid;nextid+=1
    # Isolate the intervention RNG so paired modes share environmental draws until divergence.
    active_edges=edges if mode!='reaction_off' else []
    if mode=='edge_ablation':active_edges=edges[:-1]
    snapshots={}; metrics=[]; prior_ids=set(); best_streak=0; streak=0; previous_footprint=set()
    for t in range(steps+1):
        groups=components(grid,n);big=groups[0] if groups else []
        big_ids={ids[p] for p in big}; overlap=len(big_ids & prior_ids)
        # This is descriptive only; not a lineage or proof of organizational identity.
        footprint=set(big)
        if previous_footprint and footprint and len(previous_footprint & footprint)/max(1,len(previous_footprint|footprint))>=.25:streak+=1
        else:streak=0
        best_streak=max(best_streak,streak)
        metrics.append(dict(step=t,active=sum(x in ACTIVE for x in grid),feed=sum(x==FEED for x in grid),waste=sum(x==WASTE for x in grid),largest=len(big),components=len(groups),largest_id_overlap=overlap,largest_spatial_streak=streak,distinct_active_ids=len({ids[p] for p in range(N) if grid[p] in ACTIVE})))
        prior_ids=big_ids;previous_footprint=footprint
        if t in snap_steps:snapshots[str(t)]={'grid':grid[:],'ids':ids[:]}
        if t==steps:break
        # Random local swaps: motion and diffusion, no type-specific attraction.
        for _ in range(N//2):
            p=rng.randrange(N);r,c=divmod(p,n)
            q=r*n+(c+1)%n if rng.randrange(2)==0 else ((r+1)%n)*n+c
            grid[p],grid[q]=grid[q],grid[p];ids[p],ids[q]=ids[q],ids[p]
        # Spatial shuffle breaks spatial history while preserving species counts and IDs.
        if mode=='shuffled':
            perm=list(range(N));rng.shuffle(perm)
            grid=[grid[p] for p in perm];ids=[ids[p] for p in perm]
        # Catalytic conversion: a catalyst of type i converts adjacent feed into type j.
        # Edges are generated at random; no reaction recognizes a cluster or organism.
        for _ in range(N//2):
            p=rng.randrange(N)
            if grid[p] not in ACTIVE:continue
            r,c=divmod(p,n)
            q=r*n+(c+1)%n if rng.randrange(2)==0 else ((r+1)%n)*n+c
            if grid[q]!=FEED:continue
            choices=[j for i,j in active_edges if i==grid[p]]
            if choices and rng.random()<rate:
                grid[q]=rng.choice(choices);ids[q]=nextid;nextid+=1
        # Turnover, resource inflow, waste removal; all local sites treated identically.
        for p in range(N):
            x=grid[p]
            if x in ACTIVE and rng.random()<.012:grid[p]=WASTE;ids[p]=0
            elif x==WASTE and rng.random()<.07:grid[p]=EMPTY
            elif x==EMPTY and rng.random()<.012:grid[p]=FEED
    return metrics,snapshots

def save_csv(path,rows):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def visuals(root,records,snaps,n,seed,steps):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.animation import PillowWriter,FuncAnimation
        import numpy as np
    except ImportError as e:
        print('VISUALS_SKIPPED: '+str(e)+'; install matplotlib numpy pillow')
        return
    fig,axs=plt.subplots(2,1,figsize=(10,7),sharex=True)
    for mode in ('full','shuffled','edge_ablation','reaction_off'):
        rows=[r for r in records if r['mode']==mode]
        if not rows:continue
        for ax,key in zip(axs,('active','largest')):
            ax.plot([r['step'] for r in rows],[r[key] for r in rows],label=mode)
    axs[0].set_ylabel('Active particles');axs[1].set_ylabel('Largest connected cluster')
    axs[1].set_xlabel('Step');axs[0].legend();fig.suptitle(f'E003 seed {seed} | randomized catalytic network')
    fig.tight_layout();fig.savefig(root/'timeseries.png',dpi=160);plt.close(fig)
    cmap=ListedColormap(['#ffffff','#f2c45a','#777777','#128e87','#4361b0','#c05890'])
    modes=('full','shuffled','edge_ablation','reaction_off')
    ts=sorted({int(t) for m in modes for t in snaps.get(m,{})})
    fig,axs=plt.subplots(len(modes),len(ts),figsize=(2.5*len(ts),2.6*len(modes)),squeeze=False)
    for i,m in enumerate(modes):
        for j,t in enumerate(ts):
            ax=axs[i,j];d=snaps.get(m,{}).get(str(t))
            if d:ax.imshow(np.array(d['grid']).reshape(n,n),cmap=cmap,vmin=0,vmax=5,interpolation='nearest')
            ax.set_xticks([]);ax.set_yticks([])
            if i==0:ax.set_title(f'Step {t}')
            if j==0:ax.set_ylabel(m)
    fig.suptitle('E003 spatial snapshots | white empty, gold resource, gray waste, colors active')
    fig.tight_layout();fig.savefig(root/'snapshots.png',dpi=150);plt.close(fig)
    # Animated time slices are saved at the recorded snapshot cadence, not every simulator step.
    fig,axs=plt.subplots(1,2,figsize=(8,4))
    imgs=[]
    for ax,m in zip(axs,('full','shuffled')):
        im=ax.imshow(np.zeros((n,n)),cmap=cmap,vmin=0,vmax=5,interpolation='nearest');ax.set_title(m);ax.axis('off');imgs.append(im)
    title=fig.suptitle('')
    def update(k):
        t=ts[k];title.set_text(f'E003 seed {seed} | step {t}')
        for im,m in zip(imgs,('full','shuffled')):
            d=snaps.get(m,{}).get(str(t))
            if d:im.set_data(np.array(d['grid']).reshape(n,n))
        return imgs+[title]
    anim=FuncAnimation(fig,update,frames=len(ts),interval=400,blit=False)
    try:anim.save(root/'animation.gif',writer=PillowWriter(fps=3))
    except Exception as e:print('GIF_SKIPPED:',e)
    plt.close(fig)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=5);ap.add_argument('--steps',type=int,default=500);ap.add_argument('--size',type=int,default=32);ap.add_argument('--rate',type=float,default=.25);ap.add_argument('--out',default='track2/rco002/experiment003/results');args=ap.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=True)
    allrows=[];summ=[]
    snap_steps=set(range(0,args.steps+1,max(1,args.steps//30)))|{args.steps}
    for seed in range(args.seeds):
        # Three randomly sampled catalytic transformations, no guaranteed cycles.
        erng=random.Random(seed+90871)
        edges=erng.sample([(i,j) for i in ACTIVE for j in ACTIVE],3)
        (root/f'network_seed{seed}.json').write_text(json.dumps({'seed':seed,'edges':edges,'ablated_edge':edges[-1]},indent=2))
        snapshots_by_mode={};seedrows=[]
        for mode in ('full','shuffled','edge_ablation','reaction_off'):
            rows,snaps=run(seed,mode,args.steps,args.size,args.rate,edges,snap_steps)
            snapshots_by_mode[mode]=snaps
            for r in rows:r.update(seed=seed,mode=mode)
            seedrows+=rows;allrows+=rows
            final=rows[-1]
            summ.append({'seed':seed,'mode':mode,'active':final['active'],'largest':final['largest'],'components':final['components'],'max_spatial_streak':max(x['largest_spatial_streak'] for x in rows),'edges':str(edges)})
            print('RESULT',json.dumps(summ[-1]))
        if seed==0:
            (root/'snapshots_seed0.json').write_text(json.dumps(snapshots_by_mode))
            visuals(root,seedrows,snapshots_by_mode,args.size,seed,args.steps)
    save_csv(root/'metrics.csv',allrows);save_csv(root/'summary.csv',summ)
    (root/'config.json').write_text(json.dumps(vars(args),indent=2))
    print('OUTPUT',root.resolve())
if __name__=='__main__':main()
