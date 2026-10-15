# v3-test — final model on the official test sets

**Purpose:** score the model chosen by the [pre-registered rule](../README.md#pre-registered-selection-rule-for-v3) once on the official FinQA and TAT-QA test sets. Test results were not used for any decision.

## Setup
| Item | Value |
|---|---|
| Date / platform | 14–15 Oct 2026, Kaggle, 1× Tesla T4 (repo commit `704205e`) |
| Model | Adapter saved by [v2-pilot-seed42](../v2-pilot-seed42/) (v2-A recipe), loaded from that run's Kaggle output; base `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit`, r 16, alpha 16 (checked against the config) |
| Mode | `RUN_MODE = "test"`: no training; greedy decoding, 384-token answer budget |
| Test sets | FinQA `test.json` (1,147) and TAT-QA `tatqa_dataset_test_gold.json` (1,663): 2,810 questions, all scored, 1 hit the token limit |
| Time | 122 min for the QA test sets |

## Results
| Metric | Validation subset (same adapter) | **Official test** |
|---|---|---|
| FinQA answer accuracy | 60.0% (n=300) | **62.0%** (95% CI 59.1–64.8, n=1,147) |
| TAT-QA EM / F1 (official scorer) | 66.0% / 73.8% (n=300) | **62.1% / 70.2%** (F1 95% CI 68.0–72.2, n=1,663) |
| TAT-QA scale accuracy | 96.7% | 97.5% |
| `Answer:` line rate | 100% | 99.96% |

Test scores sit close to validation, with no sign of overfitting to the validation questions.

**FinQA by calculation steps (test):** 1 step 65.3% (n=654), 2 steps 62.1% (n=409), 3+ steps 35.7% (n=84).

**TAT-QA by answer type (test):** span 64.0% (n=714), multi-span 78.6% (n=210), arithmetic 56.2% (n=699), count 42.5% (n=40).

### Context: published TAT-QA test results
Same test set and official scorer, so directly comparable.

| System | F1 | EM |
|---|---|---|
| Human experts | 90.8% | 84.1% |
| TAT-LLM 7B (fine-tuned) | 82.9% | 74.6% |
| GPT-4, zero-shot | 79.7% | 71.9% |
| **FinExpert v3 (Qwen3-4B, QLoRA, 500 TAT-QA training questions, 35 min on one T4)** | **70.2%** | **62.1%** |
| TAGOP (the TAT-QA paper's model) | 58.0% | 50.1% |

FinQA is not placed beside published results: they usually report program execution accuracy, while this project scores final answers.

### Synthetic test (30 examples)
Numeric recall 98.7%, figure fidelity 100%, classification 6/10. The synthetic test set was scored in every run since v1, so unlike the official test sets it is not a once-only held-out measurement.

## Interpretation
- The selected model generalises from the validation subset to the full official test sets (FinQA +2.0 pts, TAT-QA EM −3.9 pts; the validation subset was capped at 2,048 tokens and stratified by answer type, so small shifts are expected).
- Multi-step weakness persists on the test set (3+ steps 35.7%), consistent with validation and with the v2-B finding that reasoning-rich targets address it.
