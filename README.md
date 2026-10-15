# FinExpert: fine-tuning a 4B model for grounded financial analysis

**Model:** [ManideepVarma003/finexpert-qwen3-4b-lora](https://huggingface.co/ManideepVarma003/finexpert-qwen3-4b-lora) on Hugging Face (the exact adapter scored on the test sets, with a quick-start snippet).

FinExpert fine-tunes **Qwen3-4B-Instruct** with QLoRA on a free Tesla T4 to answer numerical questions over real company reports (FinQA, TAT-QA) and to produce structured financial explanations, risk classifications and reports. Every result is measured against prompted baselines on fixed evaluation questions, with paired significance tests, multiple seeds and a pre-registered model-selection rule.

**Final model on the official test sets:** FinQA **62.0%** answer accuracy (n=1,147) and TAT-QA **62.1% EM / 70.2% F1** (n=1,663), 12 F1 points above the TAT-QA paper's model, trained in 35 minutes on one free T4.

**Headline (validation subset, 600 questions):** a well-prompted base model and the fine-tuned model reach the **same QA accuracy**, but the fine-tuned model does it in **about 1/6 of the tokens** and is the only one that produces the structured domain outputs. Training on the base model's own verified reasoning (**self-distillation**) more than doubled accuracy on 3+ step FinQA questions (22–26% → 52–59%, replicated across two seeds) at no cost in overall accuracy, but with about 4× longer answers.

## Results

Validation subset: 300 FinQA + 300 TAT-QA questions (`data/external/eval_subset_v1.json`, never trained on) + 30 synthetic test examples. 95% confidence intervals and paired McNemar tests are in each experiment's README.

| Model | FinQA accuracy | TAT-QA EM / F1 | Synthetic classification | Synthetic numeric recall | Answer length |
|---|---|---|---|---|---|
| Base, zero-shot | 65.0% | 32.3% / 41.5% | 0/10 | 10% | 308 tokens |
| Base, zero-shot + answer-format rules | 63.3% | 61.3% / 67.2% | 0/10 | 10% | 268 tokens |
| **v2-A** fine-tuned, template targets (mean of 2 seeds) | 59.8% | 65.3% / 73.2% | 7/10 | 97% | **48 tokens** |
| **v2-B** fine-tuned, distilled reasoning (mean of 2 seeds) | 61.5% | 62.5% / 69.7% | 7/10 | 89% | 183 tokens |

**Final model (v3):** v2-A seed 42, selected by the [pre-registered rule](experiments/README.md#pre-registered-selection-rule-for-v3) (v2-A 62.6% vs v2-B 62.0% on the primary metric, p = 0.72, so the cheaper recipe), then scored once on the official test sets ([v3-test](experiments/v3-test/README.md)):

| Official test set | FinQA answer accuracy | TAT-QA EM / F1 |
|---|---|---|
| **FinExpert v3** | **62.0%** (95% CI 59.1–64.8, n=1,147) | **62.1% / 70.2%** (n=1,663) |

For context on TAT-QA (same test set and official scorer): TAGOP, the paper's model, 50.1% / 58.0%; GPT-4 zero-shot 71.9% / 79.7%; TAT-LLM 7B 74.6% / 82.9%; human experts 84.1% / 90.8%. FinQA is not compared with published results, which usually score generated programs rather than final answers.

FinQA by number of calculation steps:

| Steps | 1 (n=170) | 2 (n=103) | 3+ (n=27) |
|---|---|---|---|
| Base + rules | 68% | 56% | 63% |
| v2-A (seeds 3407 / 42) | 65% / 65% | 60% / 60% | 22% / 26% |
| v2-B (seeds 3407 / 42) | 66% / 68% | 50% / 59% | 52% / 59% |

## What the experiments showed

1. **Evaluate the evaluator.** Scoring the reference answers against themselves exposed three bugs that under-scored the first model (76.6% → 100% numeric). The same invariant now guards every scorer ([v1-baseline](experiments/v1-baseline/README.md)).
2. **Audit the data.** About 13% of FinQA's written answers disagree with their own executed calculation; the executed result is used as gold and those examples are excluded from training (`data/external/audit.json`).
3. **One run is not a result.** The same recipe gave 80% and 60% on a 10-example classification test ([v1.1-rerun](experiments/v1.1-rerun/README.md)); QA results on 300 questions were stable across seeds ([v2-pilot-seed42](experiments/v2-pilot-seed42/README.md)).
4. **Beat a fair baseline.** Fine-tuning first appeared to win TAT-QA by 32 points; once the base model was told the answer conventions, the gap disappeared (p = 0.33) ([base-zero-shot-rules](experiments/base-zero-shot-rules/README.md)).
5. **What fine-tuning actually bought:** structured domain outputs the base model cannot produce, and the same QA accuracy in about 1/6 of the tokens (5× faster evaluation).
6. **Terse targets cost multi-step reasoning; distilled reasoning recovers it.** On 3+ step FinQA questions, self-distilled models solved 7–10 questions the terse models never solved and lost none, in both seeds (p ≤ 0.016 in every pairing); a 2-step drop in the first seed did not replicate. The cost is about 4× longer answers and a mixture of answer styles ([v2b-pilot-seed3407](experiments/v2b-pilot-seed3407/README.md), [v2b-pilot-seed42](experiments/v2b-pilot-seed42/README.md)).

7. **Pre-register the selection rule.** The rule for choosing the final model was committed before the deciding run finished; it picked the cheaper recipe over the run with the single best score ([experiments/README.md](experiments/README.md#pre-registered-selection-rule-for-v3)).

The full record (setup, results, analysis and decision for every run) is in **[experiments/](experiments/README.md)**.

## Method

| Stage | What | Where |
|---|---|---|
| Synthetic data | 300 generated examples for explanation, risk classification (Healthy / Moderate / High Risk) and report generation, rule-based labels | `src/finexpert/data/`, `data/sft/` |
| Real-report data | FinQA and TAT-QA converted to the same chat format; FinQA programs re-executed (reproduces gold on all 8,281 examples), TAT-QA derivations re-checked; working first, `Answer:` last | `src/finexpert/data/external/`, `scripts/build_external_dataset.py` |
| Training mix | 300 FinQA + 500 TAT-QA (calculation-heavy, max 2 questions per document) + 240 synthetic, committed as an id list | `data/external/train_mix_v2_pilot.json` |
| Training | QLoRA (4-bit base, LoRA r 16 / alpha 16 on all projections), LR 2e-4, effective batch 8, loss on the answer only, Unsloth on a Kaggle T4 | `notebooks/finexpert_v2_train.ipynb` |
| Self-distillation | The base model answers the training questions; answers verified correct by the scorers become reasoning targets (490/800 accepted) | `src/finexpert/data/distill.py` |
| Evaluation | Deterministic scorers (figure grounding, numeric claims, labels, sections); FinQA answer accuracy; TAT-QA's official EM/F1 scorer; strict and lenient answer extraction | `src/finexpert/evaluation/` |
| Statistics | Wilson and bootstrap 95% CIs; paired McNemar exact tests | `src/finexpert/evaluation/compare.py`, `scripts/compare_runs.py` |

## Reproduce

```bash
uv sync                                   # Python 3.12+, installs dev dependencies (pytest, pandas)
git clone https://github.com/czyssrs/FinQA.git data/external/raw/FinQA
git clone https://github.com/NExTplusplus/TAT-QA.git data/external/raw/TAT-QA
uv run python scripts/build_external_dataset.py   # byte-identical to data/external/audit.json
uv run pytest

# Score any predictions file on the fixed validation subset
uv run python scripts/evaluate_qa.py --predictions experiments/v2-pilot/finetuned_qa_predictions.jsonl \
    --split validation --subset data/external/eval_subset_v1.json

# Paired comparison of two runs
uv run python scripts/compare_runs.py --a experiments/base-zero-shot-rules/base_zero_shot_rules_qa_report.json \
    --b experiments/v2-pilot/finetuned_qa_report.json
```

GPU runs use `notebooks/finexpert_v2_train.ipynb` on Kaggle or Colab (T4). Set `RUN_MODE` to `train`, `baseline`, `distill` or `test`; each run writes predictions, reports and a manifest with the exact configuration, package versions and timings.

## Demo

`demo/` is a Gradio app for a free CPU Hugging Face Space: the v3 adapter merged into the base model and converted to a 4-bit GGUF
(`notebooks/finexpert_export_gguf.ipynb`), run with llama.cpp. The export notebook also measures how far the GGUF's answers drift
from the evaluated adapter on 40 fixed validation questions. A test (`tests/test_demo_prompts.py`) checks that the demo's prompts
are byte-identical to the training prompts for both tasks.

## Limitations

- **Model comparisons use the validation subset**; only the selected model was scored on the official test sets (once).
- **Small groups:** classification uses 10 test examples; the 3+ step FinQA group has 27 questions.
- **Two seeds per recipe**, one training-mix size (1,040 examples), one base model; the 3+ step finding rests on 27 questions.
- **Synthetic tasks use rule-based labels**, so classification measures agreement with those rules.
- **FinQA scoring checks final answers** (with rounding-aware tolerance), whereas published FinQA results usually score generated programs; numbers are not directly comparable.

## Next steps

- Reasoning-only distillation (several samples per question) to remove the answer-style mixture seen in v2-B.
- A larger training mix and a larger labelled classification test set.
- Structured calculations executed by Python to remove arithmetic slips (a post-hoc version was tried and rejected; see [v2-pilot](experiments/v2-pilot/README.md)).

## Data and licences

- **FinQA**: Chen et al., *FinQA: A Dataset of Numerical Reasoning over Financial Data*, EMNLP 2021. Data CC BY 4.0.
- **TAT-QA**: Zhu et al., *TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance*, ACL 2021. Data CC BY 4.0. The official TAT-QA scorer is used unmodified from its repository.
- Base model: Qwen3-4B-Instruct-2507 (4-bit build by Unsloth).
