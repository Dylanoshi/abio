# E015 — Local Catalytic Activity and Endogenous Structural Stabilization

**Status:** exploratory experimental protocol, locked before first reported data; code on `e014-candidate-audit-v1`, not merged.  
**Prepared:** 2026-11-11  
**Question:** Can local catalytic events create spatially organized histories of bond stabilization and thereby support longer-lived, continuously turning-over catalytic complexes than equivalent substrate conditions without spatially coupled stabilization?

## Mechanism and scientific limits

The underlying E011/E014 spatial particle simulator is preserved; E015 uses an **isolated copy** `e015_sim.py`. Particle types are A–D, with lattice bonds, supplied resources, birth, decay, and randomly drawn pair-reaction rules. This experiment changes only how break probabilities depend on a **generic activity field**.

Successful catalytic births deposit `field_gain=1.0` at both catalyst sites and the produced-particle site. Field levels are capped at 4.0, and retained at 0.80× each step. The field enters bond-break trials on **subsequent steps only** (avoiding same-step response to events that occur after bond update). For a bond at lattice sites i and j:

```
h = (field[i] + field[j]) / 2
p_break_local = p_break_baseline / (1 + 3.0 * h)
```

Each bond uses the **same random draw** under its seed/step/phase update convention; the field modifies the threshold, not the random-stream schedule. No candidate, organism, boundary, species, fitness, reproduction, or lifecycle objective is selected or encoded.

**Critical distinction:** The stabilizing feedback law is **designed**. The experiment tests whether a substrate containing this universal law develops self-reinforcing organizations from interactions. It does *not* demonstrate spontaneous invention of the law itself or fully autonomous life.

## Prespecified paired conditions

Each seed begins from identical initialized substrate and rules:

1. **Disabled:** catalytic births deposit field, but it does not modify break probability.
2. **Local:** accumulated field modifies the break probability near its source.
3. **Shuffled:** at each step, the identical multiset of field strengths is redistributed to uniformly shuffled lattice positions before bond breaking. Field production, cap and decay are otherwise identical.

This shuffled control preserves the local run's *own* accumulated field-mass distribution but **does not match realized activity across diverged trajectories**; feedback changes the subsequent reaction history. A stronger future matched-exposure design may be needed. It is not an exposure-count-matched randomized intervention on a common frozen state.

## Preregistered first-pass configuration

| Parameter | Value |
|---|---:|
| Seeds | 0–11 inclusive (12 independent initializations) |
| Conditions per seed | 3 |
| Simulation steps | 600 |
| Lattice | 24 × 24 |
| Initial particle density | 0.20 |
| Baseline decay probability | 0.008 |
| Nutrient supply | 0.018 |
| Background birth rate | 0.0015 |
| Bond formation | 0.075 |
| Bond breakage baseline | 0.018 |
| Rule density | 0.85 |
| Catalysis rate | 0.14 |
| Field gain / retention / cap | 1.0 / 0.8 / 4.0 |
| Protection strength | 3.0 |
| Primary reporting window | Steps 301–600 |

Baseline reaction parameters follow E013's high-rule-density/high-catalysis regime 05, but **E015's field mechanism and numeric settings are exploratory choices**. They are not derived from a measured biological chemistry. Don't tune them after looking at these results and then present the same runs as confirmatory.

## Defined measurements

**Mechanistic validation:** compare E015 disabled mode with E014 physical hashes at matching steps; verify null effect without catalysis, and verify that the field actually changes some bond-break trials.

**Primary descriptive endpoints:** candidate connected-component observations satisfying all four requirements: functional lineage age ≥30; cumulative ≥3 constituent entries; cumulative ≥3 departures; and ≥1 productive catalytic-bond motif. Count qualifying *steps* and *distinct tracked IDs*, report both; an ID may survive through splits/merges under heuristic rules.

**Secondary endpoints:** mean bonds, mean largest bonded complex (steps 301–600), maximum tracked age, total catalytic births, actually broken bonds, trials exposed to field, and breakages prevented in same-draw threshold comparison. Report all 12 paired seed-level differences, not just aggregate averages. Distinguish physical persistence from catalytic functionality.

**Evidence classification:** candidate observation, not formal RAF; active catalysis, not necessarily self-maintenance; structural turnover and motif retention, not confirmed heredity or reproduction. Neither a longer lifespan nor increased population of components alone constitutes life.

