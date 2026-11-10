#!/usr/bin/env python3
"""E011 strict catalytic network diagnostics. Requires matplotlib."""
import csv, argparse, json
from pathlib import Path
import matplotlib.pyplot as plt
MODES=('sham','target_block','control_block','product_scramble')
LABEL={'sham':'Sham','target_block':'Target blocked','control_block':'Other complex blocked','product_scramble':'Product scrambled'}
def read(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',default='track2/rco002/experiment011/results');ap.add_argument('--seed',type=int,default=0);a=ap.parse_args();out=Path(a.results)
    config=json.loads((out/'settings.json').read_text());split=int(config['steps']*config['interrupt_fraction'])
    fields=[('descendant_present','Tracked descendant present'),('preserved_motifs','Exact branch motifs present'),('original_retained','Founding particle IDs retained'),('recent_branch_motif_births','Branch-motif births in recent window'),('recent_regenerative_incorporations','Regenerative incorporation in recent window'),('strict_candidate','Strict candidate (all criteria)')]
    fig,axs=plt.subplots(len(fields),1,figsize=(11,14),sharex=True)
    for ax,(field,label) in zip(axs,fields):
        for m in MODES:
            rows=read(out/f'exact_network_seed{a.seed}_{m}.csv');rows=[r for r in rows if int(r['step'])>=split]
            ax.plot([int(r['step']) for r in rows],[float(r[field] or 0) for r in rows],label=LABEL[m],lw=1.1)
        ax.axvline(split,color='gray',ls=':',lw=1);ax.set_ylabel(label);ax.grid(alpha=.18)
    axs[0].legend(ncol=2,fontsize=8);axs[-1].set_xlabel('Simulation step');fig.suptitle(f'ABIO E011 strict reaction-network audit — seed {a.seed}')
    fig.tight_layout();fig.savefig(out/'reaction_network_audit.png',dpi=150);plt.close(fig)
    print('SAVED',out/'reaction_network_audit.png')
if __name__=='__main__':main()
