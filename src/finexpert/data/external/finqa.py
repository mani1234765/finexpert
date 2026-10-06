"""Convert FinQA (Chen et al., EMNLP 2021; CC BY 4.0) to FinExpert chat records.

Gold answer = the executed reasoning program (`qa.exe_ans`), the quantity
FinQA's official execution-accuracy metric scores. About 10% of FinQA's
written answers (`qa.answer`) disagree with their own program beyond
rounding; those examples are flagged and excluded from training, but kept in
validation and test so results stay comparable to published numbers.

The executor below mirrors `code/evaluate/evaluate.py::eval_program` in the
FinQA repository, and every example records whether it reproduces `exe_ans`.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .common import build_record, fmt_num, markdown_table, numbers_agree

OPS = ("add", "subtract", "multiply", "divide", "exp", "greater",
       "table_max", "table_min", "table_sum", "table_average")
ARITHMETIC = {"add": "+", "subtract": "−", "multiply": "×", "divide": "÷", "exp": "^"}
TABLE_WORDS = {"table_max": "maximum", "table_min": "minimum",
               "table_sum": "sum", "table_average": "average"}

_STEP_RE = re.compile(
    r"(?P<op>" + "|".join(OPS) + r")\((?P<args>.*?)\)"
    r"(?=\s*,\s*(?:" + "|".join(OPS) + r")\(|\s*$)"
)


# ---------------------------------------------------------------- execution

def str_to_num(text: str) -> float | None:
    """FinQA's str_to_num: commas dropped, 'x%' -> x/100, const_k -> k, const_m1 -> -1."""
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        pass
    if "%" in text:
        try:
            return float(text.replace("%", "")) / 100.0
        except ValueError:
            return None
    if "const" in text:
        text = text.replace("const_", "")
        return -1.0 if text == "m1" else float(text)
    return None


def process_row(cells: list[str]) -> list[float] | None:
    """FinQA's process_row: '$' removed, text after '(' dropped, then str_to_num."""
    values = []
    for cell in cells:
        number = str_to_num(cell.replace("$", "").strip().split("(")[0].strip())
        if number is None:
            return None
        values.append(number)
    return values


def parse_program(program: str) -> list[tuple[str, str, str]]:
    """'divide(100, 100), divide(3.8, #0)' -> [(op, arg1, arg2), ...].

    arg2 never contains a comma (a number, '#k', 'const_k' or 'none'), so the
    split is on the last comma; table row names in arg1 may contain commas.
    """
    steps = []
    for match in _STEP_RE.finditer(program.strip()):
        arg1, _, arg2 = match.group("args").rpartition(",")
        steps.append((match.group("op"), arg1.strip(), arg2.strip()))
    return steps


def execute(steps: list[tuple[str, str, str]], table: list[list[str]]) -> tuple[list[Any], Any]:
    """Run a parsed program. Returns (per-step results, final result rounded to 5 dp)."""
    results: list[Any] = []

    def value(arg: str) -> float:
        if arg.startswith("#"):
            return results[int(arg[1:])]
        number = str_to_num(arg)
        if number is None:
            raise ValueError(f"bad argument {arg!r}")
        return number

    rows = {row[0]: row[1:] for row in table}
    for op, arg1, arg2 in steps:
        if op in ARITHMETIC or op == "greater":
            a, b = value(arg1), value(arg2)
            result = {
                "add": lambda: a + b, "subtract": lambda: a - b, "multiply": lambda: a * b,
                "divide": lambda: a / b, "exp": lambda: a ** b,
                "greater": lambda: "yes" if a > b else "no",
            }[op]()
        else:
            if arg1 not in rows:
                raise ValueError(f"table row {arg1!r} not found")
            numbers = process_row(rows[arg1])
            if numbers is None:
                raise ValueError(f"table row {arg1!r} is not numeric")
            result = {
                "table_max": max, "table_min": min, "table_sum": sum,
                "table_average": lambda xs: sum(xs) / len(xs),
            }[op](numbers)
        results.append(result)
    final = results[-1]
    return results, (final if isinstance(final, str) else round(final, 5))


# ------------------------------------------------------------- rendering

def _arg_text(arg: str, results: list[Any]) -> str:
    if arg.startswith("#"):
        return fmt_num(results[int(arg[1:])])
    if arg.startswith("const_"):
        return "-1" if arg == "const_m1" else arg.replace("const_", "")
    return arg.replace(",", "")


def render_steps(steps: list[tuple[str, str, str]], results: list[Any]) -> list[str]:
    lines = []
    for index, ((op, arg1, arg2), result) in enumerate(zip(steps, results), 1):
        if op in ARITHMETIC:
            line = f"{_arg_text(arg1, results)} {ARITHMETIC[op]} {_arg_text(arg2, results)} = {fmt_num(result)}"
        elif op == "greater":
            line = f"Is {_arg_text(arg1, results)} greater than {_arg_text(arg2, results)}? {result}"
        else:
            line = f"{TABLE_WORDS[op].capitalize()} of the \"{arg1}\" row = {fmt_num(result)}"
        lines.append(f"{index}. {line}")
    return lines


