"""The demo must send the model exactly the prompts it was trained on."""

import importlib.util
import json
from pathlib import Path

from finexpert.data.external.common import QA_INSTRUCTION, SYSTEM_PROMPT, build_record
from finexpert.evaluation.prompting import build_messages, to_chatml

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("demo_prompts", ROOT / "demo" / "prompts.py")
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)


def test_demo_constants_match_training():
    assert demo.SYSTEM_PROMPT == SYSTEM_PROMPT
    assert demo.QA_INSTRUCTION == QA_INSTRUCTION


def test_qa_prompt_is_byte_identical_to_training():
    record = build_record(example_id="x", source="finqa", source_id="x", split="test", difficulty="easy",
                          context="| ($m) | 2023 |\n|---|---|\n| Revenue | 1,250 |", question="What was revenue?",
                          target="Answer: 1250", gold={}, answer_type="arithmetic", flags={})
    assert demo.qa_prompt("| ($m) | 2023 |\n|---|---|\n| Revenue | 1,250 |", "What was revenue?") == \
        to_chatml(build_messages(record))


def test_classification_prompt_matches_every_training_example():
    rows = [json.loads(line) for line in (ROOT / "data" / "sft" / "train.jsonl").read_text().splitlines()]
    classification = [r for r in rows if r["category"] == "financial_classification"]
    assert len(classification) == 80
    for record in classification:
        user = record["messages"][1]["content"]
        figures = user.split("Financial data:\n", 1)[1]
        assert demo.classification_prompt(figures) == to_chatml(build_messages(record)), record["example_id"]


def test_answer_and_label_parsing():
    assert demo.final_answer("Calculation:\n210 ÷ 1250 = 0.168\nAnswer: 16.8%") == "16.8%"
    assert demo.final_answer("no answer here").startswith("(no")
    assert demo.final_label("Classification: Moderate Risk\nEvidence: ...") == "Moderate Risk"
