# E014: Retrospective candidate audit (phase 1)

This experiment is a **read-only audit**, not a new simulation or a demonstration of life. It scans the existing E011 event-level `exact_network_seed*_*.csv` evidence for the six E013 regimes and compares post-branch candidate intervals across matched modes.

**Methodological repair:** E012 currently hard-codes `step > 360` for its retrospective screening regardless of the actual `steps * interrupt_fraction` value. The E014 audit derives the actual branch step from each regime's `e011/settings.json`. E012's published summaries remain unchanged; discrepancies must be reported, not silently rewritten.

## Run against a previously completed local E013 batch

```bash
cd ~/abio
python3 track2/rco002/rco002_experiment014/audit.py \
  --batch-dir track2/rco002/remote_batches/batch_d23012657c7d41e6ba18 \
  --out track2/rco002/experiment014/results/e013_candidate_audit.json
```

The output is a versioned machine-readable `abio-e014-candidate-audit-v1` report; it does not yet go through the campaign execution API. It is intentionally not integrated into the API until checked against existing outputs.

## Verification

```bash
cd track2/rco002/rco002_experiment014
python3 -m unittest -v test_audit.py
```

## Interpretation

- The number of candidate **steps** is not the number of independent organizations or replications.
- Sham, target-blocked, control-blocked and product-scrambled results must be examined as **matched branches** rather than independent seeds.
- A candidate seen only in a control intervention cannot be treated as a positive sham or as proof of rescue.
- The current E011 simulator deep-copies state at the intervention branch but does **not** persist a complete checkpoint containing all organization-level identity/provenance for replay. Exact historical candidate replay is therefore not claimed.
- A positive strict-candidate counter does **not** demonstrate organization-specific regenerative causality.
- This stage does not select a candidate ID or evaluate independent replications, intervention specificity, or mechanistic self-maintenance. Those belong to a subsequent E014 implementation phase.

## Next implementation phase

Add versioned pre-intervention checkpoints, intervention-time organization identity, event-level causal traces, and preregistered outcome criteria. Maintain backward compatibility and test determinism before offering E014 through the remote batch API.


## Phase 2: matched short-horizon intervention from immediately before E013 event

`short_horizon.py` reconstructs E011 using the E013 regime's **recorded simulator
settings**. It runs the unperturbed sham branch until the preceding time step,
then deep-copies the same physical and tracking state for each condition.
This is a *prospective reconstruction*, not an exported historical checkpoint.

For E013 regime 05, seed 3, the retrospective audit identified the sham
episode at steps **530–535**. Run:

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/short_horizon.py \
  --e011 ~/abio-publish/track2/rco002/rco002_experiment011/sim.py \
  --settings ~/abio/track2/rco002/remote_batches/batch_d23012657c7d41e6ba18/regime_05/e011/settings.json \
  --seed 3 \
  --event-start 530 \
  --horizon 6 \
  --expected-sham-steps 6 \
  --out ~/abio/track2/rco002/experiment014/results/e013_regime05_seed3_counterfactual.json
```

**Gate 1:** `historical_sham_reproduced` must be `true`, otherwise stop
interpretation and investigate why the reconstructed sham differs from the
historical evidence.

**Gate 2:** report per-mode `intervention_exposure`. A blocked condition
with zero actual suppressed reactions is a no-op, not a causal intervention.

**Gate 3:** report matched physical divergence, functional continuity and
candidate intervals as *descriptive* outcomes. A 6-step correlation is not six
independent replications, and even a targeted short-horizon loss would not
prove self-maintenance without longer organization-specific tracking.

These scripts do **not** modify the production E011/E012 runner, do not
submit to the Site API, and do not auto-publish reports to GitHub.

### Tests

```bash
cd ~/abio-publish/track2/rco002/rco002_experiment014
python3 -m unittest -v test_audit.py test_short_horizon.py
```


## Phase 3: mechanism-specific event tracing

Following the positive-exposure step-513 intervention, inspect *which events
and physical constituents* diverge, not just a conjunctive success flag.
This tool replays matched states from step 512, records per-step suppressed
catalytic birth opportunities, actual catalytic births, functional profiles,
product uptake and first physical divergence, and writes a versioned JSON
record. It does **not** infer a formal RAF or verified self-maintenance.

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/mechanism_trace.py \
  --e011 ~/abio-publish/track2/rco002/rco002_experiment011/sim.py \
  --settings ~/abio/track2/rco002/remote_batches/batch_d23012657c7d41e6ba18/regime_05/e011/settings.json \
  --seed 3 --start 513 --end 535 --expected-sham-steps 6 \
  --out ~/abio/track2/rco002/experiment014/results/e013_mechanism_trace_513.json
```

