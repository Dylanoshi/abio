# Research Note 004

# The Conditions of Self-Maintenance

**Catalytic feedback, structural persistence, and the search for regenerative organization in a spatial computational substrate.**

**Program**

ABIO — Computational Abiogenesis Research

**Date**

November 13, 2026

**Status**

Completed experimental investigation; raw-data numerical audit completed; final regression-test and website publication checks pending

| Held-out interventions | Material continuity | Field exposure | Individual outcomes |
|---|---|---|---|
| **12 seeds** | **204.58 vs 199.33** | **198.67 vs 69.67** | **4 / 3 / 5** |
| Steps 301–600; paired arms | Mean steps: sham vs self-source removed | Mean bridge bond trials exposed to field | Sham favored / removal favored / tied |

## Abstract

We investigate whether a computational organization can contribute causally to its own persistence by generating local conditions that stabilize its constituent bonds. In a spatial particle-and-reaction substrate, successful catalytic events deposit a transient protective field that lowers subsequent bond-break probability. The mechanism alters realized bond outcomes: matched-random-draw comparisons identify bonds that remain intact with local protection but break when deposition by the materially traced organization is suppressed. Such effects were pronounced in two previously observed trajectories. A separate 12-seed evaluation, however, found no consistent advantage in the duration of organizational material continuity: the mean was 204.58 of 300 postcheckpoint steps under sham feedback and 199.33 under self-source suppression, with four seeds favoring sham, three favoring suppression, and five tied. A mechanistic audit of those same seeds found substantial differences in field exposure but little aggregate difference in catalytic births. These results distinguish a demonstrated local structural-feedback mechanism from the stronger and presently unsupported claim of regenerative organizational self-maintenance. They do not establish RAF/CAF closure, autopoiesis, reproduction, adaptation, or spontaneous abiogenesis.

## § 1 — Research question

Earlier ABIO investigations of BFF replicators examined hereditary copying, population establishment, and recovery after perturbation. Research Note 003 addressed whether an exact computational replicator family could persist and reoccupy a finite population under specified conditions. That is a distinct problem from asking whether an organization can continuously reconstruct the material or functional conditions of its own existence.

We therefore investigate a different form of persistence: not whether one sequence reproduces successfully, but whether a spatially embodied organization can modify its environment in ways that affect its continued coherence. Persistent bonds are not, by themselves, evidence of self-maintenance; nor is material turnover evidence of regeneration without a demonstrated productive relationship between the organization and its replacement constituents.

**Can an organization arising from local computational rules generate protective conditions that causally prolong its own material and functional continuity—and is this effect consistent across independently seeded trajectories?** We distinguish (i) catalytic generation of a structural influence, (ii) effects on realized bond-break events, and (iii) the subsequent continuity of the producing organization.

## § 2 — System and operational definitions

The E015 substrate is a 24 × 24 lattice of particles, nutrient sites, and bonds governed by stochastic local rules. Four particle types participate in type-dependent catalytic reactions. Productive bonded catalyst pairs can create a new particle, and a successful catalytic event deposits a finite-lived field at the catalyst and product sites. At the next bond-update stage, the field reduces the local chance of bond breakage according to:

\[
p_{\mathrm{break,eff}}=\frac{p_{\mathrm{break}}}{1+\alpha F_{\mathrm{local}}}.
\]

The baseline break probability is 0.018, the protection strength is 3.0, and field retention between steps is 0.8; the remaining substrate parameters are recorded in the experiment configuration. This stabilizing rule is deliberately supplied as a property of the substrate. The simulations do **not** discover or evolve the protection law itself.

A *functional component* is a bonded connected component with a profile of productive catalyst-pair motifs. A *material bridge* is an operational tracking heuristic that follows the component with the greatest overlap in particle identities from one step to the next; tracking ends when no material successor is found. An organization's *present-steps* are the postcheckpoint steps for which that material bridge remains identified, regardless of whether its original constituents survive. *Functional similarity* refers to similarity between the current productive-motif profile and its profile at selection. These are measurements of candidate organizations, not a validated definition of an organism.

