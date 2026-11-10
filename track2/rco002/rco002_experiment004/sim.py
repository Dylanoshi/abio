#!/usr/bin/env python3
"""RCO-002 E004: high-resolution seed-0 replay, local causal intervention.
Reimplements E003 step ordering; E003 untouched. Requires numpy/matplotlib for plots.
"""
import argparse, collections, csv, json, random
from pathlib import Path
EMPTY,FEED,WASTE=0,1,2
ACTIVE=(3,4,5)

def groups_of(g,n):
    seen=set(); out=[]
    for p,v in enumerate(g):
        if v not in ACTIVE or p in seen: continue
        q=[p];seen.add(p)
        for x in q:
            r,c=divmod(x,n)
            for y in (((r-1)%n)*n+c,((r+1)%n)*n+c,r*n+(c-1)%n,r*n+(c+1)%n):
                if y not in seen and g[y] in ACTIVE:seen.add(y);q.append(y)
        out.append(set(q))
    return sorted(out,key=len,reverse=True)

def setup(seed,n):
    rng=random.Random(seed*100003+91);N=n*n
    g=[EMPTY]*N;ids=[0]*N;sites=list(range(N));rng.shuffle(sites)
    for p in sites[:int(N*.16)]:g[p]=FEED
    for i,p in enumerate(sites[int(N*.16):int(N*.16)+18],1):g[p]=rng.choice(ACTIVE);ids[p]=i
    return rng,g,ids,19

