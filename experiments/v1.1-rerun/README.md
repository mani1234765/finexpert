# FinExpert v1.1 — baseline rerun with full recording

Same data and training recipe as v1, run with `notebooks/finexpert_qwen3_4b_qlora.ipynb` on 6 Oct 2026 (Tesla T4).
Repo commit 4c5bf85; data hashes as in v1. Full configuration and package versions: `run_manifest.json`.

## Results (test, n=30)
| Metric | v1 | v1.1 | Base model (adapter off) |
|---|---|---|---|
| Figure fidelity | 100% | 100% | 33.3% |
| Numeric precision / recall | 100% / 100% | 98.7% / 98.7% | 70.3% / 9.1% |
| Classification accuracy | 80% (8/10) | 60% (6/10), 95% CI 31.3–83.2% | 0% (no label in required format) |
| Macro F1 | 0.749 | 0.500 | 0 |
| Section coverage | 100% | 100% | 10% |

Validation loss by epoch: 0.0911, 0.0160, 0.0136 (best = epoch 3). Training: 10.1 min, peak 8.41 GB.

## Key findings
- Same recipe, different result (80% vs 60%): run-to-run variance is large on 10 labelled examples; comparisons need multiple seeds.
- One genuine calculation error (fin_rev_018: +15.0% written as 14.7%).
- Base model answers in long markdown, never emits a `Classification:` line, and hit the 700-token limit on 25/30 answers; its scores reflect format, not reasoning.

## Files
`report.*` fine-tuned scores · `base_report.*` base-model scores · `*predictions.jsonl` raw outputs · `train_log.json` + `loss_curve.png` training history · `run_manifest.json` config, versions, timings · `requirements-colab.txt` pinned versions · `notebook_executed.ipynb` notebook with outputs.
The LoRA adapter (~140 MB) is stored in Google Drive (`MyDrive/finexpert/runs/v1.1-baseline-rerun/adapter`), not in git.
