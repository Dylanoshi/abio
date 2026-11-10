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