All paired interventions begin from a shared physical state at step 300 and continue through step 600. In the *sham* condition, catalytic events deposit normally. In *dynamic self-source suppression*, catalytic births by the currently traced component proceed, but their protective deposits are withheld; births outside the component remain eligible. The *timed off-target control* instead suppresses nonfocal deposits according to counts scheduled from the corresponding sham trajectory. It approximates deposit timing and frequency but does not match field location, magnitude, actual bond exposure, or realized suppression count exactly.

## § 3 — Experiment 015: substrate-level structural feedback

The first comparisons examined disabled protection, locally coupled protection, and spatially shuffled protection. Under the shuffled condition, field magnitude is preserved while its spatial association with production is disturbed. The broad comparison showed that the field changes local bond physics, but the aggregate structural and functional metrics did not show a consistent advantage for spatial coupling. This distinction is essential: implementing a possible protective mechanism does not guarantee that it improves organization-level outcomes.

A matched checkpoint intervention subsequently compared continuation with local feedback against disabled and shuffled feedback for groups already present at step 300. Some heuristic functional-identity measures favored the locally coupled condition, but the evidence was sensitive to how groups were identified and to the small number of independent seeds. Those observations motivated a more restrictive question: does protection produced by the tracked organization itself matter, as opposed to protection produced by the rest of the substrate?

## § 4 — Experiment 015: source attribution and material continuity

An initial intervention that suppressed deposits from one fixed functional identifier showed no reliable persistence effect. This result had a methodological limitation: the same material complex could continue under a new functional identifier, so suppressing only the original identifier might fail to remove protection produced by its successors.

A subsequent ancestry audit followed material overlap through those identifier changes. It recorded 177 catalytic births attributable to traced material successors across the historical 12-seed set and found ten fixed-state, same-random-draw bond trials classified as avoidable breaks under self-attributed field. These counts established mechanistic opportunities for protection, not proof that any particular organization actively maintained or regenerated itself.

Dynamic source suppression then followed the material successor instead of a frozen identifier. In two previously observed responsive seeds, material-bridge presence was 300 versus 109 steps (seed 2) and 300 versus 197 (seed 3), comparing sham with source suppression. First-divergence analysis identified common bond trials with identical random draws but different protection-dependent break thresholds: the bond survived in sham and broke with suppression. Because these two seeds were identified after earlier experiments, they are **exploratory cases**, not a representative estimate of a general survival advantage.

## § 5 — Experiment 015: independent-seed intervention

Twelve additional seeds, 12 through 23, were evaluated at the unchanged step-300 checkpoint and followed to step 600. Each seed contributed one matched comparison. The outcome was explicitly heterogeneous.

| Condition | Mean material-bridge present-steps | Mean checkpoint-motif similarity across all steps | Mean motif-positive steps |
|---|---:|---:|---:|
| Sham feedback | 204.58 | 0.3737 | 195.42 |
| Dynamic self-source suppression | 199.33 | 0.3619 | 188.75 |
| Timed off-target suppression | 207.67 | 0.3834 | 204.33 |

The mean paired difference between sham and self-source suppression was **+5.25 steps**, but four seeds favored retaining self-source protection, three favored its removal, and five produced equal present-step counts. The associated paired comparison does not establish a reliable positive group effect. The timed off-target condition illustrates an important qualification: although its mean blocked-deposit count was close to that of the focal suppression condition, realized suppression counts matched in only five of twelve seeds, and spatial exposure was not dose-matched.

**Figure 1 — Paired effect of self-produced protection on material continuity (Experiment 015, seeds 12–23)**

![Paired differences in the observed duration of materially traced components for each held-out seed.](figures/note004_heldout_seed_effects.svg)

*Each bar is one seeded paired comparison over steps 301–600. Values are sham minus self-source-suppressed material-bridge present-steps: positive values favor protection, negative values favor its removal, and zero indicates no difference in this outcome. The twelve differences are 0, +23, +18, −54, −97, 0, 0, +131, −37, +79, 0, and 0. This is the independently evaluated cohort; it is not an additional set of twelve seeds in the later mechanistic audit.*

