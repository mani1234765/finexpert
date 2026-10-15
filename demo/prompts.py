"""Prompt construction for the demo, byte-identical to training.

Kept free of third-party imports so the repository's test suite can check it
against `finexpert.evaluation.prompting` without installing the demo's
dependencies.
"""

import re

SYSTEM_PROMPT = (
    "You are FinExpert, a specialized financial analysis assistant. Use only the financial information provided "
    "in the user input. Show relevant quantitative calculations when appropriate, distinguish reported facts from "
    "interpretation, and avoid inventing financial information or unsupported causal claims."
)
QA_INSTRUCTION = (
    'Answer the question using only the context above. Show your working first, then give the final answer on the '
    'last line in the form "Answer: <value>".'
)
CLASSIFY_INSTRUCTION = (
    "Classify the company's overall financial health as Healthy, Moderate Risk, or High Risk using only the provided "
    "financial figures. Show the key calculations and cite the evidence supporting the classification."
)


def chatml(user: str) -> str:
    """Qwen ChatML, built by hand exactly as in training (no <think> block)."""
    return (f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
            f"<|im_start|>user\n{user}<|im_end|>\n"
            f"<|im_start|>assistant\n")


def qa_prompt(context: str, question: str) -> str:
    return chatml(f"{context.strip()}\n\nQuestion: {question.strip()}\n\n{QA_INSTRUCTION}")


def classification_prompt(financial_data: str) -> str:
    return chatml(f"{CLASSIFY_INSTRUCTION}\n\nFinancial data:\n{financial_data.strip()}")


_ANSWER = re.compile(r"^\W*answer\W*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_LABEL = re.compile(r"^\W*classification\W*:\s*(Healthy|Moderate Risk|High Risk)\b", re.IGNORECASE | re.MULTILINE)


def final_answer(text: str) -> str:
    found = _ANSWER.findall(text)
    return found[-1] if found else "(no 'Answer:' line produced)"


def final_label(text: str) -> str:
    found = _LABEL.findall(text)
    return found[0] if found else "(no label produced)"
