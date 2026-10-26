# ABIO Research Note 001

## Divergent Replication Trajectories in a Computational Chemistry

**ABIO — Computational Abiogenesis Research**  
**Version:** 0.1 (preliminary)  
**Date:** October 26, 2026  
**Status:** Exploratory, not peer reviewed

### Abstract

We report exploratory observations from two simulation trajectories using the `bff_noheads` computational chemistry described in *Computational Life* (Agüera y Arcas et al., 2024). Both populations contained 131,072 fixed-length, 64-byte programs.

In seed 2, replication-positive programs increased from zero at sampled checkpoints through epoch 1024 to 8,227 at epoch 1280 and 67,424 at epoch 1536. In seed 3, 21 replication-positive programs were detected at epoch 2816, including one with a perfect 64/64 copying score, but no positive programs were detected at subsequent sampled checkpoints through epoch 4096.

These observations motivate investigating replication emergence, lineage establishment, and population proliferation as potentially distinct processes. They do not establish the mechanisms responsible for the observed differences.

### 1. Research question

Under what conditions do replication-capable configurations establish persistent, proliferating populations rather than disappearing amid ongoing computational turnover?

Our working hypothesis is:

> Replication may emerge relatively readily under favorable computational conditions, while successful establishment depends on additional ecological and stochastic factors.

This hypothesis is not established by the present experiments.

### 2. Methods

We used the original BFF `bff_noheads` computational chemistry, based on repository revision:

`f212e849027c98fcf4b242eccfb5fed435223e23`

The population contained 131,072 programs, each 64 bytes long.

Saved populations were evaluated using BFF's original `CheckSelfRep` logic, exposed through an additional Python binding. The associated source patch is included with this note.

Scores range from 0 to 64. We report the original BFF replication threshold of at least 5, a high-fidelity threshold of at least 62, and perfect scores of 64.

These scores measure copying performance under evaluator conditions, not necessarily reproductive success in the evolving population.

Seed 2 was examined at epochs 0 through 1536, at intervals of 256. Its original complete launch configuration has not been recovered.

Seed 3 was run with seed 3, mutation probability 0.00024, clear interval 2048, and checkpoint interval 256. Its initial launch and subsequent checkpoint-resumed extension are documented in the accompanying command files.

The seed-3 launch requested a maximum of 1537 epochs but produced checkpoints through epoch 1792. The continuation loaded that checkpoint and generated observations through epoch 4096. Exact equivalence between the resumed and uninterrupted simulations has not been independently established.

### 3. Results

| Observation | Seed 2 | Seed 3 |
|---|---:|---:|
| Population size | 131,072 | 131,072 |
| First sampled replication-positive epoch | 1280 | 2816 |
| Positive programs at first detection | 8,227 | 21 |
| Perfect-score programs at first detection | 209 | 1 |
| Later sampled outcome | 67,424 positive at epoch 1536 | 0 positive at epoch 4096 |

#### 3.1 Seed 2

No programs met the replication threshold at sampled checkpoints through epoch 1024.

At epoch 1280, 8,227 programs scored at least 5, including 5,874 scoring at least 62 and 209 scoring 64.

At epoch 1536, 67,424 programs scored at least 5, including 61,416 scoring at least 62 and 3,816 scoring 64.

The final observed prevalence was approximately 51.44% of the population.

#### 3.2 Seed 3

No replication-positive programs were detected at sampled checkpoints through epoch 2560.

At epoch 2816, 21 programs scored at least 5. One scored 64/64.

At epochs 3072, 3328, 3584, 3840, and 4096, no programs met the replication threshold.

The data establish a transient replication-positive assay result. They do not establish that these programs reproduced in the evolving population or formed an identifiable lineage that subsequently became extinct.

### 4. Discussion

The observations distinguish the appearance of copying capability from sustained population-level proliferation.

One possibility is that replication-capable configurations arise during ordinary pre-transition computational turnover but often fail to establish persistent lineages.

Potential contributing factors include stochastic loss, overwriting, mutation, interaction partners, competition, and the balance between reproduction and destruction.

These explanations remain hypotheses. The present observations do not identify a causal mechanism.

The results are conceptually relevant to questions in artificial life and origin-of-life research, but they do not provide estimates of biological abiogenesis rates or the prevalence of extraterrestrial life.

### 5. Limitations

- Only two simulation trajectories have been examined.
- Seed 2's original complete launch configuration is unavailable.
- The evaluator measures copying capability under specified test conditions, not realized reproductive fitness.
- Checkpoints are separated by 256 epochs; shorter episodes may be missed.
- Seed 3 includes a checkpoint-resumed continuation.
- Lineage ancestry, persistence, and differential reproductive success have not yet been established.
- The population uses fixed-length tapes; variable-length degradation and fragmentation have not been tested.

### 6. Next steps

Future experiments will examine additional independent seeds under identical configurations, increase sampling resolution around transitions, and investigate whether replication-positive programs produce persistent descendants.

A longer-term goal is to distinguish factors that promote the emergence of copying capability from those that promote successful establishment and proliferation.

### 7. Conclusion

Two exploratory BFF trajectories exhibited markedly different replication-positive population dynamics. One showed rapid proliferation; the other showed a brief positive episode without sustained proliferation at sampled checkpoints.

These observations motivate treating emergence, establishment, and proliferation as distinct research questions.

The present study is preliminary and makes no claim to have identified their governing mechanisms.

### References

Agüera y Arcas, B., et al. (2024). *Computational Life*. Original implementation: https://github.com/paradigms-of-intelligence/cubff

Karelin, G. (2025). *The Fermi Paradox in Artificial Life*. https://karegeo.github.io/fermi_alife/

### Data and reproducibility

The accompanying publication directory contains the three replication trajectory CSVs, original and continuation commands for seed 3, and the source patch exposing BFF's replication evaluator.

Full population checkpoints are not included in this initial package. Reproducing the reported seed-2 trajectory may require recovering its original configuration.