The stdout summary reports the time of first physical divergence and actual
intervention exposure, while the detailed JSON preserves per-step ancestry.
If the sham doesn't reproduce, stop causal interpretation. The original
control_block may be unexposed; do not mislabel it an active control.

To run the complete E014 test set:

```bash
cd ~/abio-publish/track2/rco002/rco002_experiment014
python3 -m unittest -v test_audit.py test_short_horizon.py test_mechanism_trace.py
```

**Important distinction:** a strict E011 candidate is a *heuristically
tracked functional motif with recorded turnover*; the E011 reaction model has
not yet been mapped to a formal catalytic reaction system with explicitly
validated RAF food-generation and catalyst-closure conditions.


## Phase 4: exposure-matched negative control preflight

The previous E014 result has a crucial limitation: the `control_block`
condition suppressed **zero** events while the target intervention suppressed
**four**. Thus it is an inactive control, not a causally informative control.

The preflight script scans the saved phase-3 mechanism trace to find **off-target
sham catalytic births at the same steps** as the target suppression events.
This is design exploration and does not run new perturbations.

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/active_control_preflight.py \
  --trace ~/abio/track2/rco002/experiment014/results/e013_mechanism_trace_513.json \
  --out ~/abio/track2/rco002/experiment014/results/e013_active_control_preflight.json
```

A successful preflight means only that comparable *candidate opportunities*
are present in the saved trace. It **does not** establish an active control:
we must implement selective inhibition of those off-target events, verify
actual suppression and biological/computational specificity, and repeat with
prospectively selected targets in fresh seeds. No change has been made to the
existing E011 dynamics or production API.

```bash
cd ~/abio-publish/track2/rco002/rco002_experiment014
python3 -m unittest -v test_audit.py test_short_horizon.py test_mechanism_trace.py test_active_control_preflight.py
```


## Phase 5: execute the actual off-target inhibition

This phase uses `e014_sim.py`, an **isolated copy of E011** with one guarded
scheduled off-target inhibition hook, plus `active_control_run.py`.
It reconstructs the same sham state before step 513 and executes matched
sham, target-block and scheduled off-target control branches through step 535.

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/active_control_run.py \
  --sim ~/abio-publish/track2/rco002/rco002_experiment014/e014_sim.py \
  --settings ~/abio/track2/rco002/remote_batches/batch_d23012657c7d41e6ba18/regime_05/e011/settings.json \
  --preflight ~/abio/track2/rco002/experiment014/results/e013_active_control_preflight.json \
  --seed 3 --start 513 --end 535 --expected-sham-steps 6 \
  --out ~/abio/track2/rco002/experiment014/results/e013_active_control_run.json
```

**Interpretation gates:** the sham must reproduce 6 candidate steps; the new
off-target branch must report `realized_scheduled_offtarget_suppressions` and
`all_offtarget_events_realized`. The original four schedule entries might
not all remain available after earlier interventions alter the state. If they
do not all occur, this is *not* exposure-matched in event count. Matching
event count and timing would still not match spatial, chemical, or network
centrality. The schedule was retrospectively chosen, so any result remains
exploratory, not prospective independent confirmation.

The production API and E011 simulator are unchanged.

```bash
cd ~/abio-publish/track2/rco002/rco002_experiment014
python3 -m unittest -v test_audit.py test_short_horizon.py test_mechanism_trace.py test_active_control_preflight.py test_active_control_run.py
```


## Phase 6: lineage survival and recovery audit

The extended step 513–600 run shows that the *selected functional lineage* has
size zero at the final step in all modes. This does not imply system extinction.

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/lineage_survival.py \
  --input ~/abio/track2/rco002/experiment014/results/e013_active_control_extended.json \
  --out ~/abio/track2/rco002/experiment014/results/e013_lineage_survival.json
