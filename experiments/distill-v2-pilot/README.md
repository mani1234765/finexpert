# distill-v2-pilot — self-distilled reasoning targets (input to v2-B)

**Purpose:** produce reasoning-rich training targets for v2-B by rejection sampling. The base model answers the 800 FinQA / TAT-QA *training* questions of the pilot mix; only answers verified correct by the evaluation scorers (and passing quality checks in `src/finexpert/data/distill.py`) become targets.

## Setup
| Item | Value |
|---|---|
| Date / platform | 9 Oct 2026, Kaggle, 1× Tesla T4 (repo commit `3dc34cd`) |
| Model / prompt | Base model, zero-shot + format rules (as [base-zero-shot-rules](../base-zero-shot-rules/)); greedy decoding, 1,024-token budget, stop after a complete `Answer:` line |
| Questions | The 300 FinQA + 500 TAT-QA training questions of `train_mix_v2_pilot.json` (no evaluation questions; checked in the notebook) |
| Output | `data/external/distilled/distilled_targets_v2_pilot.jsonl` (sha256 `43488a10db091d13809bffb987034954ab67ba8ccf74f1224051efb469d43214`) |
| Time | 168 min |

## Results
| | Accepted | Rate |
|---|---|---|
| FinQA | 214 / 300 | 71% |
| TAT-QA | 276 / 500 | 55% |
| **Total** | **490 / 800** | **61%** |

By answer type: FinQA calculations 208/294 (71%), yes/no 6/6; TAT-QA calculations 147/250 (59%), multi-span 45/75 (60%), count 28/50 (56%), span 56/125 (45%).

Rejections: wrong answer 280, hit the token limit 21, more than one `Answer:` line 5, no reasoning 4.

Accepted targets are the model's own step-by-step reasoning (median 566 characters vs about 120 for the template targets), ending with the canonical gold answer. Most use bullet points; 82 (17%) use LaTeX notation.

## Known imperfections
Rejection sampling verifies the final answer, not every line: some accepted targets have imperfect commentary or formatting (e.g. an unclosed LaTeX block before the answer). The 310 rejected questions keep their template targets, so v2-B trains on exactly the same questions as v2-A.
