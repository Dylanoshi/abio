# Research Note 004 — The Conditions of Self-Maintenance

**Subtitle:** Catalytic Feedback, Structural Persistence, and the Search for Regenerative Organization

**Status:** EDITORIAL DRAFT — not published. Mechanistic audit pending.
**Project:** ABIO — Computational Abiogenesis
**Scope:** E015 phases 1–6 and final mechanistic audit.
**Position:** Experimental research note, not evidence that artificial life has emerged.

## Abstract

When can a persistent organization become causally responsible for its own
continuation? We investigate an artificial reaction substrate with local
catalytic production and a transient protection field that changes bond-break
probabilities. Our simulations establish a mechanistic link between catalytic
activity and structural stabilization. Source-selective interventions identify
individual trajectories in which suppressing field deposition by a materially
traced organization shortens its persistence. But independent-seed evaluation
reveals heterogeneous effects, including cases where the same intervention
increases continuity. We distinguish local bond protection from the stronger
requirements of ongoing functional regeneration and organizational
self-maintenance.

**This abstract is provisional; update it after the final audit.**

## 1. Persistence is not self-maintenance

We distinguish passive survival of a bond or structure from maintenance of a
causally persistent organization despite constituent turnover. Functional
continuity requires more than the persistence of an identity label and cannot
be inferred from protection alone. Note 004 asks whether, and under what
conditions, local catalytic activity helps preserve the producing
organization's material and functional continuity.

## 2. Model and intervention logic

E015 begins from a stochastic spatial particle-and-bond substrate. Local
productive catalytic bonds generate products and temporary field strength.
At a later step, field at bond endpoints reduces the break probability via:

\[
p_{\mathrm{break,eff}}=\frac{p_{\mathrm{break}}}{1+\alpha F_{\mathrm{local}}}
\]

where \(p_{\mathrm{break}}\) is the baseline bond-break chance,
\(\alpha\) is the model's protection strength and \(F\) is local
field. This is a deliberately specified substrate mechanism, **not**
an emergently discovered biological repair program.

Simulations create organizations from the substrate's local rules rather
than instantiating predefined organisms. Candidate identities are inferred
by bonded connected components and material overlap; they are heuristic.

## 3. Progression of experiments

### Field effects and broad continuity

The initial E015 comparison of disabled, spatially coupled and shuffled
field effects (12 seeds) demonstrated physical consequences but **did not**
show a consistent benefit of local coupling to the broad candidate-step
metric (local mean 7,901.83; disabled mean 7,922.00; shuffled mean 7,975.50).

### Matched post-formation intervention

At a shared step-300 checkpoint, continuation with local feedback produced
greater mean observation-steps of existing functional identities
(6.9935 original tracked IDs per step) than disabling field influence
(6.2163) or shuffling the field (6.6447). Between-seed uncertainty and
heuristic identity assignment prevented a definitive organization-level
interpretation.

### Source and ancestry auditing

A frozen original functional-ID source suppression failed to show consistent
causal dependence. Material-bridge tracing subsequently identified
contributions overlooked after lineage-ID changes: 177 catalytic births
were attributed to traced material successors across 12 seeds, and
10 bond-break trials were classified as prevented by self-attributed field
under fixed-state, same-random-draw comparisons. These are **local causal
opportunities**, not full trajectory-level proof.

### Dynamic self-source ablation

A dynamic intervention that followed the materially overlapping successor
revealed substantial losses of measured continuity in two already observed
trajectories: seed 2 (300 versus 109 postcheckpoint steps) and seed 3
(300 versus 197). Matched-draw bond-break thresholds identified a
first different bond outcome involving the material bridge in each.
These cases were identified retrospectively and cannot serve as independent
confirmation.

### Independent-seed assessment

Fresh seeds 12–23 yielded mean material-bridge presence 204.58 steps
with sham protection, 199.33 with material-bridge-source protection
deposition suppressed, and 207.67 with a timed off-target control.
The sham-minus-suppression differences were:

\[
[0, 23, 18, -54, -97, 0, 0, 131, -37, 79, 0, 0].
\]

Only four seeds favored sham, three favored removal, and five tied.
Mean benefit +5.25 steps, with wide uncertainty. The effect does
**not** establish a reliable population-level organization-survival
benefit. The control was closer in count and timing but not matched
for spatial field mass or bond exposure.

## 4. Final mechanistic audit: turnover, function, and resource context

**PENDING:** Insert the complete, unchanged E015 Note004 audit output
from `note004_mechanistic_audit.py`. Report the same 12 seeded pairs,
including positive, negative and null persistence effects. Examine
material entries/departures, bond turnover, functional motifs, catalytic
births, field exposure at focal bonds, and local resource availability.

Do not interpret post-intervention correlations as preintervention
determinants. Distinguish mechanisms of protection from proof of
regenerative causality.

## 5. Interpretation and limits

The demonstrated local mechanism is catalytic-field modification of
bond-break hazards. This can affect bonds on the actual traced
material component, yet its long-term organizational consequences are
strongly heterogeneous. Stabilization may preserve function in some
trajectories and alter later rearrangements in others. Explanations
involving productive turnover, boundary formation or resource flows
remain hypotheses pending direct controlled testing.

No formally demonstrated RAF/CAF closure, spatial compartmental
self-maintenance, heritable reproduction, or spontaneous artificial
organism is claimed.

## 6. A bounded conclusion

Note 004 focuses the distinction between **structural persistence** and
**causal organizational maintenance**. Evidence of internally generated
structural protection does not suffice to show a self-sustaining
organization. The next ABIO research stage should test explicit
regeneration and material/functional closure, rather than treating
lifespan alone as the success criterion.

## Publication requirements

- [ ] Final mechanistic audit runs and regression tests pass.
- [ ] Insert final numeric audit findings and figures with seed-level provenance.
- [ ] Verify model equations, control logic and terminology against code.
- [ ] Cross-check scientific novelty against RAF/CAF, autopoiesis and artificial-life literature.
- [ ] Preserve the mixed/negative results; do not select only responders.
- [ ] Confirm the ABIO website content publishing interface and authorized destination.
- [ ] Publish final checked text, clearly marked Research Note 004.
