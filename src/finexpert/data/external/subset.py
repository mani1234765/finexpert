"""Deterministic, stratified evaluation subsets.

Experiments iterate on a fixed subset of the official *validation* sets so
every model is scored on identical questions; official test sets are only
used for final evaluation.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any


def allocate(counts: dict[str, int], total: int, minimum: int) -> dict[str, int]:
    """Proportional allocation (largest remainder) with a per-group minimum."""
    total = min(total, sum(counts.values()))
    alloc = {k: min(c, minimum) for k, c in counts.items()}
    remaining = total - sum(alloc.values())
    if remaining <= 0:
        return alloc
    spare = {k: counts[k] - alloc[k] for k in counts}
    spare_total = sum(spare.values())
    shares = {k: remaining * spare[k] / spare_total for k in counts}
    extra = {k: min(int(shares[k]), spare[k]) for k in counts}
    leftover = remaining - sum(extra.values())
    for k in sorted(counts, key=lambda k: (shares[k] - int(shares[k]), k), reverse=True):
        if leftover <= 0:
            break
        if extra[k] < spare[k]:
            extra[k] += 1
            leftover -= 1
    return {k: alloc[k] + extra[k] for k in counts}


def select_subset(records: list[dict[str, Any]], size: int, seed: int,
                  minimum_per_type: int = 20, max_est_tokens: int | None = 2048) -> list[str]:
    """Stratify by answer_type; skip examples longer than the training limit."""
    pool: defaultdict[str, list[str]] = defaultdict(list)
    for record in records:
        if max_est_tokens is None or record["flags"]["est_tokens"] <= max_est_tokens:
            pool[record["answer_type"]].append(record["example_id"])
    counts = {k: len(v) for k, v in pool.items()}
    plan = allocate(counts, size, minimum_per_type)
    rng = random.Random(seed)
    chosen: list[str] = []
    for answer_type in sorted(plan):
        chosen += rng.sample(sorted(pool[answer_type]), plan[answer_type])
    return sorted(chosen)
