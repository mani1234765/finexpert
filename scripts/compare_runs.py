"""Paired comparison of two QA reports (same questions), with McNemar's exact test.

    uv run python scripts/compare_runs.py \
        --a experiments/base-zero-few-shot/base_zero_shot_qa_report.json --name-a "base zero-shot" \
        --b experiments/v2-pilot/finetuned_qa_report.json             --name-b "fine-tuned pilot"

Prints a markdown table ready to paste into an experiment README.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.evaluation.compare import compare_qa_reports, format_comparison  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--a", type=Path, required=True)
    parser.add_argument("--b", type=Path, required=True)
    parser.add_argument("--name-a", default="A")
    parser.add_argument("--name-b", default="B")
    args = parser.parse_args()
    report_a = json.loads(args.a.read_text(encoding="utf-8"))
    report_b = json.loads(args.b.read_text(encoding="utf-8"))
    rows = [compare_qa_reports(report_a, report_b, source) for source in ("finqa", "tatqa")]
    print(format_comparison(rows, args.name_a, args.name_b))


if __name__ == "__main__":
    main()
