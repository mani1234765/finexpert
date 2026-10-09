# base-zero-shot-rules — base model told the answer conventions

**Purpose:** a fair baseline. The earlier baselines were never told TAT-QA's answer conventions (scale words, `; ` between items), which the fine-tuned model learned from its targets. This run adds those rules to the prompt to separate *convention learning* from *reasoning*.

## Setup
| Item | Value |
|---|---|
| Date / platform | 9 Oct 2026, Kaggle, 1× Tesla T4 (repo commit `f8f073c`) |
| Prompt | Zero-shot training prompt + `QA_FORMAT_RULES` on FinQA/TAT-QA questions (`src/finexpert/evaluation/prompting.py`); synthetic prompts unchanged |
| Settings | As in [base-zero-few-shot](../base-zero-few-shot/): base model, 1,024-token budget, stop after a complete `Answer:` line |
| Evaluation | Same 600 validation questions + 30 synthetic test examples |

## Results
| Model | FinQA accuracy | TAT-QA EM / F1 | TAT-QA scale accuracy | Synthetic classification / numeric recall | Mean answer length |
|---|---|---|---|---|---|
| Base, zero-shot | 65.0% | 32.3% / 41.5% | 64.7% | 0/10 / 10.4% | 308 tokens |
| **Base, zero-shot + rules** | **63.3%** (95% CI 57.7–68.6) | **61.3% / 67.2%** | 88.0% | 0/10 / 10.4% | 268 tokens |
| Fine-tuned pilot | 59.7% | 64.7% / 72.7% | 97.7% | 8/10 / 94.8% | 48 tokens |

21 of 630 answers hit the 1,024-token limit.

### Paired comparisons (McNemar's exact test, `scripts/compare_runs.py`)

**Zero-shot vs zero-shot + rules**

| Source | n | zero-shot | zero-shot+rules | Difference | zero-shot only right | zero-shot+rules only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 65.0% | 63.3% | -1.7 pts | 21 | 16 | 0.5114 |
| tatqa | 300 | 32.3% | 61.3% | +29.0 pts | 20 | 107 | < 0.0001 |

**Zero-shot + rules vs fine-tuned pilot**

| Source | n | zero-shot+rules | fine-tuned pilot | Difference | zero-shot+rules only right | fine-tuned pilot only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 63.3% | 59.7% | -3.7 pts | 49 | 38 | 0.2836 |
| tatqa | 300 | 61.3% | 64.7% | +3.3 pts | 37 | 47 | 0.3261 |

## Analysis
- **Answer conventions explain the TAT-QA gap.** Stating the rules lifts the base model from 32.3% to 61.3% EM (p < 0.0001), largely via scale (accuracy 64.7% → 88.0%) and list format (multi-span 0% → 70.2%). FinQA, which has no such conventions, is unchanged (p = 0.51).
- **With the rules, prompted base and fine-tuned pilot are statistically indistinguishable** on both QA datasets (p = 0.28 and p = 0.33). The pilot fine-tune's QA advantage over the plain base model was convention learning.
- **What fine-tuning still adds:** structured domain outputs the base model cannot produce even with rules (classification 0/10 vs 8/10; numeric recall 10% vs 95%), and the same QA accuracy in about 1/6 of the tokens (48 vs 268), i.e. lower cost and latency.
- **Multi-step FinQA still separates the two:** 3+ step questions 63% (17/27) for the base model vs 22% (6/27) fine-tuned, consistent with the hypothesis that terse targets cost reasoning.

## Decision
Self-distillation (v2-B): train the fine-tuned model on the base model's own *verified-correct* reasoning for the training questions, to test whether it can match or beat the prompted base model on QA while keeping its structured-output skills.

## Files
`base_zero_shot_rules_*`: predictions and reports · `run_manifest.json` · `requirements-kaggle.txt`.