def evolve(rng,g,ids,nextid,n,edges,rate,blocked=None):
    N=n*n;events=[]
    for _ in range(N//2):
        p=rng.randrange(N);r,c=divmod(p,n)
        q=r*n+(c+1)%n if rng.randrange(2)==0 else ((r+1)%n)*n+c
        g[p],g[q]=g[q],g[p];ids[p],ids[q]=ids[q],ids[p]
    for _ in range(N//2):
        p=rng.randrange(N)
        if g[p] not in ACTIVE:continue
        r,c=divmod(p,n)
        q=r*n+(c+1)%n if rng.randrange(2)==0 else ((r+1)%n)*n+c
        if g[q]!=FEED:continue
        choices=[j for i,j in edges if i==g[p]]
        if choices and rng.random()<rate:
            # Draw the same reaction RNG values in the intervention and control.
            product=rng.choice(choices)
            if blocked is not None and p in blocked:continue
            g[q]=product;ids[q]=nextid;nextid+=1;events.append((p,q,product))
    deaths=0
    for p in range(N):
        x=g[p]
        if x in ACTIVE and rng.random()<.012:g[p]=WASTE;ids[p]=0;deaths+=1
        elif x==WASTE and rng.random()<.07:g[p]=EMPTY
        elif x==EMPTY and rng.random()<.012:g[p]=FEED
    return nextid,events,deaths

def writecsv(path,rows):
    if not rows:return
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,default=0);ap.add_argument('--size',type=int,default=32)
    ap.add_argument('--steps',type=int,default=220);ap.add_argument('--intervene',type=int,default=144)
    ap.add_argument('--duration',type=int,default=30);ap.add_argument('--rate',type=float,default=.25)
    ap.add_argument('--out',default='track2/rco002/experiment004/results')
    a=ap.parse_args();assert 0<a.intervene<a.steps
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    erng=random.Random(a.seed+90871);edges=erng.sample([(i,j) for i in ACTIVE for j in ACTIVE],3)
    rng,g,ids,nextid=setup(a.seed,a.size)
    states={};rows=[];events=[];prior=None;tracked_ids=set();selected=None
    # Simulate to intervention with exact E003 RNG and transition ordering.
    for t in range(a.intervene):
        if t>=a.intervene-40:states[t]=g[:]
        nextid,ev,deaths=evolve(rng,g,ids,nextid,a.size,edges,a.rate)
        if t>=a.intervene-40:
            for p,q,v in ev:events.append(dict(step=t+1,source=p,target=q,product=v))
    clusters=groups_of(g,a.size);selected=clusters[0] if clusters else set()
    if not selected:raise RuntimeError('No active cluster at intervention step')
    tracked_ids={ids[p] for p in selected};initial_footprint=set(selected)
    baseline=(rng.getstate(),g[:],ids[:],nextid)
    # Spatial placebo: shift selected mask by half the grid width, preserving shape and size.
    n=a.size;placebo={r*n+(c+n//2)%n for p in selected for r,c in [divmod(p,n)]}
    allrows=[];snapshots={};intervention_events=[]
    for mode,mask in [('control',None),('local_block',selected),('placebo_block',placebo)]:
        rr=random.Random();rr.setstate(baseline[0]);gg=baseline[1][:];ii=baseline[2][:];nid=baseline[3]
        previous=selected;series=[];snaps={}
        for t in range(a.intervene,a.steps+1):
            cs=groups_of(gg,n);big=cs[0] if cs else set()
            # Follow descendants via maximum spatial overlap, not by always taking largest.
            match=max(cs,key=lambda c:len(c & previous),default=set())
            overlap=len(match & previous)
            if overlap==0:match=set()
            if match:previous=match
            present_ids={ii[p] for p in match}
            row=dict(mode=mode,step=t,active=sum(v in ACTIVE for v in gg),largest=len(big),tracked_cluster=len(match),tracked_original_ids=len(present_ids & tracked_ids),tracked_spatial_overlap=overlap,tracked_initial_footprint_overlap=len(match & initial_footprint))
            series.append(row);allrows.append(row)
            if t<=a.intervene+40 or t%4==0:snaps[t]=gg[:]
            if t==a.steps:break
            blocked=mask if t<a.intervene+a.duration else None
            nid,ev,deaths=evolve(rr,gg,ii,nid,n,edges,a.rate,blocked)
            if t<a.intervene+a.duration:
                intervention_events.append(dict(mode=mode,step=t+1,reactions=len(ev),deaths=deaths))
        snapshots[mode]=snaps
        print('RESULT',json.dumps({'mode':mode,'active_final':series[-1]['active'],'largest_final':series[-1]['largest'],'tracked_cluster_final':series[-1]['tracked_cluster'],'original_ids_remaining_in_tracked_cluster':series[-1]['tracked_original_ids']}))
    writecsv(out/'metrics.csv',allrows);writecsv(out/'intervention_events.csv',intervention_events)
    writecsv(out/'pre_intervention_reactions.csv',events)
    (out/'config.json').write_text(json.dumps(dict(vars(a),edges=edges,selected_sites=sorted(selected),placebo_sites=sorted(placebo),selected_size=len(selected),caveat='Local blockade uses a fixed footprint, not a moving cluster; comparisons diverge stochastically after intervention.'),indent=2))
    try:
        import numpy as np
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.animation import FuncAnimation,PillowWriter
    except ImportError as e:
        print('VISUALS_SKIPPED',e);return
    fig,axs=plt.subplots(3,1,figsize=(11,9),sharex=True)
    for mode in snapshots:
        data=[r for r in allrows if r['mode']==mode]
        for ax,k in zip(axs,['active','largest','tracked_original_ids']):ax.plot([r['step'] for r in data],[r[k] for r in data],label=mode)
    for ax,yl in zip(axs,['Active particles','Largest cluster','Original cluster IDs still present']):
        ax.set_ylabel(yl);ax.axvline(a.intervene,color='gray',ls='--',lw=1)
        ax.axvline(a.intervene+a.duration,color='gray',ls=':',lw=1)
    axs[0].legend();axs[-1].set_xlabel('Step');fig.suptitle(f'E004 seed {a.seed}: fixed-footprint catalytic blockade');fig.tight_layout();fig.savefig(out/'intervention_timeseries.png',dpi=150);plt.close(fig)
    cmap=ListedColormap(['#ffffff','#f2c45a','#777777','#128e87','#4361b0','#c05890'])
    times=[a.intervene,a.intervene+5,a.intervene+15,a.intervene+30,min(a.steps,a.intervene+60)]
    fig,axs=plt.subplots(3,len(times),figsize=(3*len(times),9),squeeze=False)
    for i,mode in enumerate(snapshots):
        for j,t in enumerate(times):
            actual=min(snapshots[mode],key=lambda z:abs(z-t))
            ax=axs[i,j];ax.imshow(np.array(snapshots[mode][actual]).reshape(n,n),cmap=cmap,vmin=0,vmax=5,interpolation='nearest');ax.set_xticks([]);ax.set_yticks([])
            if i==0:ax.set_title(f'Step {actual}')
            if j==0:ax.set_ylabel(mode)
    fig.suptitle('E004: full vs targeted footprint vs shifted-footprint placebo');fig.tight_layout();fig.savefig(out/'snapshots.png',dpi=140);plt.close(fig)
    times=sorted(set.intersection(*(set(x) for x in snapshots.values())))
    fig,axs=plt.subplots(1,3,figsize=(10,3.8));ims=[]
    for ax,mode in zip(axs,snapshots):
        im=ax.imshow(np.array(snapshots[mode][times[0]]).reshape(n,n),cmap=cmap,vmin=0,vmax=5,interpolation='nearest');ax.set_title(mode);ax.axis('off');ims.append(im)
    label=fig.suptitle('')
    def update(k):
        t=times[k];label.set_text(f'E004 seed {a.seed} | step {t}')
        for im,mode in zip(ims,snapshots):im.set_data(np.array(snapshots[mode][t]).reshape(n,n))
        return ims+[label]
    FuncAnimation(fig,update,frames=len(times),interval=100,blit=False).save(out/'animation.gif',writer=PillowWriter(fps=8))
    plt.close(fig)
    print('OUTPUT',out.resolve())
if __name__=='__main__':main()
