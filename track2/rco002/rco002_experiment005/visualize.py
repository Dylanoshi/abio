#!/usr/bin/env python3
import argparse,json,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.animation import FuncAnimation,PillowWriter
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--out',default='track2/rco002/experiment005/results');a=p.parse_args();out=Path(a.out)
with open(out/'metrics.csv') as f:rows=list(csv.DictReader(f))
fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True)
for mode in ('full','composition_off','composition_shuffled'):
    r=[x for x in rows if x['seed']=='0' and x['mode']==mode]
    axs[0].plot([int(x['step']) for x in r],[int(x['bonds']) for x in r],label=mode)
    axs[1].plot([int(x['step']) for x in r],[int(x['largest_complex']) for x in r],label=mode)
axs[0].set_ylabel('Bonds');axs[1].set_ylabel('Largest bonded complex');axs[1].set_xlabel('Step');axs[0].legend();fig.suptitle('RCO-002 E005: compositional chemistry | seed 0');fig.tight_layout();fig.savefig(out/'timeseries.png',dpi=150);plt.close(fig)
frames=json.loads((out/'frames_full.json').read_text());size=json.loads((out/'config_full.json').read_text())['size'];colors={'A':'#0d9488','B':'#3467bd','C':'#e3ae39'}
def draw(ax,frame):
    ax.set_xlim(-.5,size-.5);ax.set_ylim(size-.5,-.5);ax.set_aspect('equal');ax.set_facecolor('#f7f7f7');ax.set_xticks([]);ax.set_yticks([])
    cells={i:t for i,t,_ in frame['cells']}
    for typ in 'ABC':
        pos=[i for i,t in cells.items() if t==typ]
        if pos:ax.scatter([i%size for i in pos],[i//size for i in pos],s=22,c=colors[typ],marker='s',linewidths=0)
    segs=[[(a%size,a//size),(b%size,b//size)] for a,b in frame['bonds']]
    if segs:ax.add_collection(LineCollection(segs,colors='#a12874',linewidths=1.5,alpha=.9))
    ax.set_title(f"Step {frame['step']} | {len(frame['bonds'])} bonds",fontsize=9)
fig,axs=plt.subplots(2,3,figsize=(12,8));inds=np.linspace(0,len(frames)-1,6,dtype=int)
for ax,idx in zip(axs.flat,inds):draw(ax,frames[int(idx)])
fig.suptitle('Seed 0 | colored elements, magenta bonds');fig.tight_layout();fig.savefig(out/'snapshots.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(6,6))
def update(i):
    ax.clear();draw(ax,frames[i]);return []
ani=FuncAnimation(fig,update,frames=len(frames),interval=110,blit=False)
ani.save(out/'animation.gif',writer=PillowWriter(fps=9));plt.close(fig)
for name in ('timeseries.png','snapshots.png','animation.gif'):print('SAVED',out/name)
