# Experiment log

Every training run is recorded here with its configuration, predictions, reports and a short write-up. Runs are compared only on identical evaluation questions, with paired tests (`scripts/compare_runs.py`); the official FinQA and TAT-QA **test** sets are reserved for final models.

| Run | Date | Platform | Training data | Purpose | Key result | Decision |
|---|---|---|---|---|---|---|
| [v1-baseline](v1-baseline/) | 5 Oct 2026 | Colab T4 | 240 synthetic | First fine-tune | Synthetic test: numeric 100%, classification 80% (8/10) after fixing evaluator bugs | Found and fixed evaluator false negatives; froze v1 data |
| [v1.1-rerun](v1.1-rerun/) | 6 Oct 2026 | Colab T4 | Same as v1 | Reproduce v1 with full recording | Classification 60% (6/10) with the same recipe | Run-to-run variance is large: compare with ≥3 seeds; put evidence before labels |
| [v2-pilot](v2-pilot/) | 8 Oct 2026 | Kaggle T4 | 300 FinQA + 500 TAT-QA + 240 synthetic | Validate real-data pipeline, measure speed | FinQA 59.7%, TAT-QA EM/F1 64.7/72.7 (validation subset, 1 seed) | Size v2-A; add a prompted baseline; calculator needs a structured format |
| [base-zero-few-shot](base-zero-few-shot/) | 8–9 Oct 2026 | Kaggle T4 | none (base model) | What does prompting alone achieve? | TAT-QA: fine-tuned far ahead (EM 64.7% vs 32.3%, p < 0.0001). FinQA: base zero-shot 65.0% vs fine-tuned 59.7% (p = 0.09, no fine-tuning gain) | Test a format-rules baseline; make reasoning-rich targets (v2-B) the central experiment |
| [base-zero-shot-rules](base-zero-shot-rules/) | 9 Oct 2026 | Kaggle T4 | none (base model) | Fair baseline: answer conventions stated in the prompt | TAT-QA EM 32.3% → 61.3%; vs fine-tuned pilot: no significant difference on FinQA (p = 0.28) or TAT-QA (p = 0.33) | Fine-tuning's QA gain was conventions; test self-distilled reasoning (v2-B) |
| [v2-pilot-seed42](v2-pilot-seed42/) | 9 Oct 2026 | Kaggle T4 | Same as v2-pilot | Second seed: run-to-run variance | FinQA 60.0%, TAT-QA EM/F1 66.0/73.8; vs seed 3407 p = 1.00 / 0.58; classification 6/10 (vs 8/10) | QA results stable across seeds; 10-example classification is not |
| [distill-v2-pilot](distill-v2-pilot/) | 9 Oct 2026 | Kaggle T4 | none (generation only) | Self-distilled reasoning targets for v2-B | 490/800 answers verified correct and kept (FinQA 71%, TAT-QA 55%) | Train v2-B on them, 2 seeds |
| [v2b-pilot-seed3407](v2b-pilot-seed3407/) | 9 Oct 2026 | Kaggle T4 | Pilot mix, 490/800 QA targets distilled reasoning | Do reasoning targets fix multi-step FinQA? | Overall no change (FinQA 59.0%, TAT-QA EM 61.3%); 3+ step FinQA 22–26% → 52% (p ≤ 0.016) but 2-step 60% → 50% | Second seed; reasoning-only targets as next step |
| [v2b-pilot-seed42](v2b-pilot-seed42/) | 9 Oct 2026 | Kaggle T4 | Same as v2b-pilot-seed3407 | Second seed of v2-B | FinQA 64.0%, TAT-QA EM 63.7%; 3+ step FinQA 59% (vs 22–26% for v2-A, p ≤ 0.004); 2-step drop not replicated | Rule outcome: v2-A selected (62.6% vs 62.0%, p = 0.72); v3 = v2-pilot-seed42 |
| [v3-test](v3-test/) | 14–15 Oct 2026 | Kaggle T4 | none (evaluation of the v2-pilot-seed42 adapter) | Final model on the official test sets, once | FinQA 62.0% (n=1,147); TAT-QA EM/F1 62.1% / 70.2% (n=1,663; TAGOP 50.1 / 58.0, GPT-4 zero-shot 71.9 / 79.7) | Project complete; next steps in the main README |

## Findings so far
1. **Evaluate the evaluator.** Scoring reference answers against themselves exposed three evaluator bugs that under-scored v1 (76.6% → 100% numeric). The same invariant now guards every evaluator ([v1-baseline](v1-baseline/README.md)).
2. **Audit the data.** About 13% of FinQA's written answers disagree with their own executed calculation; these are excluded from training, with the executed result used as gold (`data/external/audit.json`).
3. **One run is not a result.** Identical recipe, 80% vs 60% classification across two runs ([v1.1-rerun](v1.1-rerun/README.md)).
4. **Arithmetic is a large share of errors.** Up to a quarter of FinQA errors and ~40% of TAT-QA calculation errors are miscalculations on correctly chosen figures ([v2-pilot](v2-pilot/README.md)).
5. **Beat a fair prompted baseline, not just the base model.** Fine-tuning appeared to win TAT-QA by 32 points; once the base model was told the answer conventions, the gap vanished (61.3% vs 64.7%, p = 0.33), and on FinQA the pilot never beat prompting ([base-zero-shot-rules](base-zero-shot-rules/README.md)). What fine-tuning did add: structured domain outputs (classification 8/10 vs 0/10) and the same QA accuracy in about 1/6 of the tokens.
6. **Terse targets may cost reasoning.** On 3+ step FinQA questions the base model (about 300 tokens of reasoning) scored 59% vs 22% for the fine-tuned model (about 48 tokens); few-shot examples in the terse format also hurt the base model (p = 0.044).
7. **Distilled reasoning fixes multi-step questions, replicated.** Training on the base model's verified reasoning raised 3+ step FinQA accuracy from 22–26% to 52–59% across two seeds (v2-B solved 7–10 questions the terse models missed and lost none; p ≤ 0.016 in every seed pairing), with no change in overall accuracy and about 4× longer answers ([v2b-pilot-seed42](v2b-pilot-seed42/README.md)).

## Pre-registered selection rule for v3
Recorded on 9 Oct 2026 **before** the v2-B seed 42 result was available (see this file's git history).

| Rule | |
|---|---|
| Primary metric | Mean of FinQA accuracy and TAT-QA EM on the validation subset, averaged over the 2 seeds of each recipe |
| If the recipes' difference is not statistically significant | Choose the cheaper recipe (shorter answers) |
| Seed within the winning recipe | The seed with the higher primary metric on validation |
| Test sets | Scored once, for the selected adapter only; test results are never used for selection |

Standing at registration: v2-A 62.6% (seeds 3407 and 42), v2-B 60.2% (seed 3407 only).

**Outcome (applied after v2-B seed 42):** v2-A 62.58% vs v2-B 62.00% (seed-matched pooled McNemar p = 0.72, not significant) → cheaper recipe **v2-A**; best validation seed **42** (63.0% vs 62.2%). The v3 model is `v2-pilot-seed42`. v2-B's single best seed (63.8%) was not selected: the rule compares recipes, not lucky seeds.

## Conventions
- Each run folder: `README.md` (setup, results, analysis, decision), predictions (`*.jsonl`), reports (`*.json`/`*.txt`), `run_manifest.json` (exact config, versions, timings).
- Model weights (LoRA adapters) are not stored in git.
