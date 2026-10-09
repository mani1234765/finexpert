# base-zero-few-shot — untrained base model, prompted

**Purpose:** measure what the base model does *without* fine-tuning, on exactly the questions the fine-tuned pilot was scored on. Fine-tuning is only worth it if it beats a well-prompted base model.

## Setup
| Item | Value |
|---|---|
| Date / platform | 8–9 Oct 2026, Kaggle, 1× Tesla T4 |
| Notebook | `notebooks/finexpert_v2_train.ipynb`, `RUN_MODE = "baseline"` (repo commit `5f7ab4b`) |
| Model | `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit`, no adapters |
| Zero-shot prompt | Identical to the training prompt (system + question + "show your working, then `Answer:`") |
| Few-shot prompt | Same, preceded by worked examples as earlier chat turns: 2 per QA source (different documents), 1 per synthetic task, all from the training split (`run_manifest.json` lists the ids) |
| Fairness settings | 1,024-token answer budget (training format needs ~50), 8,192-token context, generation stops after a complete `Answer:` line, strict and lenient scoring |
| Evaluation | Same fixed 600 validation questions (`eval_subset_v1.json`) + 30 synthetic test examples as v2-pilot |

## Results
| Model | FinQA accuracy | TAT-QA EM / F1 | Synthetic classification | Synthetic numeric recall | Mean answer length | Eval time |
|---|---|---|---|---|---|---|
| Base, zero-shot | **65.0%** (95% CI 59.4–70.2) | 32.3% / 41.5% | 0/10 (no labels in required format) | 10.4% | 308 tokens | 159 min |
| Base, few-shot | 60.3% (54.7–65.7) | 32.7% / 43.9% | 5/10 | 18.2% | 162 tokens | 101 min |
| Fine-tuned pilot ([v2-pilot](../v2-pilot/)) | 59.7% (54.0–65.1) | **64.7% / 72.7%** | **8/10** | **94.8%** | **48 tokens** | **29 min** |

Lenient scores equal strict ones within 0.4 pts for both base variants (`Answer:` line rate 97% zero-shot, 99.5% few-shot), so the base model's gaps are not about finding its answer. Zero-shot hit the 1,024-token limit on 18 of 630 answers (3 for few-shot).

### Paired comparisons (same questions, McNemar's exact test)
Generated with `scripts/compare_runs.py`.

**Base zero-shot vs fine-tuned pilot**

| Source | n | base zero-shot | fine-tuned pilot | Difference | base zero-shot only right | fine-tuned pilot only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 65.0% | 59.7% | -5.3 pts | 47 | 31 | 0.0888 |
| tatqa | 300 | 32.3% | 64.7% | +32.3 pts | 31 | 128 | < 0.0001 |

**Base few-shot vs fine-tuned pilot**

| Source | n | base few-shot | fine-tuned pilot | Difference | base few-shot only right | fine-tuned pilot only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 60.3% | 59.7% | -0.7 pts | 42 | 40 | 0.9122 |
| tatqa | 300 | 32.7% | 64.7% | +32.0 pts | 27 | 123 | < 0.0001 |

**Base zero-shot vs base few-shot**

| Source | n | base zero-shot | base few-shot | Difference | base zero-shot only right | base few-shot only right | McNemar p |
|---|---|---|---|---|---|---|---|
| finqa | 300 | 65.0% | 60.3% | -4.7 pts | 28 | 14 | 0.0436 |
| tatqa | 300 | 32.3% | 32.7% | +0.3 pts | 12 | 13 | 1.0000 |

## Analysis
**TAT-QA: the fine-tuned model wins clearly, but much of the gap is answer conventions.** Of the base zero-shot model's 203 TAT-QA misses, 136 contain a number matching the gold value up to scale or small rounding (automatic check), in a form the official scorer rejects: no scale word (`-12.6` for `-12.6 million`), a bare number for a list of items, or last-digit rounding. Lists written with commas instead of `;` fail as well. The prompt never stated these conventions; fine-tuning taught them. Multi-span questions show it most: base 0%, fine-tuned 79%. The gain is real and useful (outputs that downstream code can consume), but it is not, on its own, evidence of better reasoning.

**FinQA: the pilot fine-tune does not beat the base model.** Fine-tuned 59.7% vs zero-shot 65.0% (p = 0.089, not significant) and vs few-shot 60.3% (p = 0.91). The difference sits in longer calculations:

| FinQA program steps (correct count) | 1 (n=170) | 2 (n=103) | 3+ (n=27) |
|---|---|---|---|
| Base zero-shot (~300 tokens of reasoning) | 68% (116) | 61% (63) | 59% (16) |
| Base few-shot (~160 tokens) | 66% (112) | 53% (55) | 52% (14) |
| Fine-tuned pilot (~48 tokens, terse) | 65% (111) | 60% (62) | 22% (6) |

The base model reasons in prose before answering and holds up on 3+ step questions; the fine-tuned model learned the terse template (`Calculation:` lines only) and collapses there. Few-shot examples, which also show the terse format, make the base model terser and significantly worse than zero-shot on FinQA (p = 0.044). Together this suggests the terse target format costs multi-step reasoning. The 3+ step group is small (n = 27), so this is a hypothesis to test, not a conclusion.

**Structured synthetic tasks need fine-tuning.** Zero-shot, the base model never produced a `Classification:` label (0/10) and recalled 10% of expected figures; few-shot reached 5/10 and 18%.

**Efficiency.** The fine-tuned model answers in about 1/6 of the tokens, so evaluation ran 5.5× faster (29 vs 159 min): lower cost and latency in use.

## Limitations
- The prompts did not state TAT-QA's answer conventions (scale words, `;` between items). A follow-up baseline with explicit format rules isolates reasoning from convention-learning.
- One seed for the fine-tuned pilot; validation subset only; 3+ step FinQA results rest on 27 questions.

## Decision
1. Run a format-rules baseline (explicit answer conventions in the prompt) before claiming the TAT-QA gain as reasoning.
2. Make v2-B (teacher-written reasoning as training targets) the central experiment: it tests whether reasoning-rich targets keep the fine-tuned model's format and efficiency while recovering multi-step FinQA.

## Files
`base_zero_shot_*`, `base_few_shot_*`: predictions and reports for QA and synthetic tests · `run_manifest.json`: settings, few-shot example ids, environment · `requirements-kaggle.txt`.
