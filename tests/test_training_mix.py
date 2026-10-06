"""Tests for training-mix selection."""

import json
from collections import Counter
from pathlib import Path

import pytest

from finexpert.data.external.mix import context_key, select_mix

ROOT = Path(__file__).resolve().parents[1]


def _records(n_contexts=300, per_context=6):
    types = ["arithmetic", "span", "multi-span", "count"]
    return [{"example_id": f"t{c:03d}_{q}", "source_type": "tatqa", "source_id": f"t{c:03d}_{q}",
             "answer_type": types[(c + q) % 4], "flags": {"table_uid": f"table{c:03d}"}}
            for c in range(n_contexts) for q in range(per_context)]


def test_at_most_two_questions_per_context():
    records = _records()
    by_id = {r["example_id"]: r for r in records}
    chosen = select_mix(records, 100, seed=1)
    assert max(Counter(context_key(by_id[i]) for i in chosen).values()) <= 2


def test_type_shares_are_followed_and_selection_is_deterministic():
    records = _records()
    by_id = {r["example_id"]: r for r in records}
    shares = {"arithmetic": 0.5, "span": 0.25, "multi-span": 0.15, "count": 0.10}
    chosen = select_mix(records, 100, seed=1, type_shares=shares)
    counts = Counter(by_id[i]["answer_type"] for i in chosen)
    assert counts == {"arithmetic": 50, "span": 25, "multi-span": 15, "count": 10}
    assert chosen == select_mix(records, 100, seed=1, type_shares=shares)


def test_short_type_is_topped_up_to_full_size():
    records = [r for r in _records() if r["answer_type"] != "count"]
    chosen = select_mix(records, 100, seed=1, type_shares={"arithmetic": 0.5, "count": 0.5})
    assert len(chosen) == 100 and len(set(chosen)) == 100


def test_finqa_context_is_the_report_page():
    record = {"source_type": "finqa", "source_id": "ABC/2015/page_10.pdf-3"}
    assert context_key(record) == "ABC/2015/page_10.pdf"


@pytest.mark.skipif(not (ROOT / "data/external/finqa/train.jsonl").exists(), reason="external data not built")
def test_committed_pilot_mix_matches_data_and_avoids_eval_subset():
    mix = json.loads((ROOT / "data/external/train_mix_v2_pilot.json").read_text())
    subset = json.loads((ROOT / "data/external/eval_subset_v1.json").read_text())
    held_out = {i for s in subset["sources"].values() for i in s["example_ids"]}
    for source, spec in mix["sources"].items():
        train_ids = {json.loads(l)["example_id"] for l in
                     (ROOT / "data/external" / source / "train.jsonl").read_text().splitlines()}
        assert set(spec["train_ids"]) <= train_ids
        assert not set(spec["monitor_ids"]) & held_out
