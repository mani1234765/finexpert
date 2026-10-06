"""Create the fixed validation subset used by every experiment.

    uv run python scripts/make_eval_subset.py            # writes data/external/eval_subset_v1.json

The file is committed. Never regenerate it with different settings under the
same name: results are only comparable on identical questions.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.data.external.common import sha256_file  # noqa: E402
from finexpert.data.external.subset import select_subset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/external"))
    parser.add_argument("--size", type=int, default=300, help="questions per source")
    parser.add_argument("--seed", type=int, default=20261006)
    parser.add_argument("--out", type=Path, default=Path("data/external/eval_subset_v1.json"))
    args = parser.parse_args()

    subset = {"version": 1, "split": "validation", "seed": args.seed, "size_per_source": args.size,
              "selection": "stratified by answer_type, min 20 per type, est_tokens <= 2048",
              "sources": {}}
    for source in ("finqa", "tatqa"):
        path = args.data / source / "validation.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        ids = select_subset(records, args.size, args.seed)
        by_id = {r["example_id"]: r for r in records}
        subset["sources"][source] = {
            "validation_sha256": sha256_file(path),
            "answer_types": dict(sorted(Counter(by_id[i]["answer_type"] for i in ids).items())),
            "difficulty": dict(sorted(Counter(by_id[i]["difficulty"] for i in ids).items())),
            "example_ids": ids,
        }
        print(f"{source}: {len(ids)} questions {subset['sources'][source]['answer_types']}")
    args.out.write_text(json.dumps(subset, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