def answer_presentation(exe_ans: Any, written: str) -> tuple[str, bool, float | None]:
    """Decide how to state the gold answer.

    Returns (answer text, is_percent, value as stated). FinQA programs often
    produce a ratio (0.1446) for a question whose written answer is a percent
    ("14%"); the stated value is then multiplied by 100.
    """
    if isinstance(exe_ans, str):
        return exe_ans, False, None
    written_clean = written.replace(",", "").replace("$", "").strip()
    is_percent = written_clean.endswith("%")
    stated = float(exe_ans)
    if is_percent:
        try:
            written_value = float(written_clean.rstrip("%").strip())
            if abs(stated * 100 - written_value) < abs(stated - written_value):
                stated *= 100
        except ValueError:
            if abs(stated) <= 1:
                stated *= 100
    # Percentages to 2 dp; other values keep the same precision as the working (4 dp).
    # Small values keep at least 3 significant digits (-0.0345%, not -0.03%).
    decimals = 2 if is_percent else 4
    if stated != 0 and abs(stated) < 1:
        decimals = max(decimals, -math.floor(math.log10(abs(stated))) + 2)
    text = fmt_num(stated, decimals) + ("%" if is_percent else "")
    return text, is_percent, stated


def written_answer_consistent(exe_ans: Any, written: str) -> bool:
    """Does FinQA's written answer agree with its executed program (rounding allowed)?"""
    written = str(written).strip()
    if isinstance(exe_ans, str):
        return written.lower() == exe_ans
    cleaned = written.replace(",", "").replace("$", "").strip()
    try:
        reference = float(cleaned.rstrip("%").strip())
    except ValueError:
        return False
    candidates = [exe_ans * 100, exe_ans] if cleaned.endswith("%") else [exe_ans, exe_ans * 100, exe_ans / 100]
    return any(numbers_agree(c, reference, cleaned) for c in candidates)


def difficulty_from_steps(n_steps: int) -> str:
    return "easy" if n_steps <= 1 else ("medium" if n_steps == 2 else "hard")


# --------------------------------------------------------------- convert

def build_context(example: dict[str, Any]) -> str:
    ticker, year, page = (example["filename"].split("/") + ["", ""])[:3]
    page = page.replace(".pdf", "").replace("page_", "page ")
    def text(parts: list[str]) -> str:
        return " ".join(p.strip() for p in parts if p.strip() and p.strip() != ".")
    blocks = [f"Excerpt from the {year} annual report of {ticker} ({page}):",
              text(example["pre_text"]), markdown_table(example["table_ori"]), text(example["post_text"])]
    return "\n\n".join(b for b in blocks if b)


def convert_example(example: dict[str, Any], split: str, index: int) -> dict[str, Any]:
    qa = example["qa"]
    steps = parse_program(qa["program"])
    flags: dict[str, Any] = {}
    try:
        results, executed = execute(steps, example["table"])
        flags["executor_matches_gold"] = (
            executed == qa["exe_ans"] if isinstance(executed, str) or isinstance(qa["exe_ans"], str)
            else abs(executed - float(qa["exe_ans"])) <= 1e-4 * max(1.0, abs(float(qa["exe_ans"])))
        )
    except Exception as error:  # noqa: BLE001 - recorded as a flag, never silently used
        results, executed = [], None
        flags["executor_matches_gold"] = False
        flags["executor_error"] = str(error)

    flags["written_answer_consistent"] = written_answer_consistent(qa["exe_ans"], qa["answer"])
    answer_text, is_percent, stated = answer_presentation(qa["exe_ans"], str(qa["answer"]))

    lines = ["Calculation:"] + render_steps(steps, results) if results else ["Calculation:"]
    if is_percent and stated is not None and not isinstance(qa["exe_ans"], str) and abs(stated - float(qa["exe_ans"])) > 1e-9:
        lines.append(f"As a percentage: {fmt_num(float(qa['exe_ans']))} × 100 = {answer_text}")
    lines.append(f"Answer: {answer_text}")

    return build_record(
        example_id=f"finqa_{split}_{index:05d}",
        source="finqa",
        source_id=example["id"],
        split=split,
        difficulty=difficulty_from_steps(len(steps)),
        context=build_context(example),
        question=qa["question"],
        target="\n".join(lines),
        gold={"value": qa["exe_ans"], "is_percent": is_percent, "stated": stated,
              "answer_text": answer_text, "written_answer": str(qa["answer"]), "program": qa["program"]},
        answer_type="yes_no" if isinstance(qa["exe_ans"], str) else "arithmetic",
        flags={**flags, "n_steps": len(steps)},
    )


def load_split(finqa_dir: Path, split: str) -> list[dict[str, Any]]:
    filename = {"train": "train.json", "validation": "dev.json", "test": "test.json"}[split]
    return json.loads((finqa_dir / "dataset" / filename).read_text(encoding="utf-8"))


def convert_split(finqa_dir: Path, split: str) -> list[dict[str, Any]]:
    return [convert_example(example, split, i) for i, example in enumerate(load_split(finqa_dir, split))]
