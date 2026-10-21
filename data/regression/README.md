# Regression set

Every failure FinExpert has shown, frozen with a verified answer and run on every new model version **and** every
deployed format (GGUF), so improvements and regressions are measured on identical cases.

## Scoring dimensions (`src/finexpert/evaluation/regression.py`)

| Dimension | Fails when |
|---|---|
| `final_correct` | A requested value is missing or wrong |
| `formula_ok` | A required intermediate (e.g. NOPAT 350) is absent, or a known wrong-formula value (e.g. 441) appears |
| `complete` | Any requested part is missing |
| `units_ok` | A value appears in the wrong unit (0.15 where 15% was asked) |
| `behaviour_ok` | Missing data invented, advice rules broken, or wrong classification label |
| `no_leak` | A training artefact phrase appears in the answer |

## Case origins

| Origin | Meaning |
|---|---|
| `observed` | A failure recorded from a real run; the case stores the model, platform, date and verbatim output |
| `reconstructed` | Rebuilt to reproduce a reported failure whose exact prompt was not recorded |
| `designed` | A new probe for a known weakness |

Expected values are computed with `src/finexpert/finance/formulas.py`, never typed by hand, and
`tests/test_regression_suite.py` checks that a correct answer passes every case and that known wrong answers fail on
the right dimension.

## Adding an observed failure

Add a case in `scripts/build_regression_set.py` with `origin="observed"` and an `observed` block holding the model,
platform, date and the output **copied verbatim**, then rebuild (`uv run python scripts/build_regression_set.py`)
and add a correct answer for it in `tests/test_regression_suite.py`.

## Running

```bash
# against a running model (Ollama, llama-server or any OpenAI-compatible endpoint)
uv run python scripts/run_regression.py --endpoint http://localhost:11434/v1 --model finexpert --out results.json
# or score saved outputs (JSONL: {"id": ..., "output": ...})
uv run python scripts/run_regression.py --outputs outputs.jsonl
```
