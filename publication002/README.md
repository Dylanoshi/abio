# ABIO — Research Note 002

**Functional Heredity, Multigenerational Replication, and Mutational Robustness in an Evolved Computational Chemistry**  
October 28, 2026

Read the [full research note](002-functional-heredity.md).

## Principal results

- 43/50 selected configurations completed three reproductive transitions, representing 39 distinct ancestral sequences.
- 501,696 experimentally introduced single-byte substitution trials.
- 452,752 first-transition successes (90.2%).
- 407,098 three-transition successes (81.1%); 406,301 distinct successful mutant sequences.
- All 39 founders and all 64 positions permitted some viable mutations.
- Position-specific three-transition success ranged from 47.6% to 95.9%.

These results demonstrate controlled functional heredity and heritable sequence variation, **not** spontaneous mutation or Darwinian evolution.

## Included materials

- `experiment012/`: reproduction and causal-assay scripts, cases, and functional-heredity output.
- `experiment013a/`: mutation assay script, founders, summary, and aggregate position/founder robustness CSVs.

## Reproducibility caveat

The experiment scripts import a locally compiled `cubff` module from the instrumented BFF project, which is **not bundled here**. The full 145 MB mutation-level CSV and 408 MB interaction binary are also excluded. Reproducing the assays requires the corresponding BFF implementation and matching simulator build; the included scripts and summary tables alone do not provide a fully standalone replication package.

The replacement alphabet was drawn from byte values observed in the successful founders, not verified against the full language instruction set. Reported mutation success is sequence-level and conditional on controlled encounters.
