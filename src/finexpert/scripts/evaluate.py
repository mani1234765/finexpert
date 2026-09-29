#!/usr/bin/env python3
"""
Score a predictions file against a test split.

Decoupled from Colab/GPU on purpose: the notebook only needs to dump
{example_id: prediction} once, and this script (backed by
finexpert.evaluation, which has its own tests) does the scoring.
Run it again any time -- after retraining, after changing the
dataset, whenever -- without touching Colab.

Usage:
    python scripts/evaluate.py \
        --test data/splits/test.jsonl \
        --predictions predictions.jsonl \
        --out report.json

test.jsonl: the chat-format test split (system/user/assistant messages,
            example_id/category/difficulty), same shape used elsewhere
            in this repo.
predictions.jsonl: one {"example_id": ..., "prediction": ...} per line.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.evaluation.report import build_report, format_report  # noqa: E402


def load_test_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            by_role = {m["role"]: m["content"] for m in record["messages"]}
            rows.append(
                {
                    "example_id": record["example_id"],
                    "category": record["category"],
                    "difficulty": record["difficulty"],
                    "user": by_role["user"],
                    "assistant": by_role["assistant"],
                }
            )
    return rows


def load_predictions(path):
    predictions = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            predictions[record["example_id"]] = record["prediction"]
    return predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", required=True, help="path to test.jsonl")
    parser.add_argument("--predictions", required=True, help="path to predictions.jsonl")
    parser.add_argument("--out", default="report.json", help="where to write the full JSON report")
    args = parser.parse_args()

    rows = load_test_rows(args.test)
    predictions = load_predictions(args.predictions)

    report = build_report(rows, predictions)

    print(format_report(report))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nFull report written to {args.out}")


if __name__ == "__main__":
    main()