```

The audit reports first detected absence, any later reappearance, contiguous
motif-preservation and candidate intervals, and time present. The lineage
identifier is heuristic; a tracked lineage disappearing does not show all
components died or demonstrate failure of all related organizations.

Unit tests:

```bash
cd ~/abio-publish/track2/rco002/rco002_experiment014
python3 -m unittest -v test_lineage_survival.py
```


## Phase 7: particle-level fate audit across the step-543 loss of tracking

The prior survival audit found the **selected functional lineage ID** first
absent at step 543 under sham, target inhibition, and active off-target
inhibition. Phase 7 reconstructs the matched branches and records physical
particle survival, bonds, nearby candidate successor groups, and functional
profiles on steps 538–548. It distinguishes lineage assignment loss from
true disappearance of material. The tool does **not** infer self-maintenance.

```bash
cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/fate_audit.py \
  --sim ~/abio-publish/track2/rco002/rco002_experiment014/e014_sim.py \
  --settings ~/abio/track2/rco002/remote_batches/batch_d23012657c7d41e6ba18/regime_05/e011/settings.json \
  --preflight ~/abio/track2/rco002/experiment014/results/e013_active_control_preflight.json \
  --seed 3 --start 513 --inspect-start 538 --inspect-end 548 \
  --out ~/abio/track2/rco002/experiment014/results/e013_fate_audit_543.json
```

Run `python3 -m unittest -v test_fate_audit.py` before executing.
An original tracked ID can be lost by splitting, merging, or a replacement
assignment while substantial constituent material survives. Any overlapping
functional group is a successor **candidate**, not proven continuity.


## Phase 8: direct causal-mechanism audit of step-543 bond loss

This phase instruments **only the already existing E014 simulator variant** to
record the **original random draw** used to test each existing bond against
`bond_break` at step 543. It does **not** change the transition rule or RNG
call order. The original E011 simulator is untouched. The matched reconstruction
reports whether each bond of the tracked functional group at step 542 was
actually removed by a successful stochastic break trial.

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment014
python3 -m unittest -v test_bond_break_cause.py test_fate_audit.py

cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/bond_break_cause.py \
  --sim ~/abio-publish/track2/rco002/rco002_experiment014/e014_sim.py \
  --settings ~/abio/track2/rco002/remote_batches/batch_d23012657c7d41e6ba18/regime_05/e011/settings.json \
  --preflight ~/abio/track2/rco002/experiment014/results/e013_active_control_preflight.json \
  --seed 3 --start 513 \
  --out ~/abio/track2/rco002/experiment014/results/e013_bond_break_cause_543.json
```

The log distinguishes direct stochastic bond breakage from unexplained
end-of-step bond loss. Even a direct break is not proof that the organization
could not repair itself, or that catalytic inhibition determined this event.
The same keyed random streams and shared prehistory make the branches
**correlated**, not independent replicates. No RAF or life claim.


## Phase 9: global bond-turnover counterfactual at step 543

Phase 8 confirmed that two bonds connecting the tracked three-particle
organization were removed by **ordinary stochastic break trials** at step 543:
their site-specific draws were 0.0019299045 and 0.0034529178 against the
original threshold 0.018. The same draws occurred in all matched treatment
branches, so those observations are **correlated, not independent**.

Phase 9 reconstructs the **sham state at the end of step 542** and forks
counterfactual conditions with global bond-break thresholds
`0.0, 0.002, 0.004, 0.018`, each in two variants:

- **Pulse:** set the alternate threshold for step 543 only, then restore the
  baseline threshold for steps 544–600.
- **Sustained:** set the alternate threshold for steps 543–600.

All variants share a physically identical checkpoint and differ only in the
bond-break threshold at or after step 543. The intervention affects **every
bond in the substrate**, not just this candidate's edges. It is an externally
imposed mechanism probe, not spontaneous bond repair.

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment014
python3 -m unittest -v test_bond_turnover_counterfactual.py

cd ~/abio
python3 ~/abio-publish/track2/rco002/rco002_experiment014/bond_turnover_counterfactual.py \
  --sim ~/abio-publish/track2/rco002/rco002_experiment014/e014_sim.py \
  --settings ~/abio/track2/rco002/remote_batches/batch_d23012657c7d41e6ba18/regime_05/e011/settings.json \
  --seed 3 --checkpoint 542 --end 600 \
  --rates 0.0 0.002 0.004 0.018 \
  --out ~/abio/track2/rco002/experiment014/results/e013_bond_turnover_counterfactual.json
```

The summary reports first absence of the original functional lineage and first
disconnection of the three checkpoint constituents, along with duration and
final fate. The unmodified baseline (`0.018`) must reproduce loss at step
543; if it does not, stop interpretation. A lower break threshold that extends
lifetime demonstrates a dependence on external turnover conditions, **not**
endogenous organizational self-maintenance. Future prospective studies must
test independent seeds and whether organization itself alters bond durability.
