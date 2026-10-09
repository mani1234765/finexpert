# v2-pilot-seed42 — second seed of the v2-A recipe (template targets)

**Purpose:** repeat [v2-pilot](../v2-pilot/) with a different seed to measure run-to-run variance before comparing recipes.

## Setup
Identical to v2-pilot (same mix of 1,040 examples / 723,617 tokens, same recipe, Kaggle T4) except `SEED = 42` (repo commit `f8f073c`). Training 34.7 min (348 tokens/s), peak 11.9 GB.

## Results
| Metric | Seed 3407 (v2-pilot) | Seed 42 | Mean of 2 seeds |
|---|---|---|---|
| FinQA accuracy | 59.7% | 60.0% (95% CI 54.4–65.4) | 59.8% |
| TAT-QA EM / F1 | 64.7% / 72.7% | 66.0% / 73.8% | 65.3% / 73.2% |
| Synthetic numeric recall | 94.8% | 98.7% | 96.8% |
| Synthetic classification | 8/10 | 6/10 | 7/10 |
| `Answer:` line rate | 100% | 100% | |

### Paired comparisons (`scripts/compare_runs.py`)

**Seed 3407 vs seed 42**

| Source | n | seed 3407 | seed 42 | Difference | seed 3407 only right | seed 42 only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 59.7% | 60.0% | +0.3 pts | 14 | 15 | 1.0000 |
| tatqa | 300 | 64.7% | 66.0% | +1.3 pts | 13 | 17 | 0.5847 |

**Base + format rules vs seed 42**

| Source | n | base+rules | seed 42 | Difference | base+rules only right | seed 42 only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 63.3% | 60.0% | -3.3 pts | 46 | 36 | 0.3203 |
| tatqa | 300 | 61.3% | 66.0% | +4.7 pts | 34 | 48 | 0.1507 |

## Analysis
- **QA results are stable across seeds:** about 30 of 300 questions flip in each direction and neither difference is significant, so a single v2 run is representative for FinQA / TAT-QA at this scale.
- **The 10-example classification test is not:** 8/10 vs 6/10 with the same recipe, as in v1 vs v1.1. Classification claims need a larger labelled test set.
- The comparison with the format-rules baseline repeats the seed-3407 picture: no significant difference on either QA dataset.

## Files
As in v2-pilot: `finetuned_*` predictions and reports, `train_log.json`, `loss_curve.png`, `run_manifest.json`, `requirements-kaggle.txt`. The adapter is in the Kaggle run output, not in git.
