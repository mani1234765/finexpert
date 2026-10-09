# Experiment log

Every training run is recorded here with its configuration, predictions, reports and a short write-up. Runs are compared only on identical evaluation questions, with paired tests (`scripts/compare_runs.py`); the official FinQA and TAT-QA **test** sets are reserved for final models.

| Run | Date | Platform | Training data | Purpose | Key result | Decision |
|---|---|---|---|---|---|---|
| [v1-baseline](v1-baseline/) | 5 Oct 2026 | Colab T4 | 240 synthetic | First fine-tune | Synthetic test: numeric 100%, classification 80% (8/10) after fixing evaluator bugs | Found and fixed evaluator false negatives; froze v1 data |
| [v1.1-rerun](v1.1-rerun/) | 6 Oct 2026 | Colab T4 | Same as v1 | Reproduce v1 with full recording | Classification 60% (6/10) with the same recipe | Run-to-run variance is large: compare with ≥3 seeds; put evidence before labels |
| [v2-pilot](v2-pilot/) | 8 Oct 2026 | Kaggle T4 | 300 FinQA + 500 TAT-QA + 240 synthetic | Validate real-data pipeline, measure speed | FinQA 59.7%, TAT-QA EM/F1 64.7/72.7 (validation subset, 1 seed) | Size v2-A; add a prompted baseline; calculator needs a structured format |
| [base-zero-few-shot](base-zero-few-shot/) | 8–9 Oct 2026 | Kaggle T4 | none (base model) | What does prompting alone achieve? | TAT-QA: fine-tuned far ahead (EM 64.7% vs 32.3%, p < 0.0001). FinQA: base zero-shot 65.0% vs fine-tuned 59.7% (p = 0.09, no fine-tuning gain) | Test a format-rules baseline; make reasoning-rich targets (v2-B) the central experiment |

## Findings so far
1. **Evaluate the evaluator.** Scoring reference answers against themselves exposed three evaluator bugs that under-scored v1 (76.6% → 100% numeric). The same invariant now guards every evaluator ([v1-baseline](v1-baseline/README.md)).
2. **Audit the data.** About 13% of FinQA's written answers disagree with their own executed calculation; these are excluded from training, with the executed result used as gold (`data/external/audit.json`).
3. **One run is not a result.** Identical recipe, 80% vs 60% classification across two runs ([v1.1-rerun](v1.1-rerun/README.md)).
4. **Arithmetic is a large share of errors.** Up to a quarter of FinQA errors and ~40% of TAT-QA calculation errors are miscalculations on correctly chosen figures ([v2-pilot](v2-pilot/README.md)).
5. **Beat a prompted baseline, not just the base model.** Fine-tuning won TAT-QA by 32 points, but about two-thirds of the base model's TAT-QA misses had the right number in the wrong format; on FinQA the pilot did not beat zero-shot prompting ([base-zero-few-shot](base-zero-few-shot/README.md)).
6. **Terse targets may cost reasoning.** On 3+ step FinQA questions the base model (about 300 tokens of reasoning) scored 59% vs 22% for the fine-tuned model (about 48 tokens); few-shot examples in the terse format also hurt the base model (p = 0.044).

## Conventions
- Each run folder: `README.md` (setup, results, analysis, decision), predictions (`*.jsonl`), reports (`*.json`/`*.txt`), `run_manifest.json` (exact config, versions, timings).
- Model weights (LoRA adapters) are not stored in git.
