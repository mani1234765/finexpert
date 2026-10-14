# v2b-pilot-seed3407 — v2-B: self-distilled reasoning targets (seed 3407)

**Purpose:** test whether training on the base model's own verified-correct reasoning ([distill-v2-pilot](../distill-v2-pilot/)) fixes the terse model's weakness on multi-step FinQA questions while keeping its strengths.

## Setup
Identical to [v2-pilot](../v2-pilot/) (same 1,040 questions, recipe, seed 3407) except that 490 of the 800 QA targets are replaced by distilled reasoning (`DISTILLED_TARGETS`, sha256 `43488a10…`); the other 310 keep their template targets. 807,029 training tokens (vs 723,617), 35.8 min (376 tokens/s), peak 9.0 GB. Repo commit `de45988`. Answer budget 1,024 tokens with stop after a complete `Answer:` line.

## Results
| Metric | v2-A seed 3407 | v2-A seed 42 | **v2-B seed 3407** |
|---|---|---|---|
| FinQA accuracy | 59.7% | 60.0% | 59.0% (95% CI 53.4–64.4) |
| TAT-QA EM / F1 | 64.7% / 72.7% | 66.0% / 73.8% | 61.3% / 69.2% (F1 CI 64.1–74.0) |
| Synthetic numeric recall | 94.8% | 98.7% | 88.3% |
| Synthetic classification | 8/10 | 6/10 | 7/10 |
| Mean answer length | 48 tokens | 48 tokens | 157 tokens |
| Evaluation time | 29 min | 30 min | 124 min |

Paired tests (McNemar) against v2-A: FinQA p = 0.90 (seed 3407) / 0.80 (seed 42); TAT-QA p = 0.30 / 0.11. No overall difference.

### Where it differs: FinQA by number of calculation steps
| Steps | 1 (n=170) | 2 (n=103) | 3+ (n=27) |
|---|---|---|---|
| Base + format rules | 68% | 56% | 63% |
| v2-A seed 3407 / 42 | 65% / 65% | 60% / 60% | 22% / 26% |
| **v2-B seed 3407** | 66% | 50% | 52% |

| Paired, within group | v2-B only right | v2-A only right | McNemar p (vs seed 3407 / 42) |
|---|---|---|---|
| 3+ steps | 8 / 7 | 0 / 0 | 0.008 / 0.016 |
| 2 steps | 4 / 5 | 15 / 16 | 0.019 / 0.027 |

## Analysis
- **Reasoning targets help multi-step questions.** On 3+ step questions v2-B solved 7–8 questions the terse models never solved and lost none. These are subgroup tests on small groups; only the 3+ step result vs seed 3407 survives a Bonferroni correction for the four tests, so this is strong evidence rather than proof.
- **But 2-step accuracy fell**, so overall accuracy is unchanged.
- **The model learned two styles.** Because 310 targets stayed terse, v2-B now picks a style per question: reasoning style on 206 FinQA / 101 TAT-QA answers (66% / 81% correct), template style on 94 / 199 (45% / 51% correct). This is confounded: template targets were kept exactly on the questions the base model could not solve, so the model likely learned "hard-looking question → terse style". The accuracy gap by style is not evidence that style causes accuracy.
- **Costs:** answers 3× longer (evaluation 124 vs 30 min) and lower synthetic numeric recall (88% vs 95–99%).

## Next step suggested by this run
Reasoning-only targets: sample several answers per training question during distillation so most questions get a verified reasoning target, removing the style mixture.

## Files
As in v2-pilot. The adapter is in the Kaggle run output, not in git.
