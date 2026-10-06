"""Score FinQA / TAT-QA predictions.

    uv run python scripts/evaluate_qa.py --predictions preds.jsonl \
        --split validation --subset data/external/eval_subset_v1.json --out qa_report.json

Predictions: JSONL with {"example_id": ..., "prediction": ...} (the format the
training notebook writes). Missing predictions count as wrong. Use
--split test only for final evaluation of a finished model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.evaluation.qa.report import build_qa_report, format_qa_report  # noqa: E402


def load_records(data: Path, split: str, subset: Path | None) -> list[dict]:
    wanted = None
    if subset is not None:
        spec = json.loads(subset.read_text(encoding="utf-8"))
        if spec["split"] != split:
            sys.exit(f"Subset is for split {spec['split']!r}, not {split!r}")
        wanted = {i for source in spec["sources"].values() for i in source["example_ids"]}
    records = []
    for source in ("finqa", "tatqa"):
        path = data / source / f"{split}.jsonl"
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            records += [r for r in map(json.loads, filter(str.strip, lines))
                        if wanted is None or r["example_id"] in wanted]
    if wanted is not None and len(records) != len(wanted):
        sys.exit(f"Subset lists {len(wanted)} ids but only {len(records)} were found; rebuild the data?")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--subset", type=Path)
    parser.add_argument("--data", type=Path, default=Path("data/external"))
    parser.add_argument("--tatqa-dir", type=Path, default=Path("data/external/raw/TAT-QA"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    records = load_records(args.data, args.split, args.subset)
    predictions = {}
    for line in args.predictions.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            predictions[row["example_id"]] = row.get("prediction")
    report = build_qa_report(records, predictions, str(args.tatqa_dir))
    report["config"] = {"split": args.split, "subset": str(args.subset) if args.subset else None,
                        "predictions": str(args.predictions), "n_records": len(records)}
    print(format_qa_report(report))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
