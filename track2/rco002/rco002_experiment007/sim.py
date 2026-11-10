#!/usr/bin/env python3
"""ABIO RCO-002 E007: random catalytic reaction networks (not abiogenesis)."""
import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

TYPES = 'ABCD'
MODES = ('full', 'type_blind', 'bond_blind', 'catalysis_off', 'interrupted')


def neighbors(site, side):
    x, y = site % side, site // side
    if x:
        yield site - 1
    if x + 1 < side:
        yield site + 1
    if y:
        yield site - side
    if y + 1 < side:
        yield site + side


def components(cells, bonds):
    adjacent = {site: set() for site in cells}
    for a, b in bonds:
        if a in adjacent and b in adjacent:
            adjacent[a].add(b)
            adjacent[b].add(a)
    seen, result = set(), []
    for start in cells:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        member_sites = []
        while stack:
            site = stack.pop()
            member_sites.append(site)
            for other in adjacent[site] - seen:
                seen.add(other)
                stack.append(other)
        result.append(member_sites)
    return result


def write_csv(path, rows):
    if rows:
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


def run(seed, mode, args, out):
    side = args.size
    n = side * side
    # Common initialization and chemistry for every condition of one seed.
    init = random.Random(seed + 171)
    chem_rng = random.Random(seed + 202607)
    rng = random.Random(seed * 1009 + 12345)
    cells = {i: init.choice(TYPES) for i in range(n) if init.random() < args.initial_density}
    ids = {i: i + 1 for i in cells}
    next_id = n + 1
    nutrient = {i for i in range(n) if i not in cells and init.random() < 0.45}
    bonds = set()
    # Pair-specific random catalytic affordances. No cycle or organism is prescribed.
    rule = {(a, b): (chem_rng.choice(TYPES) if chem_rng.random() < args.rule_density else None)
            for a in TYPES for b in TYPES}
    rows, events, frames = [], [], []
    births = deaths = catalytic_births = background_births = 0
    bond_births = bond_deaths = 0

    def record(t):
        groups = components(cells, bonds)
        multi = [g for g in groups if len(g) > 1]
        rows.append(dict(seed=seed, mode=mode, step=t, particles=len(cells), nutrient=len(nutrient),
                         bonds=len(bonds), complexes=len(multi), largest=max((len(g) for g in groups), default=0),
                         births=births, deaths=deaths, catalytic_births=catalytic_births,
                         background_births=background_births, bond_births=bond_births,
                         bond_deaths=bond_deaths))
        if t % args.save_every == 0 or t == args.steps:
            frames.append(dict(step=t, cells=[[i, cells[i], ids[i]] for i in sorted(cells)],
                               nutrient=sorted(nutrient), bonds=[list(b) for b in sorted(bonds)]))

    record(0)
    for t in range(1, args.steps + 1):
        # The environment replenishes resources. Sites are capacity constrained.
        for _ in range(int(n * args.supply)):
            site = rng.randrange(n)
            if site not in cells:
                nutrient.add(site)

        # Unbonded constituents diffuse. Bonded particles are locally immobilized.
        degree = Counter(i for e in bonds for i in e)
        for _ in range(n // 2):
            i = rng.randrange(n)
            if i not in cells or degree[i] != 0:
                continue
            j = rng.choice(tuple(neighbors(i, side)))
            if j not in cells:
                cells[j] = cells.pop(i)
                ids[j] = ids.pop(i)

        # Stochastic bonds. A bonded pair is a catalyst candidate, not an organism.
        degree = Counter(i for e in bonds for i in e)
        for _ in range(n):
            i = rng.randrange(n)
            j = rng.choice(tuple(neighbors(i, side)))
            if i not in cells or j not in cells:
                continue
            edge = tuple(sorted((i, j)))
            if edge in bonds:
                if rng.random() < args.bond_break:
                    bonds.remove(edge)
                    degree[i] -= 1
                    degree[j] -= 1
                    bond_deaths += 1
            elif degree[i] < 2 and degree[j] < 2 and rng.random() < args.bond_form:
                bonds.add(edge)
                degree[i] += 1
                degree[j] += 1
                bond_births += 1

        # Catalysis: a local type pair may convert an adjacent food site into a new
        # constituent. Products can catalyze other conversions in later steps.
        # Rules are random; neither closure nor self-repair is hardcoded.
        if mode != 'catalysis_off' and not (mode == 'interrupted' and t > args.steps * 0.6):
            candidate_pairs = list(bonds) if mode != 'bond_blind' else [
                (i, j) for i in cells for j in neighbors(i, side) if j > i and j in cells]
            rng.shuffle(candidate_pairs)
            for a, b in candidate_pairs:
                if a not in cells or b not in cells or rng.random() >= args.catalysis_rate:
                    continue
                product = rule[(cells[a], cells[b])]
                if product is None:
                    continue
                sites = [k for endpoint in (a, b) for k in neighbors(endpoint, side)
                         if k not in cells and k in nutrient]
                if not sites:
                    continue
                k = rng.choice(sites)
                # Type-blind retains the same pair activation rules but destroys
                # the pair -> specific product relationship.
                produced = rng.choice(TYPES) if mode == 'type_blind' else product
                nutrient.remove(k)
                cells[k] = produced
                ids[k] = next_id
                events.append(dict(seed=seed, mode=mode, step=t, event='catalytic_birth',
                                   particle_id=next_id, particle_type=produced, site=k,
                                   catalyst_id_a=ids[a], catalyst_id_b=ids[b],
                                   catalyst_bonded=int(tuple(sorted((a, b))) in bonds)))
                next_id += 1
                births += 1
                catalytic_births += 1

        # Weak substrate background conversion tests whether catalytic production
        # differs from an otherwise near-identical noncatalytic ecology.
        for _ in range(n // 2):
            if rng.random() >= args.background_rate or not cells:
                continue
            i = rng.choice(tuple(cells))
            available = [k for k in neighbors(i, side) if k not in cells and k in nutrient]
            if not available:
                continue
            k = rng.choice(available)
            nutrient.remove(k)
            cells[k] = rng.choice(TYPES)
            ids[k] = next_id
            events.append(dict(seed=seed, mode=mode, step=t, event='background_birth',
                               particle_id=next_id, particle_type=cells[k], site=k,
                               catalyst_id_a='', catalyst_id_b='', catalyst_bonded=''))
            next_id += 1
            births += 1
            background_births += 1

        for i in list(cells):
            if rng.random() < args.decay:
                events.append(dict(seed=seed, mode=mode, step=t, event='death',
                                   particle_id=ids[i], particle_type=cells[i], site=i,
                                   catalyst_id_a='', catalyst_id_b='', catalyst_bonded=''))
                del cells[i]
                del ids[i]
                deaths += 1
        old = len(bonds)
        bonds = {e for e in bonds if e[0] in cells and e[1] in cells}
        bond_deaths += old - len(bonds)
        record(t)

    # Per-seed trajectories and frames support future longitudinal lineage analysis.
    write_csv(out / f'timeseries_seed{seed}_{mode}.csv', rows)
    if seed == 0:
        (out / f'frames_{mode}.json').write_text(json.dumps(frames))
    return rows[-1], events, rule


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--steps', type=int, default=600)
    p.add_argument('--size', type=int, default=24)
    p.add_argument('--save-every', type=int, default=12)
    p.add_argument('--initial-density', type=float, default=0.20)
    p.add_argument('--decay', type=float, default=0.008)
    p.add_argument('--supply', type=float, default=0.018)
    p.add_argument('--bond-form', type=float, default=0.075)
    p.add_argument('--bond-break', type=float, default=0.018)
    p.add_argument('--rule-density', type=float, default=0.65)
    p.add_argument('--catalysis-rate', type=float, default=0.14)
    p.add_argument('--background-rate', type=float, default=0.0015)
    p.add_argument('--out', default='track2/rco002/experiment007/results')
    a = p.parse_args()
    if a.size < 4 or a.steps < 1 or a.seeds < 1 or a.save_every < 1 or any(
        not 0 <= x <= 1 for x in (a.initial_density, a.decay, a.supply, a.bond_form,
                                   a.bond_break, a.rule_density, a.catalysis_rate, a.background_rate)):
        p.error('Invalid argument range')
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    all_events, summaries = [], []
    for seed in range(a.seeds):
        for mode in MODES:
            summary, events, rules = run(seed, mode, a, out)
            summaries.append(summary)
            all_events.extend(events)
            print('RESULT', json.dumps(summary), flush=True)
        (out / f'rules_seed{seed}.json').write_text(json.dumps({f'{a}{b}': v for (a, b), v in rules.items()}, indent=2))
    write_csv(out / 'summary.csv', summaries)
    write_csv(out / 'events.csv', all_events)
    (out / 'settings.json').write_text(json.dumps(vars(a), indent=2))
    print('OUTPUT', out.resolve())


if __name__ == '__main__':
    main()
