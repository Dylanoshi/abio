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


## Phase 3 — Source-dependent protection: focal catalytic deposition audit

**Prepared 2026-11-11, before obtaining Phase 3 results.** Following Phase 2's
matched checkpoint comparison (mean original-ID continuity: local 6.9935,
disabled 6.2163, shuffled 6.6447 across seeds 0–11), Phase 3 asks whether
ongoing protection is generated by the *same* organization whose continuity is
being measured, rather than by catalytic activity elsewhere.

### Design

For each seed, evolve the local-feedback substrate unchanged through step
300. At the checkpoint select exactly one eligible component using ONLY
information available at or before step 300. Eligibility: heuristic functional
age >=30, size >=3, and at least one potentially productive catalytic-bond
profile. Rank by realized catalytic births attributable to its functional ID
during steps 261–300 (descending), followed by age, size and lowest numeric
ID. Record zero recent activity and absence of eligible components rather
than silently dropping seeds or selecting retrospectively.

Deep-copy the *same full physical and field state* into four continuations
through step 600:

| Arm | Catalytic births | Protective field deposition |
|---|---|---|
| `all` | Unchanged | Every realized catalytic birth deposits |
| `no_new_field` | Unchanged | No new field; pre-existing field decays |
| `remove_focal_source` | Unchanged | Only nonfocal births deposit |
| `focal_source_only` | Unchanged | Only births assigned to focal ID deposit |

All arms retain local bond protection from the existing field and ordinary
bond formation, degradation, resource input, and catalysis. This changes ONLY
which successful catalytic births deposit additional protection. A field
deposit influences bond break thresholds **on later ticks**, never the same
birth tick. The rule is a **generic experimenter-designed substrate feature**.

Counterfactual evaluation: mean focal-lineage presence, motif-profile
similarity, retention of checkpoint constituent IDs, local field at currently
assigned focal component, initial loss of original focal ID, and number of
focal/nonfocal catalytic births and allowed or blocked protection deposits.
Record all 12 paired seed-level differences. The source-ablation effect is
**not identified** for seeds where zero focal deposits are actually suppressed;
report exposed and unexposed cases separately.

The focal-source classification uses `producer_fid` assigned by the existing
heuristic component tracker; splitting, merging and ID reassignment may
reclassify sources. A productive-bond profile indicates catalytic
*possibility*, not realized local RAF closure. Source-specific intervention
strengths are not rate-, mass-, or site-matched, so contrasts are diagnostic
rather than definitive attribution of autonomous self-maintenance.

### Run

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment015
python3 -m unittest -v test_source_ablation.py test_e015.py test_ablation.py

cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment015/source_ablation.py \
  --checkpoint 300 --end 600 \
  --out ~/abio/track2/rco002/experiment015/results/source_ablation.json
```

Do not interpret a preserved heuristic ID as verified organism maintenance.
A stronger subsequent test will examine actual material ancestry, catalytic
replenishment and damage repair with controls matched for total field mass.
Keep the original E015 first-pass negative/mixed results in the report.


## Phase 3 observations (2026-11-11)

All 12 E015 Phase 3 tests passed and 12 matched seed continuations
completed. Focal lineage mean present-steps /300: normal **77.0833**,
no-new-field **89.7500**, remove-focal-source **78.1667**, focal-only
**80.8333**. Mean normal provenance counts: **5.00 focal birth deposits**
versus **897.00 external birth deposits** per seed. Focal removal was
exposed in **11/12 seeds**, but normal-minus-focal-removed tracked
persistence differed only in seed 2 (+44 steps) and seed 7 (−57 steps),
and was zero in the other 10 seeds. This is **not evidence of a reliable
source-dependent self-maintenance advantage**. These are heuristic focal
lineages, and their numerical IDs can change on splits/merges.

## Phase 4 — Material bridge, catalytic provenance and actual bond exposure

Prepared **2026-11-12**, prior to observing Phase 4 outputs. This is a
**diagnostic observational audit**, not a new mechanism or intervention.

Use the same checkpoint and one focal group selected only by its
precheckpoint catalytic activity (past 40 steps), age and size. For
each seed, continue local feedback from step 301 to 600. The new
`ancestry_exposure_audit.py` records:

1. **Material bridge:** after each bond update, choose the connected
   component with greatest overlap of actual particle IDs with the
   previous traced component; ties are recorded as ambiguous, and a
   zero-overlap transition ends the trace. It can survive lineage-ID
   reassignment, but cannot establish functional continuity when every
   original particle disappears at once.
2. **Source attribution:** for every *realized* catalytic birth, classify
   its current connected source as `self_bridge` if assigned to the
   current material-bridge component, `neighboring` if its birth or
   catalyst sites touch the traced component, or `external` otherwise.
   Record source counts and the actual net protective-field gain after
   accounting for site-level caps. Precheckpoint field is `legacy`
   (unknown source).
3. **Field exposure:** for existing bonds in the previously traced
   component, log their actual break trials, whether any protection
   was present, whether their field contains contributions tagged
   `self_bridge`, and whether a same-draw removal of only the
   self-tagged field would have allowed a break. The last counter is
   a one-step threshold comparison with all other fields and draws
   fixed; it is **not** a full dynamic causal intervention.
4. **Checks:** per-site provenance sums must reproduce the simulation's
   protective field after every update; the instrumented trajectory
   must hash-match an independent, hook-free replay. No E011–E014 or
   production runner changes.

**Preregistered first audit:** seeds 0–11, 24×24, 600 steps,
checkpoint 300, same E015 parameters; no parameter tuning or
retrospective seed selection. Full per-step records are versioned JSON.

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment015
python3 -m unittest -v test_ancestry_exposure.py test_source_ablation.py test_e015.py test_ablation.py

cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment015/ancestry_exposure_audit.py \
  --checkpoint 300 --end 600 \
  --out ~/abio/track2/rco002/experiment015/results/ancestry_exposure.json
```

