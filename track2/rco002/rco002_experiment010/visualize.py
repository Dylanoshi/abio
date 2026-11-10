#!/usr/bin/env python3
"""E010 functional continuity visualizations. Requires matplotlib."""
import argparse,csv,json
from pathlib import Path
import matplotlib.pyplot as plt
MODES=('sham','target_block','control_block','product_scramble')
LABELS={'sham':'Sham','target_block':'Target blocked','control_block':'Other complex blocked','product_scramble':'Target products scrambled'}
def read(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',default='track2/rco002/experiment010/results');p.add_argument('--seed',type=int,default=0);a=p.parse_args();out=Path(a.results)
    sets={m:read(out/f'timeseries_seed{a.seed}_{m}.csv') for m in MODES}
    cfg=json.loads((out/'settings.json').read_text()); split=int(cfg['steps']*cfg['interrupt_fraction'])
    fields=[('particles','Population'),('target_functional_size','Tracked functional descendant size'),('target_functional_original_retained','Original particle IDs retained'),('target_functional_similarity','Catalytic motif similarity to branch point'),('target_functional_entered','Cumulative entrants to descendant'),('target_functional_departed','Cumulative departures from descendant')]
    fig,axs=plt.subplots(6,1,figsize=(11,15),sharex=True)
    for ax,(field,label) in zip(axs,fields):
        for mode in MODES:
            d=sets[mode];ax.plot([int(r['step']) for r in d],[float(r[field]) for r in d],label=LABELS[mode],lw=1.25)
        ax.axvline(split,color='gray',ls=':',lw=1);ax.set_ylabel(label);ax.grid(alpha=.15)
    axs[0].legend(ncol=2,fontsize=8);axs[-1].set_xlabel('Step');fig.suptitle(f'ABIO E010 · seed {a.seed} · branch at {split}')
    fig.tight_layout();fig.savefig(out/'functional_continuity.png',dpi=150);plt.close(fig)
    fig,axs=plt.subplots(3,1,figsize=(11,10),sharex=True)
    for ax,field,label in zip(axs,['bonds','catalytic_births','suppressed'],['Bonds','Cumulative catalytic births','Cumulative suppressed events']):
        for mode in MODES:
            d=sets[mode];ax.plot([int(r['step']) for r in d],[int(r[field]) for r in d],label=LABELS[mode],lw=1.25)
        ax.axvline(split,color='gray',ls=':',lw=1);ax.set_ylabel(label);ax.grid(alpha=.15)
    axs[0].legend(ncol=2,fontsize=8);axs[-1].set_xlabel('Step');fig.tight_layout();fig.savefig(out/'ecology_controls.png',dpi=150);plt.close(fig)
    print('SAVED',out/'functional_continuity.png');print('SAVED',out/'ecology_controls.png')
if __name__=='__main__':main()
