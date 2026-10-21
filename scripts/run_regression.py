"""Run the regression set against a model and print a scorecard.

Against a running chat endpoint (OpenAI-compatible, e.g. Ollama or llama-server):
    uv run python scripts/run_regression.py --endpoint http://localhost:11434/v1 --model finexpert --out results.json

Or score saved outputs (JSONL with id and output), e.g. from the GPU notebook:
    uv run python scripts/run_regression.py --outputs outputs.jsonl

Every case is sent as a fresh, single-turn chat with greedy decoding, in the exact prompt format of the case.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.evaluation.regression import score_case  # noqa: E402

DIMENSIONS = ("final_correct", "formula_ok", "complete", "units_ok", "behaviour_ok", "no_leak")


def ask(endpoint: str, model: str, case: dict, max_tokens: int) -> str:
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": case["system"]}, {"role": "user", "content": case["user"]}]}
    request = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.loads(response.read())["choices"][0]["message"]["content"]


def scorecard(results: list[dict]) -> str:
    by_category: defaultdict[str, list[dict]] = defaultdict(list)
    for result in results:
        by_category[result["category"]].append(result)
    lines = ["| Category | Cases | Passed | " + " | ".join(DIMENSIONS) + " |", "|---|---|---|" + "---|" * len(DIMENSIONS)]
    for category, rows in sorted(by_category.items()):
        cells = []
        for dim in DIMENSIONS:
            scored = [r[dim] for r in rows if dim in r]
            cells.append(f"{sum(scored)}/{len(scored)}" if scored else "-")
        lines.append(f"| {category} | {len(rows)} | {sum(r['passed'] for r in rows)} | " + " | ".join(cells) + " |")
    total = sum(r["passed"] for r in results)
    lines.append(f"\n**Passed {total}/{len(results)}.** Failed: " +
                 (", ".join(r["id"] for r in results if not r["passed"]) or "none"))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", type=Path, default=Path("data/regression/cases_v1.jsonl"))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--endpoint")
    source.add_argument("--outputs", type=Path)
    parser.add_argument("--model", default="finexpert")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    cases = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.outputs:
        saved = {r["id"]: r["output"] for r in map(json.loads, args.outputs.read_text(encoding="utf-8").splitlines())}
        outputs = {c["id"]: saved.get(c["id"], "") for c in cases}
    else:
        outputs = {}
        for number, case in enumerate(cases, 1):
            print(f"[{number}/{len(cases)}] {case['id']}", file=sys.stderr)
            try:
                outputs[case["id"]] = ask(args.endpoint, args.model, case, args.max_tokens)
            except OSError as error:
                sys.exit(f"Could not reach {args.endpoint} ({error}). Is the server running?")
    results = [{**score_case(case, outputs[case["id"]]), "output": outputs[case["id"]]} for case in cases]
    print(scorecard(results))
    if args.out:
        args.out.write_text(json.dumps({"cases": str(args.cases), "model": args.model, "results": results},
                                       indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
