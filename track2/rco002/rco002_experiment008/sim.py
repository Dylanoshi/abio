#!/usr/bin/env python3
"""ABIO RCO-002 E008: complex lineage and selective interruption (not abiogenesis)."""
import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

TYPES = 'ABCD'
MODES = ('full', 'local_interrupt', 'sham', 'catalysis_off')


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
            fields = list(dict.fromkeys(k for row in rows for k in row))
            writer = csv.DictWriter(f, fieldnames=fields)
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
    rows, events, frames, lineage_rows = [], [], [], []
    prev_components = {}  # lineage id -> set of individual particle IDs
    next_lineage = 1
    current_components = {}  # lineage id -> current member IDs
    site_lineages = {}       # site -> lineage ID
    lineage_ages = {}
    lineage_births = Counter()       # catalytic products incorporated (ever)
    lineage_catalysis = Counter()    # catalytic births facilitated by component
    produced_by = {}  # particle ID -> source lineage at creation, if any
    counted_uptake = set()
    selected_lineage = None
    chosen_at_step = None
    target_initial_ids = set()
    suppressed = 0
    interruption_step = int(args.steps * args.interrupt_fraction)

    def update_lineages(t):
        nonlocal prev_components, next_lineage, current_components, site_lineages
        curr_groups = []
        for sites in components(cells, bonds):
            if len(sites) >= 2:
                curr_groups.append((set(ids[i] for i in sites), sites))
        # One-to-one identity-overlap matching. Split/merge ambiguity is logged;
        # this is a heuristic trajectory label, NOT established organizational identity.
        owner = {pid: lid for lid, members in prev_components.items() for pid in members}
        candidates = []
        predecessor_count = {}
        for gi, (members, _) in enumerate(curr_groups):
            counts = Counter(owner[pid] for pid in members if pid in owner)
            predecessor_count[gi] = len(counts)
            for lid, overlap in counts.items():
                union = len(members) + len(prev_components[lid]) - overlap
                candidates.append((overlap, overlap / union, gi, lid))
        candidates.sort(reverse=True)
        matches, used = {}, set()
        for overlap, jaccard, gi, lid in candidates:
            if gi not in matches and lid not in used:
                matches[gi] = (lid, overlap, jaccard)
                used.add(lid)
        new, mapping = {}, {}
        for gi, (members, sites) in enumerate(curr_groups):
            if gi in matches:
                lid, overlap, similarity = matches[gi]
                lineage_ages[lid] += 1
            else:
                lid, overlap, similarity = next_lineage, 0, 0
                next_lineage += 1
                lineage_ages[lid] = 1
            new[lid] = members
            for site in sites:
                mapping[site] = lid
            old_members = prev_components.get(lid, set())
            entering = len(members - old_members) if overlap else 0
            leaving = len(old_members - members) if overlap else 0
            lineage_rows.append(dict(seed=seed, mode=mode, step=t, lineage_id=lid,
                size=len(members), age=lineage_ages[lid], retained=overlap,
                entered=entering, departed=leaving,
                jaccard=round(similarity, 5),
                overlap_with_other_predecessors=max(0, predecessor_count[gi] - (1 if overlap else 0)),
                catalytic_events=lineage_catalysis[lid],
                incorporated_products=lineage_births[lid],
                selected=int(lid == selected_lineage)))
        # Uptake: produced particles that have subsequently joined any bonded
        # descendant of their producing lineage. Does not imply useful repair.
        for lid, members in new.items():
            for pid in members:
                if pid in produced_by and pid not in counted_uptake and produced_by[pid] == lid:
                    lineage_births[lid] += 1
                    counted_uptake.add(pid)
        current_components = new
        prev_components = new
        site_lineages = mapping

    births = deaths = catalytic_births = background_births = 0
    bond_births = bond_deaths = 0

    def record(t):
        groups = components(cells, bonds)
        multi = [g for g in groups if len(g) > 1]
        rows.append(dict(seed=seed, mode=mode, step=t, particles=len(cells), nutrient=len(nutrient),
                         bonds=len(bonds), complexes=len(multi), largest=max((len(g) for g in groups), default=0),
                         births=births, deaths=deaths, catalytic_births=catalytic_births,
                         background_births=background_births, bond_births=bond_births,
                         bond_deaths=bond_deaths, selected_lineage=(selected_lineage or ''),
                         target_size=len(current_components.get(selected_lineage, ())),
                         suppressed=suppressed))
        if t % args.save_every == 0 or t == args.steps:
            frames.append(dict(step=t, cells=[[i, cells[i], ids[i]] for i in sorted(cells)],
                               nutrient=sorted(nutrient), bonds=[list(b) for b in sorted(bonds)],
                               selected_lineage=selected_lineage, target_sites=sorted(site for site, lid in site_lineages.items() if lid == selected_lineage)))

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

        # Select a candidate AFTER bonding, at the intervention time, based only
        # on prior trajectory age and current size (no look-ahead). For sham and
        # intervention, the selection is identical before the intervention.
        update_lineages(t)
        if t == interruption_step and mode in ('local_interrupt', 'sham'):
            eligible = [(lineage_ages[lid], len(members), lid)
                        for lid, members in current_components.items()
                        if len(members) >= args.min_target_size]
            if eligible:
                _, _, selected_lineage = max(eligible)
                chosen_at_step = t
                target_initial_ids = set(current_components[selected_lineage])
                events.append(dict(seed=seed, mode=mode, step=t, event='selection',
                    particle_id='', particle_type='', site='', catalyst_id_a='',
                    catalyst_id_b='', catalyst_bonded='', lineage_id=selected_lineage))

        # Catalysis: a local type pair may convert an adjacent food site into a new
        # constituent. Products can catalyze other conversions in later steps.
        # Rules are random; neither closure nor self-repair is hardcoded.
        if mode != 'catalysis_off':
            candidate_pairs = list(bonds)
            rng.shuffle(candidate_pairs)
            for a, b in candidate_pairs:
                if a not in cells or b not in cells or rng.random() >= args.catalysis_rate:
                    continue
                # Target one bonded lineage, not all catalysis in the world.
                if (mode == 'local_interrupt' and t > interruption_step
                        and selected_lineage is not None
                        and site_lineages.get(a) == selected_lineage
                        and site_lineages.get(b) == selected_lineage):
                    suppressed += 1
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
                produced = product
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
                lid = site_lineages.get(a)
                if lid is not None and lid == site_lineages.get(b):
                    lineage_catalysis[lid] += 1
                    produced_by[next_id - 1] = lid

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
        # Count uptake only if a newly produced particle became bonded to
        # one of its catalyst lineage members in the current step. At birth,
        # E007 adds new particles unbonded, so such incorporation can only
        # happen on subsequent steps; we count it on first observed joining.
        # Recompute after deaths to avoid recording dead constituents.
        # Birth-to-lineage uptake is computed below from the lineage ledger.
        record(t)

    # Per-seed trajectories and frames support future longitudinal lineage analysis.
    write_csv(out / f'timeseries_seed{seed}_{mode}.csv', rows)
    write_csv(out / f'lineages_seed{seed}_{mode}.csv', lineage_rows)
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
    p.add_argument('--interrupt-fraction', type=float, default=0.60)
    p.add_argument('--min-target-size', type=int, default=3)
    p.add_argument('--out', default='track2/rco002/experiment008/results')
    a = p.parse_args()
    if a.size < 4 or a.steps < 1 or a.seeds < 1 or a.save_every < 1 or any(
        not 0 <= x <= 1 for x in (a.initial_density, a.decay, a.supply, a.bond_form,
                                   a.bond_break, a.rule_density, a.catalysis_rate, a.background_rate, a.interrupt_fraction)) or a.min_target_size < 2:
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