## Execution

Run verification before the sweep:

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment015
python3 -m unittest -v test_e015.py
```

Run all 12 prespecified seeds:

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment015/run.py \
  --out ~/abio/track2/rco002/experiment015/results/first_pass
```

Outputs: `results.json` (complete parameters, criteria, records and aggregation), `per_seed.csv`, and `timeseries_10step.json`. The runner prints per-mode progress lines and a compact final summary.

**Analysis gates:** Confirm disabled-trajectory parity and nonzero field exposure. If zero effective interventions occur, the experiment is uninformative about feedback. Inspect local-versus-shuffled *paired seed* differences before concluding that spatial coupling matters. If outcomes are not improved, record a negative result rather than silently adjusting the first-pass settings.

## Next stages (not part of first pass)

- Instrument *post-formation* interruption of locally generated field to test continued dependence of structures on their own catalysis.
- Distinguish chemically/spatially selective catalytic protection from global reductions in break rate.
- Trace material provenance and functional component continuity across fragmentation/repair.
- Introduce conservation or an energetic cost for protective activity to exclude free stabilization.
- Test formally specified RAF sets, food generation, compartment continuity and later reproduction, only after these prerequisites are measurable.

## Source comparison

The disabled E015 physics must exactly match `rco002_experiment014/e014_sim.py`. E011 and the production runner API are unchanged. This is a mechanism exploration, not a declaration of abiogenesis.


## First-pass observations (12 seeds, 2026-11-11)

All four E015 unit tests passed on the investigator's Mac, and all 36 first-pass
runs completed using the prespecified settings. The source output remains at
`~/abio/track2/rco002/experiment015/results/first_pass/results.json`;
the numbers below are **transcribed from the shared terminal report**, not
verified against a GitHub-archived raw output.

| Mean metric | Disabled | Local | Shuffled |
|---|---:|---:|---:|
| Bonds (steps 301–600) | 211.9800 | 212.8622 | 214.8173 |
| Largest bonded component | 12.4395 | 12.6191 | 12.8408 |
| Candidate observation-steps | 7922.0000 | 7901.8333 | 7975.5000 |
| Distinct candidate lineage IDs | 164.2500 | 159.5000 | 159.7500 |
| Maximum tracked age | 356.1667 | 395.9167 | 408.4167 |
| Actual bond breaks (full run) | 1012.6667 | 863.5833 | 903.4167 |
| Exposed bond trials (full run) | 0 | 26575.4167 | 24274.8333 |

The local arm saw fewer realized bond-break events than the disabled arm
(149.0834 fewer per seed on average), but **did not improve** the primary
candidate observation-step metric: local minus disabled = -20.1667;
local minus shuffled = -73.6667. Local exceeded disabled on candidate-steps
in 7/12 seeds, and exceeded shuffled in 5/12 seeds. This is a **mixed /
negative result for the proposed organization-level advantage**, not proof
of emergent self-maintenance.

The total number of breaks is affected by the number of bonds sampled and
activity history, so it is *not* a clean per-trial hazard ratio. Likewise,
counted observation-steps are serially correlated, often overlapping
component-level observations, **not independent individual organisms**.

## Phase 2 — predeclared follow-up: matched field interruption

To isolate post-formation dependency on continued spatial feedback, E015
Phase 2 starts **each seed** under local feedback through the end of step 300,
then deep-copies an *identical physical state and field* into three conditions:
continued local, disabled field effect, and shuffled field effect. We select
eligible bonded functional components at the checkpoint using only their
age (≥30), size (≥3) and nonempty catalytic-pair profile. Thus no candidate
is chosen based on its *future* survival.

No organism-specific repair or evolutionary objective is introduced. Branch
interventions apply globally, so improved persistence would demonstrate
dependence on a designed environment-level stabilizing law, not autonomous
regulation by a living individual.

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment015
python3 -m unittest -v test_ablation.py test_e015.py

cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment015/ablation.py \
  --checkpoint 300 --end 600 \
  --out ~/abio/track2/rco002/experiment015/results/field_ablation.json
```

Read `aggregate` and compare all 12 matched-seed records in the JSON.
The recorded functional IDs are heuristic; splitting/reassignment can produce
false apparent disappearance, and motif similarity is not a demonstration of
self-regeneration. Preserve the entire first-pass negative result without
retuning the same data.
