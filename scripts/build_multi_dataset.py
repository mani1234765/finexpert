"""Build multi-question examples (2-4 questions about one document) from the converted FinQA / TAT-QA data.

    uv run python scripts/build_external_dataset.py   # first, if not built
    uv run python scripts/build_multi_dataset.py

Writes data/external/multi/{train,validation,test}.jsonl (rebuilt, not committed), plus the committed
data/external/multi/audit.json and eval_subset_multi_v1.json (fixed validation bundles for every experiment).
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.data.external.common import MAX_TRAIN_TOKENS, sha256_file, write_jsonl  # noqa: E402
from finexpert.data.external.multi import build_bundles  # noqa: E402

SEED = 20261016
EVAL_BUNDLES_PER_SOURCE = 75


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    data = Path("data/external")
    out = data / "multi"
    audit: dict = {"seed": SEED, "max_train_tokens_estimate": MAX_TRAIN_TOKENS, "splits": {}}
    validation_bundles: dict[str, list[dict]] = {}
    for split in ("train", "validation", "test"):
        bundles = []
        for source in ("finqa", "tatqa"):
            records = read_jsonl(data / source / f"{split}.jsonl")
            made = build_bundles(records, SEED, MAX_TRAIN_TOKENS if split == "train" else None)
            bundles += made
            if split == "validation":
                validation_bundles[source] = made
        write_jsonl(out / f"{split}.jsonl", bundles)
        audit["splits"][split] = {
            "bundles": len(bundles),
            "questions": sum(len(b["items"]) for b in bundles),
            "by_source": dict(Counter(b["source_type"] for b in bundles)),
            "by_size": dict(sorted(Counter(len(b["items"]) for b in bundles).items())),
            "sha256": sha256_file(out / f"{split}.jsonl"),
        }
        print(f"{split:10s} {audit['splits'][split]}")

    rng = random.Random(SEED)
    subset = {"version": 1, "split": "validation", "seed": SEED, "bundles_per_source": EVAL_BUNDLES_PER_SOURCE,
              "selection": "random bundles per source, est_tokens <= 2048", "sources": {}}
    for source, bundles in validation_bundles.items():
        eligible = sorted((b for b in bundles if b["flags"]["est_tokens"] <= MAX_TRAIN_TOKENS),
                          key=lambda b: b["example_id"])
        chosen = sorted(b["example_id"] for b in rng.sample(eligible, min(EVAL_BUNDLES_PER_SOURCE, len(eligible))))
        by_id = {b["example_id"]: b for b in bundles}
        subset["sources"][source] = {
            "bundle_ids": chosen,
            "questions": sum(len(by_id[i]["items"]) for i in chosen),
            "by_size": dict(sorted(Counter(len(by_id[i]["items"]) for i in chosen).items())),
        }
    (out / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    (out / "eval_subset_multi_v1.json").write_text(json.dumps(subset, indent=1) + "\n", encoding="utf-8")
    print("eval subset:", {s: (len(v["bundle_ids"]), v["questions"], v["by_size"]) for s, v in subset["sources"].items()})


if __name__ == "__main__":
    main()