## § 6 — Experiment 015: mechanistic turnover audit

The final audit replayed the **same twelve seeds** under sham and dynamic self-source suppression, adding observational measurements of material entries and departures, internal particle-ID bond gains and losses, catalytic production, field exposure, and nearby nutrient sites. Every instrumented sham continuation reproduced the final physical state of a corresponding uninstrumented continuation. The complete uploaded JSON was independently reconciled against seed-level timelines and reported summary statistics; the most recent standalone regression-test output remains to be confirmed.

| Mean per seed, steps 301–600 | Sham | Self-source removed |
|---|---:|---:|
| Material-bridge presence | 204.58 | 199.33 |
| Material entries | 34.33 | 31.33 |
| Material departures | 39.50 | 37.67 |
| Internal bond gains | 34.50 | 31.75 |
| Internal bond losses | 39.00 | 37.33 |
| Catalytic births assigned to bridge | 11.50 | 11.58 |
| Mean field at bridge sites, while present | 0.11506 | 0.01220 |
| Field-exposed bridge bond-break trials | 198.67 | 69.67 |
| Same-draw baseline-avoided break trials | 1.42 | 0.33 |
| Mean checkpoint-motif similarity, while present | 0.5483 | 0.6034 |

Suppression greatly lowered field exposure at bridge bonds while leaving the mean number of attributed catalytic births nearly unchanged. That is consistent with the intervention acting on the prescribed field-deposition pathway rather than directly inhibiting catalysis. Yet the larger protection exposure in sham did not translate into a consistent advantage in material-bridge duration.

Absolute material-entry and bond-turnover counts were somewhat higher in sham. Those totals cannot be interpreted directly as rates of regeneration: longer observed component lifetimes provide more opportunities for change, while bond gains and losses can reflect merging, splitting, and changes in which component is tracked. Nor does the higher similarity *conditional on the bridge remaining present* under suppression demonstrate improved function, since that condition selects different surviving states and observation windows.

Individual trajectories convey the heterogeneity. Sham outlasted suppression in seed 19 (217 versus 86 steps) and seed 21 (131 versus 52). Conversely, suppression outlasted sham in seed 16 (266 versus 169) and seed 15 (300 versus 246). Seed 12 retained its bridge for all 300 postcheckpoint steps under either condition. These contrasting cases justify studying how topology, turnover, and spatial resource context interact, but the present audit does not identify a validated predictive cause of their different outcomes.

## § 7 — Interpretation and limitations

These investigations support a distinction between three levels of evidence. First, the substrate includes a well-defined production-linked field capable of reducing bond-break probability. Second, matched-draw interventions demonstrate that differences in that field can alter *actual* bond-break events on a tracked material component. Third, the consequences for material and functional organizational continuity are heterogeneous and remain inconclusive at the group level. Observing the first two levels does not establish the third.

- The protective field is a deliberately implemented local rule, not an emergent repair system.
- Candidate identities rely on a single-successor material-overlap heuristic. Splits, mergers, or discontinuous reorganization can invalidate apparent individual continuity.
- Particle entry and departure do not demonstrate regenerative incorporation, and nutrient proximity is not nutrient uptake or metabolic closure.
- The timed off-target control matches intended event counts and timing only imperfectly, not field placement or actual protection dose.
- The final audit reuses the held-out cohort for explanation. It is not new independent replication, and post-intervention features cannot be treated as prespecified predictors.
- Separate bond trials, time steps, and particles within one seed are not independent experimental replicates.
- No explicit test establishes a reflexively autocatalytic and food-generated (RAF) set, a constructively autocatalytic and food-generated (CAF) network, a maintained compartment, or an autonomous self-repair cycle.
- Reproduction, heredity, open-ended evolution, and spontaneous abiogenesis were not demonstrated.

A possible explanation for the opposing outcomes is that preserving some connections stabilizes productive catalytic topology, while preserving others changes later rearrangements or competitive interactions. This remains a hypothesis; no preintervention structural criterion was validated in an independent prospective test.

## § 8 — Research question assessment

