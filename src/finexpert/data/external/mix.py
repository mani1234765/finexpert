"""Deterministic training-mix selection.

A mix file (committed) fixes exactly which examples a run trains on, so
repeated seeds and the template-vs-teacher comparison use identical
questions. Selection rules:

* at most `max_per_context` questions per source context (a FinQA report page,
  a TAT-QA table) so the model sees many different documents;
* answer types sampled toward target shares (calculation-heavy for TAT-QA).
  The per-context cap is applied first; if a type then runs short, the mix
  is topped up from other types, so shares are targets, not guarantees
  (the committed mix files record the achieved counts);
* a separate monitoring set (validation loss only) drawn from validation
  examples that are NOT in the evaluation subset.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

TATQA_TYPE_SHARES = {"arithmetic": 0.50, "span": 0.25, "multi-span": 0.15, "count": 0.10}


def context_key(record: dict[str, Any]) -> str:
    if record["source_type"] == "finqa":
        return record["source_id"].rsplit("-", 1)[0]  # report page
    return record["flags"]["table_uid"]


def _cap_per_context(records: list[dict[str, Any]], rng: random.Random, cap: int) -> list[dict[str, Any]]:
    by_context: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in sorted(records, key=lambda r: r["example_id"]):
        by_context[context_key(record)].append(record)
    kept = []
    for key in sorted(by_context):
        group = by_context[key]
        kept += rng.sample(group, min(cap, len(group)))
    return kept


def select_mix(records: list[dict[str, Any]], size: int, seed: int,
               type_shares: dict[str, float] | None = None, max_per_context: int = 2) -> list[str]:
    """Pick `size` example ids, capped per context, steered toward type shares."""
    rng = random.Random(seed)
    pool = _cap_per_context(records, rng, max_per_context)
    by_type: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in pool:
        by_type[record["answer_type"]].append(record)
    if type_shares is None:  # proportional to what is available
        total = sum(len(v) for v in by_type.values())
        type_shares = {t: len(v) / total for t, v in by_type.items()}

    targets = {t: int(round(size * type_shares.get(t, 0.0))) for t in by_type}
    chosen: list[dict[str, Any]] = []
    for answer_type in sorted(by_type):
        candidates = sorted(by_type[answer_type], key=lambda r: r["example_id"])
        chosen += rng.sample(candidates, min(targets[answer_type], len(candidates)))
    if len(chosen) < size:  # a type ran short: top up from the rest, deterministically
        taken = {r["example_id"] for r in chosen}
        rest = sorted((r for r in pool if r["example_id"] not in taken), key=lambda r: r["example_id"])
        chosen += rng.sample(rest, min(size - len(chosen), len(rest)))
    return sorted(r["example_id"] for r in chosen[:size])
