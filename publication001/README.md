# ABIO

**Investigating the possibility of computational abiogenesis.**

ABIO is an independent experimental research project investigating how replication-capable systems emerge, persist, and evolve in computational environments.

## Research question

Can replication emerge spontaneously in computational systems, and what determines whether replication-capable configurations establish persistent, proliferating populations?

Our working hypothesis:

> Replication may emerge relatively readily under favorable computational conditions, while successful establishment depends on additional ecological and stochastic factors.

## Research

### Research Note 001 — Divergent Replication Trajectories in a Computational Chemistry

Our first preliminary report examines two experimental trajectories using the BFF computational chemistry developed by Blaise Agüera y Arcas and collaborators.

One trajectory exhibited rapid proliferation of replication-positive programs. Another exhibited a transient replication-positive episode without sustained proliferation at sampled checkpoints.

These observations motivate further investigation. They do not establish the mechanisms responsible for the differences.

**[Read Research Note 001](001-emergence-establishment.md)**

## Data and reproducibility

The `data/` directory contains the replication trajectories for both experiments.

The repository also includes the recorded seed-3 simulation commands and a patch exposing the original BFF self-replication evaluator through Python.

Original BFF implementation:
https://github.com/paradigms-of-intelligence/cubff

## Status

ABIO is an independent, exploratory research initiative. Findings are preliminary and have not undergone peer review.

Research notes will be updated as experiments are reproduced, extended, and independently evaluated.

## Website

https://abio.life
