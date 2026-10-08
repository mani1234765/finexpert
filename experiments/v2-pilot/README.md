# v2-pilot — first run on real-report data (FinQA + TAT-QA)

**Purpose:** prove the real-data pipeline end to end on Kaggle and measure training/inference speed to size the full v2 runs. Not a final result: 1 seed, validation subset only, no baseline.

## Setup
| Item | Value |
|---|---|
| Date / platform | 8 Oct 2026, Kaggle, 1× Tesla T4 |
| Notebook | `notebooks/finexpert_v2_train.ipynb` (repo commit `d762e5e`) |
| Training mix | `data/external/train_mix_v2_pilot.json`: 300 FinQA + 500 TAT-QA + 240 synthetic = 1,040 examples, 723,617 tokens, none over 2,048 |
| Recipe | Same LoRA as v1.1 (r 16, alpha 16, dropout 0, all projections), LR 2e-4, effective batch 8, **1 epoch**, warmup 5% linear, seed 3407 |
| Evaluation | Fixed validation subset `data/external/eval_subset_v1.json` (300 FinQA + 300 TAT-QA, never trained on) + the 30 synthetic test examples |
| Versions | unsloth 2026.10.2, torch 2.11.0+cu128, transformers 5.16.1, trl 1.13.0, peft 0.20.0 (see `run_manifest.json`) |

## Results
| Metric | Value |
|---|---|
| FinQA answer accuracy | 59.7% (95% CI 54.0–65.1%) |
| TAT-QA official EM / F1 | 64.7% / 72.7% (F1 95% CI 67.7–77.4%) |
| `Answer:` line followed | 100%; 0 answers hit the token limit |
| Synthetic test | classification 80% (8/10, same two misses as v1); numeric recall 94.8%; figure fidelity 100% |
| Speed | 31.9 min training (378 tokens/s), 29.3 min evaluation, 11.7 GB peak GPU memory |

Monitoring (validation) loss: 0.317 → 0.150 → 0.121 → 0.103 → 0.097 (steps 25–130), still flattening at the end of the epoch.

## Error analysis
- **Accuracy falls with calculation length** (FinQA): 1 step 65.3% (n=170), 2 steps 60.2% (n=103), 3 steps 35.3% (n=17), 4–5 steps 0% (n=10).
- **Arithmetic slips**: re-computing every calculation line the model wrote, up to 28 of 118 wrong FinQA answers and 18 of 43 wrong TAT-QA calculation answers contain a miscalculation with the right inputs (e.g. (592 − 519) ÷ 519 written as 0.1398 instead of 0.1407). Counts are upper bounds; a few are rounding-only differences.
- **Reasoning errors**: the rest are correct arithmetic on the wrong figures or operation.
- **Scale**: 10 TAT-QA answers had the right number with the wrong scale (e.g. thousand vs million).
- **Synthetic tasks held up** after adding real data; numeric recall dipped from 98.7–100% to 94.8% (some metrics omitted, one calculation error).

## Rejected idea: post-hoc calculator
Re-computing the model's free-text working with Python and rebuilding its answer fixed 17 answers but broke 57 (e.g. all yes/no answers), so it was not adopted. Rebuilding answers from free text is too fragile; a calculator needs a structured calculation format the model is trained to emit (planned as its own experiment, v2-C).

## Decision
- Pipeline validated on Kaggle; speed measured.
- Next: a prompted base-model baseline on the same questions, then v2-A (800 FinQA + 1,200 TAT-QA + 240 synthetic, ≈1.73M tokens, ≈76 min training per run) with 3 seeds.

## Correction (8 Oct 2026)
`finetuned_qa_report.*` show TAT-QA **scale accuracy 72.3%**. That figure came from a tie-break bug in our scorer: when two
readings of an answer scored the same EM/F1, the scale of the wrong reading could be kept. Rescoring the same predictions with
the fixed scorer gives **97.7%**; official EM (64.7%) and F1 (72.7%) are unchanged. The original report files are kept as
produced; the fix and its regression test are in the commit that added this note.

## Files
`finetuned_qa_*` QA predictions and report · `finetuned_synthetic_*` synthetic test predictions and report · `train_log.json`, `loss_curve.png` training history · `run_manifest.json` config, versions, timings · `requirements-kaggle.txt` pinned versions. The LoRA adapter is not stored in git.
