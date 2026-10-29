# Research Note 002

## Functional Heredity, Multigenerational Replication, and Mutational Robustness in an Evolved Computational Chemistry

**ABIO — Computational Abiogenesis Research Program**  
**October 28, 2026**  
**Status:** Completed experimental investigation

### Abstract

An isolated copying event does not establish functional heredity or an evolvable lineage. We investigated multigenerational reproduction and the inheritance of experimentally introduced sequence changes in an instrumented implementation of the BFF computational chemistry (`bff_noheads`). Of 50 previously selected replication-positive configurations, 43 completed three controlled reproductive transitions, representing 39 distinct ancestral sequences. Every successful lineage alternated between a 64-byte sequence and its byte reversal. In a subsequent substitution survey of the 39 validated founders, 452,752 of 501,696 mutation trials (90.2%) completed an initial reproductive transition, and 407,098 (81.1%) completed three transitions. These successful trials represented 406,301 unique mutant sequences. All 39 founders and all 64 byte positions permitted some viable substitutions, but position-specific success ranged from 47.6% to 95.9%. The results support controlled functional heredity, transmission of introduced sequence variation, and nonuniform mutational robustness. They do not establish spontaneous mutation, autonomous lineage persistence, natural selection, or open-ended evolution.

### 1. Research question

Can reproductive configurations recovered from an evolved computational chemistry generate reproductively competent descendants, transmit altered sequence information, and retain reproductive function despite mutations? The distinction is between one-off copying and the inheritance of the capacity to reproduce. This note addresses controlled multigenerational reproduction, sequence transmission, and the tolerance of experimentally imposed variation; autonomous population evolution is left for Research Note 003.

### 2. System and assay

The experiments used the instrumented BFF `bff_noheads` language. Each assay combined a 64-byte donor and a blank 64-byte recipient, executed through `RunSingleParsedProgramState` with an 8,192-step limit. A successful reproductive transition required the donor to remain unchanged and the recipient to become the nonblank exact byte reversal of the donor. For multigenerational tests, the *actual simulator-produced offspring* served as donor in the next interaction with a new blank recipient. The initial candidates came from an earlier computational run of 1,048,576 interactions; the selected candidates are not a random sample of arbitrary programs.

### 3. Experiment 012: functional heredity

Fifty replication-positive configurations were assayed for three consecutive reproductive transitions. Forty-three completed all three; those successful cases contained 39 distinct starting sequences. Every completed lineage followed the observed pattern:

\[
A \rightarrow R(A) \rightarrow A \rightarrow R(A)
\]

where `R` reverses the 64-byte sequence. The fact that reversing twice recovers the original sequence is a mathematical identity, not itself an experimental finding. The evidence of functional heredity is that the simulator actually executed each transition and the resulting offspring could reproduce again. This establishes three-transition reproductive competence under the tested conditions, not autonomous persistence in an unconstrained population. The 43/50 fraction is conditional on prior selection of replication-positive configurations.

### 4. Experiment 013A: mutational inheritance

The 39 distinct successful ancestors were recovered from Experiment 012 and independently verified as three-transition positive controls (39/39). For each 64-byte founder, each position was substituted with each of 201 alternative byte values observed across the founders. Thus each founder had 64 × 201 = 12,864 trials, for a total of 501,696 trials. The mutations were deliberately introduced by the experimenter; they were not spontaneous mutations observed during reproduction.

| Measurement | Result |
|---|---:|
| Validated founders | 39 |
| Single-byte substitution trials | 501,696 |
| Unique mutant sequences tested | 500,888 |
| First-transition successes | 452,752 (90.2%) |
| Three-transition successes | 407,098 (81.1%) |
| Unique successful mutant sequences | 406,301 |
| Founders with at least one successful mutant | 39/39 |
| Byte positions with at least one successful mutant | 64/64 |

Successful mutant trials retained the exact altered sequence through the simulator's reversal-based reproductive transformations while offspring remained capable of further reproduction. Multiple mutation events sometimes produced the same genotype, so trial counts and unique-sequence counts are reported separately.

