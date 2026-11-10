#!/usr/bin/env python3
"""Plot paired-branch aggregate and selected-lineage trajectories for E009."""
import argparse, csv
from pathlib import Path
import matplotlib.pyplot as plt

MODES=('sham','target_block','control_block')
COLORS={'sham':'#2457a6','target_block':'#bd4265','control_block':'#288369'}
LABELS={'sham':'Sham','target_block':'Target catalysis blocked','control_block':'Matched-complex blocked'}

def get(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--results',default='track2/rco002/experiment009/results')
    p.add_argument('--seed',type=int,default=0)
    a=p.parse_args();out=Path(a.results)
    d={m:get(out/f'timeseries_seed{a.seed}_{m}.csv') for m in MODES}
    intervention=round(int(d['sham'][-1]['step'])*.6)
    settings=out/'settings.json'
    if settings.exists():
        import json
        setting=json.loads(settings.read_text())
        intervention=int(setting['steps']*setting['interrupt_fraction'])
    fig,axs=plt.subplots(4,1,figsize=(11,12),sharex=True)
    fields=['particles','bonds','target_size','target_incorporated']
    titles=['Active constituents','Bonds','Selected lineage size (approximate, pre-reaction observation)','Cumulative products incorporated into selected lineage']
    for ax,field,title in zip(axs,fields,titles):
        for mode in MODES:
            data=d[mode]
            ax.plot([int(r['step']) for r in data],
                    [int(r[field]) for r in data],label=LABELS[mode],
                    color=COLORS[mode],lw=1.6)
        ax.axvline(intervention,ls=':',color='gray',lw=1)
        ax.set_ylabel(title);ax.grid(alpha=.2)
    axs[0].legend(fontsize=9)
    axs[-1].set_xlabel('Simulation step')
    fig.suptitle(f'ABIO E009 seed {a.seed}: matched post-intervention trajectories (intervention {intervention})')
    fig.tight_layout();fig.savefig(out/'timeseries.png',dpi=155);plt.close(fig)
    fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for mode in MODES:
        data=d[mode]
        steps=[int(r['step']) for r in data]
        axs[0].plot(steps,[int(r['target_original_retained']) for r in data],label=LABELS[mode],color=COLORS[mode])
        axs[1].plot(steps,[int(r['target_catalytic_births']) for r in data],label=LABELS[mode],color=COLORS[mode])
    axs[0].set_ylabel('Original constituents retained')
    axs[1].set_ylabel('Cumulative catalytic births attributed to lineage')
    for ax in axs:
        ax.axvline(intervention,ls=':',color='gray');ax.grid(alpha=.2)
    axs[0].legend(fontsize=9);axs[1].set_xlabel('Simulation step')
    fig.tight_layout();fig.savefig(out/'lineage_diagnostics.png',dpi=155);plt.close(fig)
    print('SAVED',out/'timeseries.png')
    print('SAVED',out/'lineage_diagnostics.png')

if __name__=='__main__': main()