**Interpretation gate:** distinguish *local activity around a structure*
from *activity that is physically part of its material successor*.
A few attributable prevented bond breaks establish a narrow exposure
mechanism only; they do not prove that the structure produces its own
continuity. No inference of RAF closure, autopoiesis, spontaneous
life, reproduction or adaptive computation from these counts. Preserve
the negative/mixed prior stages and publication hold.


## Phase 5 — Dynamic material-bridge source ablation (planned 2026-11-12)

**Prior observations:** E015 Phase 4 recovered 177 self-bridge catalytic births
across the 12 focal trajectories versus 60 births credited to the frozen
functional ID in Phase 3. Across 12 seeds, the Phase 4 static same-draw field
audit attributed **10 avoided bond-break trials** (five seeds) to self-sourced
field on a material bridge. These are static counterfactual threshold results,
**not** a demonstration that dynamic source removal affects organizational
survival.

**Hypothesis:** ongoing protective-field deposition by the *materially bridged
successor* increases that successor's persistence and functional similarity to
its checkpoint configuration, relative to selective removal of its source.
The mechanism of protective-field production is designed, not emergently
invented.

**Prespecified data and procedure:** Seeds 0–11, 24×24 substrate, 600 steps,
all E015 defaults unchanged. All arms begin from exactly the same state at
the end of step 300 after locally coupled activity; focal selection is identical
to Phases 3/4 (prior 40-step births, then age, size, ID). Every tick after the
bond update and functional-group identification, track the connected group
with greatest material overlap to the prior selected group. Ambiguous splits
are reported; trace ends after zero material overlap. This choice is made
**within each arm's current state**, without inspecting future outcomes.

| Arm | Protection-field deposition after checkpoint |
|---|---|
| `sham` | All realized catalytic births (unchanged) |
| `dynamic_self_off` | All except births attributed to current material-bridge successor |
| `offtarget_control` | Keep all focal deposits; block each nonfocal deposit with a fixed Bernoulli probability calibrated from past 40-step focal/nonfocal production at checkpoint |
| `global_field_off` | Block all new deposits, allow existing field to decay |

Catalytic births, substrate resources, reaction rules, and original random
streams are **not directly inhibited**. Field suppression has a delayed physical
effect only from subsequent ticks; the first diverging tick retains the same
predeposit physical state.

**Dosing caveat:** The off-target control is *calibrated prospectively*
using only preintervention history, but actual suppressed deposit counts,
location, timing, field mass and consequent trajectories are **not guaranteed
matched**. Report both exposure counts, flag seeds where the intervention
did not actually affect a focal source, and report unequal dosing explicitly.
No causal self-maintenance conclusion if this control is poorly exposed or
poorly matched. Classification depends on heuristic material overlap and
the single chosen successor; merges may change identity in all arms.

**Outcome measures:** material-bridge present-steps, first material loss,
mean cosine similarity of its catalytic-pair motif profile with the
checkpoint, steps with an active productive motif, mean protective field at
its sites, source-labelled realized births, source-specific blocked/allowed
deposits, lineage-ID changes and ambiguous splits, paired seed-level effects.
Postbranch birth counts and deposition counts must reconcile exactly.

**Code and execution:**

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment015
python3 -m unittest -v test_dynamic_source_ablation.py test_ancestry_exposure.py test_source_ablation.py test_e015.py test_ablation.py

cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment015/dynamic_source_ablation.py \
  --checkpoint 300 --end 600 \
  --out ~/abio/track2/rco002/experiment015/results/dynamic_source_ablation.json
```

**Evidence gates:** Tests pass; fixed-checkpoint states identical; sham
observationally equals the original local trajectory; source accounting
reconciles with realized catalytic births; focal source suppression has
nonzero opportunity in enough seeds; off-target exposure differences are
quantified. Only then interpret source-sensitive differences in bridge
survival and function. No claims of verified RAF closure, autopoiesis,
self-maintenance, heredity or abiogenesis.
