# Research Note 004 — Airo site publishing instructions

Publish to the **existing ABIO website** under its existing Research Notes design; preserve previous notes, navigation, branding and related pages.

**Title:** The Conditions of Self-Maintenance

**Subtitle:** Catalytic Feedback, Structural Persistence, and the Search for Regenerative Organization

**Article source:** research_notes/004_the_conditions_of_self_maintenance_DRAFT.md

**Figure source:** research_notes/figures/note004_heldout_seed_effects.svg

**Metadata:** research_notes/004_publication_manifest.json

**Suggested URL:** /research/notes/004-the-conditions-of-self-maintenance (adapt to existing site URL patterns).

The central finding is that catalytic production can protect bonds, but it does not reliably increase the persistence of the producing organization in the held-out seed cohort. Preserve mixed and negative results and the limitations of material-bridge identity tracking. Do not claim RAF/CAF closure, artificial life, autonomous self-maintenance, reproduction or peer review.

Create an unpublished website preview first. Check desktop/mobile figures, equations, references, source links, and accessibility. Publish only after the latest Note004 regression test passes and the investigator's raw JSON result file has been archived and verified against the tables/figure. Confirm the live URL after release.

**Local verification:**

```bash
cd ~/abio-publish
git pull --ff-only origin e014-candidate-audit-v1
cd track2/rco002/rco002_experiment015
python3 -m unittest -v test_note004_mechanistic_audit.py
ls -lh ~/abio/track2/rco002/experiment015/results/note004_mechanistic_audit.json
```

The reported final audit and physical-parity checks completed across all 12 seeds. The unit-test rerun and original raw JSON are still needed to complete the publication provenance record.


## RN-003 editorial and presentation parity (2026-11-13)

The supplied previous website Research Note 003 is the **layout and voice reference**. In the current ABIO site reuse its existing article template: breadcrumb `Experiments / RN-004`, Research Note 004 eyebrow, title/subtitle, Program/Date/Status fields, four restrained metric cards, abstract, numbered `§` sections, experiment-specific headings, individually numbered figure and caption, research-question assessment table, conclusion and next investigation, reproducibility and provenance, references, and footer links. Avoid generic marketing copy or one-sentence-per-line writing. Keep the same sober, specific, conditionally stated research voice. Text must not give stronger conclusions than the actual measurements.

Use the article's full revised Markdown, not the earlier outline, as the source of truth. The publication manifest now includes site presentation metadata and card values. Use muted figure colours consistent with RN-003's established palette; preserve the already data-grounded SVG unless the site renderer requires an equivalent native figure. Add navigation links back to all experiments and to RN-003 using the site's real routes. Do not invent a live URL or claim RN-004 is published until that occurs.
