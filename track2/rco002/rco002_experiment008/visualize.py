#!/usr/bin/env python3
"""Plot E008 trajectories and seed-zero spatial snapshots (requires matplotlib)."""
import argparse
import csv
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

MODES = ('full', 'sham', 'local_interrupt', 'catalysis_off')
COLORS = {'A': 2, 'B': 3, 'C': 4, 'D': 5}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--results', default='track2/rco002/experiment008/results')
    a = p.parse_args()
    root = Path(a.results)
    settings = json.loads((root / 'settings.json').read_text())
    side = settings['size']
    fig, axes = plt.subplots(4, 1, figsize=(12, 11), sharex=True)
    for mode in MODES:
        path = root / f'timeseries_seed0_{mode}.csv'
        with path.open() as f:
            rows = list(csv.DictReader(f))
        t = [int(r['step']) for r in rows]
        for ax, key in zip(axes, ('particles', 'bonds', 'catalytic_births', 'largest')):
            ax.plot(t, [int(r[key]) for r in rows], label=mode, linewidth=1.7)
    for ax, label in zip(axes, ('Active particles', 'Bonds', 'Cumulative catalytic births', 'Largest bonded component')):
        ax.set_ylabel(label)
        ax.grid(alpha=0.2)
        ax.axvline(int(settings['steps'] * settings['interrupt_fraction']), color='gray', linestyle=':', alpha=0.6)
    axes[0].legend(loc='upper right', fontsize=8, ncol=3)
    axes[-1].set_xlabel('Step')
    axes[0].set_title('ABIO RCO-002 E008 — seed 0')
    fig.tight_layout()
    fig.savefig(root / 'timeseries.png', dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(len(MODES), 5, figsize=(15, 13))
    cmap = ListedColormap(['white', '#dcb14b', '#199b91', '#366cc3', '#80848d', '#a27ab5'])
    for y, mode in enumerate(MODES):
        frames = json.loads((root / f'frames_{mode}.json').read_text())
        indices = [round(i * (len(frames) - 1) / 4) for i in range(5)]
        for x, index in enumerate(indices):
            frame = frames[index]
            arr = [[0] * side for _ in range(side)]
            for site in frame['nutrient']:
                arr[site // side][site % side] = 1
            for site, kind, _ in frame['cells']:
                arr[site // side][site % side] = COLORS[kind]
            ax = axes[y][x]
            ax.imshow(arr, cmap=cmap, vmin=0, vmax=5, interpolation='nearest')
            for i, j in frame['bonds']:
                ax.plot([i % side, j % side], [i // side, j // side], color='#e12c91', lw=1.0)
            ax.set_title(f'Step {frame["step"]}', fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])
            if x == 0:
                ax.set_ylabel(mode, fontsize=10)
    fig.suptitle('E008: gold = food; teal/blue/gray/purple = constituents; magenta = bonds')
    fig.tight_layout()
    fig.savefig(root / 'snapshots.png', dpi=140)
    plt.close(fig)
    print('SAVED', root / 'timeseries.png')
    print('SAVED', root / 'snapshots.png')


if __name__ == '__main__':
    main()
