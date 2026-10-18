"""Build the v4 prompt sets (no GPU): concept explanations, analysis-based assessments, and the red-team set.

    uv run python scripts/build_v4_prompts.py

Writes data/v4/*.jsonl (committed). Targets are added later by the teacher-generation run, which keeps only
targets that pass the automatic checks.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.data.external.common import SYSTEM_PROMPT, write_jsonl  # noqa: E402
from finexpert.data.v4.concepts import QUESTION_TEMPLATES, concept_records  # noqa: E402
from finexpert.data.v4.figures import compute_facts, parse_figures  # noqa: E402
from finexpert.data.v4.teacher import (  # noqa: E402
    ASSESSMENT_QUESTIONS_TRAIN, REDTEAM_QUESTIONS, assessment_user, teacher_explanation_prompt,
    teacher_suggestions_prompt,
)

SEED = 20261018
OUT = Path("data/v4")


def scenarios(split: str) -> list[tuple[str, str]]:
    """(example_id, financial data) for unique synthetic scenarios of a split."""
    seen, rows = set(), []
    for line in Path(f"data/sft/{split}.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        data = record["messages"][1]["content"].split("Financial data:")[1].strip()
        if data not in seen:
            seen.add(data)
            rows.append((record["example_id"], data))
    return rows


def main() -> None:
    rng = random.Random(SEED)
    summary = {}

    explain = {"train": [], "validation": [], "test": []}
    for concept in concept_records():
        templates = rng.sample(QUESTION_TEMPLATES, 2 if concept["split"] == "train" else 1)
        for template in templates:
            explain[concept["split"]].append({
                **concept, "id": f"explain_{concept['split']}_{len(explain[concept['split']]):04d}",
                "question": template.format(term=concept["term"]),
                "teacher_prompt": teacher_explanation_prompt(concept["term"], concept["has_formula"]),
                "system": SYSTEM_PROMPT,
            })
    for split, rows in explain.items():
        write_jsonl(OUT / f"explain_prompts_{split}.jsonl", rows)
    summary["explain"] = {k: len(v) for k, v in explain.items()}

    assess = {}
    for split in ("train", "validation"):
        rows = []
        for source_id, data in scenarios(split):
            facts = compute_facts(parse_figures(data))
            question = rng.choice(ASSESSMENT_QUESTIONS_TRAIN)
            rows.append({"id": f"assess_{split}_{len(rows):04d}", "source_id": source_id, "split": split,
                         "system": SYSTEM_PROMPT, "user": assessment_user(data, question), "facts": facts,
                         "teacher_prompt": teacher_suggestions_prompt(facts)})
        write_jsonl(OUT / f"assess_prompts_{split}.jsonl", rows)
        assess[split] = len(rows)
    summary["assess"] = assess

    redteam = []
    validation = scenarios("validation")
    for kind, question in REDTEAM_QUESTIONS:
        for source_id, data in rng.sample(validation, 5):
            redteam.append({"id": f"redteam_{len(redteam):03d}", "kind": kind, "source_id": source_id,
                            "system": SYSTEM_PROMPT, "user": assessment_user(data, question)})
    write_jsonl(OUT / "redteam.jsonl", redteam)
    summary["redteam"] = dict(Counter(r["kind"] for r in redteam))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
