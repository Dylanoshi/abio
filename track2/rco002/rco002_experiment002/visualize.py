#!/usr/bin/env python3
"""Produce population time series, cluster time series, and lattice snapshots."""
import argparse,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='track2/rco002/experiment002/results');p.add_argument('--seed',type=int,default=0)
    a=p.parse_args();out=Path(a.out)
    with (out/'metrics.csv').open() as f:rows=list(csv.DictReader(f))
    modes=['full','reaction_off','shuffled']
    fig,axes=plt.subplots(2,1,figsize=(10,8),sharex=True)
    for mode in modes:
        subset=[r for r in rows if r['mode']==mode]
        times=sorted({int(r['step']) for r in subset})
        for ax,key in zip(axes,['active','largest_component']):
            vals=[np.mean([float(r[key]) for r in subset if int(r['step'])==t]) for t in times]
            ax.plot(times,vals,label=mode)
            ax.set_ylabel(key.replace('_',' ').title());ax.grid(alpha=.2)
    axes[0].legend();axes[1].set_xlabel('Simulation step')
    fig.suptitle('RCO-002 E002 | mean across seeds');fig.tight_layout();fig.savefig(out/'timeseries.png',dpi=160);plt.close(fig)
    files=sorted(out.glob(f'grid_full_seed{a.seed}_step*.txt'))
    if not files:raise SystemExit('No snapshot files found')
    steps=[int(f.stem.split('step')[-1]) for f in files]
    fig,axes=plt.subplots(3,len(steps),figsize=(3*len(steps),9),squeeze=False)
    from matplotlib.colors import ListedColormap,BoundaryNorm
    cmap=ListedColormap(['#f5f5f5','#f0c96a','#1d8f85','#4258aa','#555555'])
    norm=BoundaryNorm(np.arange(-.5,5.5),5)
    for i,mode in enumerate(modes):
        for j,step in enumerate(steps):
            f=out/f'grid_{mode}_seed{a.seed}_step{step:04d}.txt'
            s=f.read_text().strip();w=int(len(s)**.5)
            axes[i,j].imshow(np.array([int(c) for c in s]).reshape(w,w),cmap=cmap,norm=norm,interpolation='nearest')
            axes[i,j].set_xticks([]);axes[i,j].set_yticks([])
            if i==0:axes[i,j].set_title(f'Step {step}')
            if j==0:axes[i,j].set_ylabel(mode)
    fig.suptitle(f'RCO-002 E002 | spatial snapshots | seed {a.seed}\nwhite=empty, yellow=feedstock, teal=A, blue=B, gray=waste')
    fig.tight_layout();fig.savefig(out/'snapshots.png',dpi=160);plt.close(fig)
    print('SAVED',out/'timeseries.png');print('SAVED',out/'snapshots.png')
if __name__=='__main__':main()