### 5. Nonuniform mutational tolerance

Founder-level three-transition success ranged from **66.7% to 85.2%**. Position-level success varied more strongly. Positions **33–36** each permitted approximately **95.9%** of tested substitutions; position **24** permitted **95.7%**. In contrast, position **48** permitted **47.6%**, position **15** **47.8%**, position **7** **54.9%**, and position **45** **55.2%**. Every position allowed at least some successful substitutions, but the observed tolerance was strongly position-dependent.

This pattern is consistent with unequal functional constraints across the sequence. Some bytes may influence copying instructions, others may be copied without affecting execution, and others may have context-dependent effects. The present assays do not establish which explanation applies to any specific position. In particular, a byte substitution is not necessarily a change to an executed instruction, and sequence-level variation should not be equated with novel reproductive functionality.

### 6. Interpretation and limitations

The strongest joint finding is that descendants can inherit the *ability* to reproduce, not merely a recognizable sequence, and that this ability persists across a substantial set of experimentally altered sequences. The high tolerance to single-byte substitutions indicates a broad local neighborhood of reproductive viability under controlled conditions, while the pronounced differences among positions suggest a structured mutational landscape.

Several limits constrain interpretation:

- **Selected founders:** All 39 founders came from previously replication-positive configurations; the results do not estimate how common such robustness is among arbitrary programs.
- **Controlled encounters:** Fresh blank recipients and fixed execution conditions were supplied externally; persistence in an autonomous population was not tested.
- **Introduced rather than spontaneous variation:** The mutation library was created by intervention, not by naturally occurring errors during reproduction.
- **Byte-level representation:** The assays do not distinguish changes to executed instructions from neutral or nonexecuted bytes.
- **Restricted replacement set:** The 201 replacement values were those observed in the validated founders, not a verified exhaustive list of valid instruction symbols.
- **Three-transition horizon:** These assays demonstrate short-term lineage continuation, not indefinite persistence.
- **No population selection:** Differences in viability do not by themselves demonstrate competition, differential fitness in a shared environment, or changes in variant frequencies through natural selection.
- **Deterministic dependence:** Large numbers of substitution trials do not constitute an equivalent number of independent stochastic replicates.

### 7. Research question assessment

| Question | Assessment |
|---|---|
| Can selected evolved configurations reproduce? | Demonstrated in controlled assays |
| Can their offspring reproduce? | Demonstrated |
| Can reproductive competence persist for three transitions? | Demonstrated |
| Is sequence information inherited through reproduction? | Demonstrated |
| Can introduced sequence variants be transmitted? | Demonstrated |
| Can reproduction tolerate many single-byte substitutions? | Demonstrated |
| Does tolerance depend on byte position? | Demonstrated |
| Do spontaneous mutations arise and propagate? | Not established |
| Do lineages persist autonomously? | Not established |
| Does population-level natural selection occur? | Not established |
| Is open-ended Darwinian evolution present? | Not established |

### 8. Conclusion and next investigation

Research Note 002 establishes controlled multigenerational functional heredity in selected BFF reproductive configurations and substantial, nonuniform tolerance of inherited sequence variation. This advances the investigation from isolated copying toward an experimentally characterized hereditary mechanism. It does not demonstrate autonomous Darwinian evolution. **Research Note 003** will investigate whether reproductive variants can persist in a shared environment, generate spontaneous heritable variation, and undergo population-level selection. Mechanistic mapping of sensitive sequence positions and compensatory mutations is a complementary next step.

### Reproducibility and provenance

Experiment 012 source and results: `experiment012/`. Experiment 013A source and summarized results: `experiment013a/`. The `experiment013a/position_robustness.csv` and `founder_robustness.csv` files contain aggregated results used in the figures. Full mutation-level data (`mutations_all.csv`, approximately 145 MB) and the earlier interaction archive (`interactions.bin`, approximately 408 MB) are not included in this Git repository; therefore, full independent auditing of every mutation-level result requires obtaining those separately or rerunning the supplied experiment against a compatible BFF simulator. The original instrumented simulator and its version/build details should be archived for exact reproducibility.
