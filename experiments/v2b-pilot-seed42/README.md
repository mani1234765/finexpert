# v2b-pilot-seed42 — v2-B, second seed

**Purpose:** second seed of the self-distillation recipe ([v2b-pilot-seed3407](../v2b-pilot-seed3407/)); completes the 2-seed comparison used by the pre-registered v3 selection rule.

## Setup
Identical to v2b-pilot-seed3407 except `SEED = 42` (repo commit `de45988`, same 490/800 distilled targets). Training 41.5 min (324 tokens/s), peak 9.7 GB; evaluation 190 min.

## Results
| Metric | v2-A seed 3407 / 42 | v2-B seed 3407 | **v2-B seed 42** |
|---|---|---|---|
| FinQA accuracy | 59.7% / 60.0% | 59.0% | 64.0% (95% CI 58.4–69.2) |
| TAT-QA EM / F1 | 64.7% / 66.0% · 72.7% / 73.8% | 61.3% / 69.2% | 63.7% / 70.2% |
| Primary metric (mean of FinQA and TAT-QA EM) | 62.2% / 63.0% | 60.2% | 63.8% |
| Synthetic numeric recall / classification | 94.8% / 98.7% · 8/10 / 6/10 | 88.3% · 7/10 | 89.6% · 7/10 |
| Mean answer length | 48 tokens | 157 tokens | 209 tokens (11 of 630 hit the limit) |

### FinQA by calculation steps
| Steps | 1 (n=170) | 2 (n=103) | 3+ (n=27) |
|---|---|---|---|
| v2-A seed 3407 / 42 | 65% / 65% | 60% / 60% | 22% / 26% |
| v2-B seed 3407 | 66% | 50% | 52% |
| **v2-B seed 42** | 68% | 59% | 59% |

| Paired, within group (v2-B seed 42) | v2-B only right | v2-A only right | McNemar p (vs v2-A seed 3407 / 42) |
|---|---|---|---|
| 3+ steps | 10 / 9 | 0 / 0 | 0.002 / 0.004 |
| 2 steps | 9 / 9 | 10 / 10 | 1.000 / 1.000 |

## Analysis
- **The multi-step gain replicates.** Across both seeds of both recipes, reasoning-trained models solved 7–10 of the 3+ step questions that terse models missed, and the terse models never solved one the reasoning models missed.
- **The 2-step drop of seed 3407 does not replicate** (59% vs 60%), so it was seed-to-seed variation.
- **Seed variance is larger for v2-B** (FinQA 59.0% vs 64.0%) than for v2-A (59.7% vs 60.0%), plausibly because of the mixture of answer styles it learned.

## Decision (pre-registered rule)
v2-A mean 62.6% vs v2-B mean 62.0%; seed-matched paired test pooled over both datasets: 143 questions only v2-A right vs 136 only v2-B right, p = 0.72. Not significant, so the rule selects the cheaper recipe, **v2-A**, and within it the seed with the higher validation score, **seed 42** (63.0%). The v3 model is the `v2-pilot-seed42` adapter.
