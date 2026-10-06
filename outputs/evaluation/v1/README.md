# FinExpert v1 baseline — results record

## What produced these files
| Item | Value |
|---|---|
| Training run | Fresh Colab run on 5 Oct 2026 (Tesla T4) |
| Notebook | `notebooks/archive/v1_finexpert_qwen3_4b_finetune.ipynb` |
| Base model | `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit` |
| LoRA | r=16, alpha=16, dropout=0, all 7 attention/MLP projections |
| Training | 3 epochs, LR 2e-4, batch 2 x accum 4 (eff. 8), warmup 0.1 linear, weight decay 0.01, adamw_8bit, seed 3407, max length 2048, loss on assistant answer only, best epoch by val loss |
| Decoding | Greedy, max_new_tokens=700 |
| Data | `data/sft/` — train b9fe27b8..., validation 165c3bf0..., test 851220d9... (SHA-256) |

## Files
| File | Contents |
|---|---|
| `test_predictions.jsonl` | Model outputs for all 30 test examples (primary artifact of the run) |
| `evaluation_report_original_buggy_evaluator.json` | Scored in Colab with evaluator at commit f970624. **Do not cite**: under-scored correct answers |
| `evaluation_report_corrected.json` / `.txt` | Same predictions rescored with the fixed evaluator (commit 4e1c1dc) |

## Corrected results (test, n=30)
| Metric | Value |
|---|---|
| Figure fidelity | 100% |
| Numeric precision / recall | 100% / 100% |
| Classification accuracy | 80% (8/10), 95% CI 49.0–94.3% |
| Macro F1 / weighted F1 | 0.749 / 0.798 |
| Section coverage | 100% |
| Verbatim reference match (diagnostic) | 76.7% |

Classification errors: fin_debt_017 (Moderate Risk -> Healthy), fin_risk_023 (High Risk -> Moderate Risk); both easy, single-signal examples at rule thresholds.

## Why the scores were corrected
Evaluator bugs were found by scoring the reference answers against themselves, before any model predictions were inspected: source inputs use "changing/increasing" (not parsed), 1-decimal percent ratios failed a 0.015 tolerance, and repeated figures were counted as invented. The references scored 76.62% numeric against themselves; after the fix they score 100%.

## Known gaps
- LoRA adapter from this run was not saved.
- Training/validation loss history and best epoch were not saved.
- Library versions were not recorded.
- Base-model (adapter off) predictions were not saved.
These are fixed in `notebooks/finexpert_qwen3_4b_qlora.ipynb` (v1.1), which uses the same training recipe.
