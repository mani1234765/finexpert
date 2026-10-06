"""Create a committed training-mix file.

    uv run python scripts/make_training_mix.py --name v2_pilot --finqa 300 --tatqa 500

Writes data/external/train_mix_<name>.json listing the exact FinQA / TAT-QA
training ids, the synthetic file used, and a validation-loss monitoring set
drawn from validation examples outside the evaluation subset.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.data.external.common import sha256_file  # noqa: E402
from finexpert.data.external.mix import TATQA_TYPE_SHARES, select_mix  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--finqa", type=int, required=True, help="FinQA training questions")
    parser.add_argument("--tatqa", type=int, required=True, help="TAT-QA training questions")
    parser.add_argument("--monitor", type=int, default=100, help="validation-loss questions per source")
    parser.add_argument("--seed", type=int, default=20261006)
    parser.add_argument("--data", type=Path, default=Path("data/external"))
    parser.add_argument("--synthetic", type=Path, default=Path("data/sft/train.jsonl"))
    parser.add_argument("--eval-subset", type=Path, default=Path("data/external/eval_subset_v1.json"))
    args = parser.parse_args()

    subset = json.loads(args.eval_subset.read_text(encoding="utf-8"))
    held_out = {i for source in subset["sources"].values() for i in source["example_ids"]}

    mix = {"name": args.name, "seed": args.seed,
           "rules": "max 2 questions per context; TAT-QA type shares "
                    f"{TATQA_TYPE_SHARES}; FinQA types proportional",
           "synthetic": {"path": str(args.synthetic), "sha256": sha256_file(args.synthetic),
                         "count": len(read_jsonl(args.synthetic))},
           "eval_subset": str(args.eval_subset), "sources": {}}
    for source, size, shares in (("finqa", args.finqa, None), ("tatqa", args.tatqa, TATQA_TYPE_SHARES)):
        train_path = args.data / source / "train.jsonl"
        val_path = args.data / source / "validation.jsonl"
        train = read_jsonl(train_path)
        train_ids = select_mix(train, size, args.seed, shares)
        monitor_pool = [r for r in read_jsonl(val_path) if r["example_id"] not in held_out]
        monitor_ids = select_mix(monitor_pool, args.monitor, args.seed + 1)
        by_id = {r["example_id"]: r for r in train}
        mix["sources"][source] = {
            "train_sha256": sha256_file(train_path), "validation_sha256": sha256_file(val_path),
            "train_answer_types": dict(sorted(Counter(by_id[i]["answer_type"] for i in train_ids).items())),
            "train_est_tokens": sum(by_id[i]["flags"]["est_tokens"] for i in train_ids),
            "train_ids": train_ids, "monitor_ids": monitor_ids,
        }
        print(f"{source}: {len(train_ids)} train {mix['sources'][source]['train_answer_types']} "
              f"| {len(monitor_ids)} monitor")
    out = args.data / f"train_mix_{args.name}.json"
    out.write_text(json.dumps(mix, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