| Question | Assessment |
|---|---|
| Can catalytic production generate a local protective influence? | Demonstrated by the E015 substrate mechanism and field audit |
| Does this influence alter actual bond-break decisions? | Demonstrated in matched-draw event comparisons |
| Can the producing material bridge be affected by suppressing its own protective deposits? | Observed in individual intervened trajectories |
| Does self-source protection reliably prolong material continuity across fresh seeds? | Not established: 4 positive, 3 negative, 5 tied |
| Does protection preserve functional identity through material turnover? | Sometimes observed descriptively; causal regenerative maintenance not established |
| Does the substrate reconstruct the conditions of its own operation? | Not demonstrated |
| Is RAF/CAF closure or autopoiesis demonstrated? | Not tested to the required formal criteria |
| Is computational abiogenesis demonstrated? | No |

## § 9 — Conclusion and next investigation

E015 demonstrates a local, production-linked mechanism through which catalytic activity can change the physical fate of bonds. Its actual organizational effects are mixed: suppression of an organization's own field production can shorten, extend, or leave unchanged the observed duration of its material successor. The result is therefore not a discovery of autonomous self-maintenance. It is a constrained empirical reason to distinguish **stabilization of structure** from **regeneration of the organization that makes the stabilization possible**.

The next ABIO investigation should test whether material renewal, resource processing, and functional reconstruction can become causally coupled within a persistent organization, ideally with explicit spatial compartmentalization and interventions aimed at the proposed regenerative cycle. That is a new hypothesis and experimental program, rather than a positive conclusion of this note.

## Reproducibility and provenance

**Figure data provenance.** Figure 1 uses twelve paired present-step differences extracted from the held-out seed summary and checked against the original uploaded machine-readable audit. The illustration does not depict an unobserved trajectory or imply continuous outcomes between samples.

**Repository layout.** E015 implementation, audit and test files are maintained under `track2/rco002/rco002_experiment015/` in the [ABIO repository](https://github.com/Dylanoshi/abio/tree/e014-candidate-audit-v1). This manuscript is `research_notes/004_the_conditions_of_self_maintenance_DRAFT.md` and its figure is under `research_notes/figures/`. A compact, verified evidence record is available as [004_verified_evidence_summary.json](004_verified_evidence_summary.json).

**Raw-data verification.** The investigator-provided `note004_mechanistic_audit.json` was validated as twelve seeds × two arms × 300 postcheckpoint observations, including per-seed sums, paired effects and aggregate statistics. Raw file size: **7,384,244 bytes**; SHA-256: `95afd90dbe3baec7267b5969f6ba20df80898fc866eb1f5adb20ec965f05d147`. The compact summary is **not** a substitute for a permanent public deposit of the full original time-series JSON.

**Reproduction requirements.** An archival release should preserve the simulator and audit code revisions, Python environment, parameters, checkpoint and selection rules, per-seed run logs, full source JSON, output checksum, sham parity results, and results of the latest regression suite. The mechanistic audit and data-accounting verification are complete; independently documented latest regression output and final public data deposition remain outstanding.

## References

1. Hordijk, W., & Steel, M. (2019). *Autocatalytic networks in biology: structural theory and algorithms.* [Philosophical Transactions of the Royal Society B](https://pmc.ncbi.nlm.nih.gov/articles/PMC6408349/).
2. Hordijk, W. (2023). *A Concise and Formal Definition of RAF Sets and the RAF Algorithm.* [arXiv:2303.01809](https://arxiv.org/abs/2303.01809).
3. Agüera y Arcas, B., et al. (2024). *Computational Life: How Well-formed, Self-replicating Programs Emerge from Simple Interaction.* [arXiv:2406.19108](https://arxiv.org/abs/2406.19108).
4. Knierim, C., et al. (2026). *BFF: Simple explanations for complex phenomena.* [arXiv:2607.01483](https://arxiv.org/abs/2607.01483).
5. ABIO Research Note 003. *Replication, Population Takeover, and Recovery in a Mutation-Free Computational Substrate.* See the existing ABIO research-notes archive.

---

*ABIO · [abio.life](https://abio.life) · Open Science · 2026*
