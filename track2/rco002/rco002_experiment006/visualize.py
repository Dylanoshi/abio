#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.animation import FuncAnimation,PillowWriter
p=argparse.ArgumentParser();p.add_argument('--out',default='track2/rco002/experiment006/results');p.add_argument('--size',type=int,default=32);a=p.parse_args();out=Path(a.out)
with open(out/'metrics.csv') as f:rows=list(csv.DictReader(f))
fig,axs=plt.subplots(3,1,figsize=(11,9),sharex=True)
for mode in ('full','composition_off','composition_shuffled','production_off'):
 data=[r for r in rows if int(r['seed'])==0 and r['mode']==mode]
 t=[int(r['step']) for r in data]
 for ax,k in zip(axs,['particles','bonds','largest']):ax.plot(t,[int(r[k]) for r in data],label=mode)
for ax,label in zip(axs,['Active particles','Bonds','Largest bonded component']):ax.set_ylabel(label);ax.grid(alpha=.2)
axs[0].legend();axs[-1].set_xlabel('Step');fig.suptitle('RCO-002 E006 | seed 0');fig.tight_layout();fig.savefig(out/'timeseries.png',dpi=150);plt.close(fig)
colors=ListedColormap(['#ffffff','#e9b949','#0e9488','#3265b8','#6e6e6e'])
def raster(frame):
 z=np.zeros((a.size,a.size),dtype=np.uint8)
 for i in frame['nutrient']:z[i//a.size,i%a.size]=1
 for i,t,_ in frame['cells']:z[i//a.size,i%a.size]={'A':2,'B':3,'C':4}[t]
 return z
def draw(ax,frame):
 ax.imshow(raster(frame),cmap=colors,vmin=0,vmax=4,interpolation='nearest')
 for i,j in frame['bonds']:
  ax.plot([i%a.size,j%a.size],[i//a.size,j//a.size],color='#db2777',lw=1.1)
 ax.set_xticks([]);ax.set_yticks([]);ax.set_title('Step '+str(frame['step']),fontsize=9)
frames={mode:json.loads((out/f'frames_{mode}.json').read_text()) for mode in ('full','composition_off','composition_shuffled','production_off')}
fig,axs=plt.subplots(4,5,figsize=(15,12))
for row,(mode,fr) in enumerate(frames.items()):
 indices=np.linspace(0,len(fr)-1,5,dtype=int)
 for col,ix in enumerate(indices):draw(axs[row,col],fr[ix])
 axs[row,0].set_ylabel(mode,fontsize=9)
fig.suptitle('RCO-002 E006 | white empty, gold resource, teal/blue/gray elements, magenta bonds');fig.tight_layout();fig.savefig(out/'snapshots.png',dpi=140);plt.close(fig)
fig,ax=plt.subplots(figsize=(6,6))
def animate(k):
 ax.clear();draw(ax,frames['full'][k]);return []
ani=FuncAnimation(fig,animate,frames=len(frames['full']),interval=120,blit=False)
ani.save(out/'animation.gif',writer=PillowWriter(fps=8));plt.close(fig)
for name in ('timeseries.png','snapshots.png','animation.gif'):print('SAVED',out/name)
