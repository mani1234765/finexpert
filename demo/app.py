"""FinExpert demo: a Hugging Face Space running the fine-tuned model as a 4-bit GGUF on a free CPU."""

import os
import time
from functools import lru_cache

import gradio as gr
from huggingface_hub import hf_hub_download

from prompts import classification_prompt, final_answer, final_label, qa_prompt

GGUF_REPO = os.environ.get("GGUF_REPO", "ManideepVarma003/finexpert-qwen3-4b-gguf")
GGUF_FILE = os.environ.get("GGUF_FILE", "finexpert-qwen3-4b-Q4_K_M.gguf")
MODEL_PAGE = "https://huggingface.co/ManideepVarma003/finexpert-qwen3-4b-lora"
CODE_PAGE = "https://github.com/mani1234765/finexpert"


@lru_cache(maxsize=1)
def get_llm():
    from llama_cpp import Llama  # imported lazily so the UI module stays importable for tests

    path = hf_hub_download(repo_id=GGUF_REPO, filename=GGUF_FILE)
    return Llama(model_path=path, n_ctx=4096, n_threads=os.cpu_count() or 2, verbose=False)


def generate(prompt: str, max_tokens: int = 512):
    started = time.time()
    out = get_llm().create_completion(prompt, max_tokens=max_tokens, temperature=0.0, stop=["<|im_end|>"])
    text = out["choices"][0]["text"].strip()
    stats = f"{out['usage']['completion_tokens']} tokens in {time.time() - started:.1f} s (free CPU)"
    return text, stats


def run_qa(context: str, question: str):
    if not context.strip() or not question.strip():
        return "Please provide both a report excerpt and a question.", "", ""
    text, stats = generate(qa_prompt(context, question), max_tokens=384)
    return text, final_answer(text), stats


def run_classification(financial_data: str):
    if not financial_data.strip():
        return "Please provide the financial figures.", "", ""
    text, stats = generate(classification_prompt(financial_data), max_tokens=512)
    return text, final_label(text), stats


QA_EXAMPLES = [
    ["Excerpt from a company annual report:\n\n| ($ in millions) | 2023 | 2022 |\n|---|---|---|\n| Revenue | 1,250 | 1,100 |\n"
     "| Operating income | 210 | 176 |\n\nRevenue growth was driven by higher subscription volumes.",
     "What was the operating margin in 2023?"],
    ["Excerpt from a company annual report:\n\n| (in thousands) | 2021 | 2020 |\n|---|---|---|\n| Cash and equivalents | 48,300 | 61,900 |\n"
     "| Short-term investments | 12,450 | 9,800 |",
     "What was the percentage change in cash and equivalents from 2020 to 2021?"],
]
CLASSIFY_EXAMPLES = [
    ["Vertex Solutions reported revenue changing from ₹180 Cr to ₹207 Cr. Operating profit changed from ₹27 Cr to ₹33 Cr. "
     "Total debt changed from ₹90 Cr to ₹81 Cr."],
    ["Pioneer Industries reported debt of ₹420 Cr and revenue of ₹350 Cr. Cash changed from ₹60 Cr to ₹38 Cr."],
]

DESCRIPTION = f"""
**FinExpert** is Qwen3-4B fine-tuned with QLoRA to answer numerical questions about financial report excerpts and to classify
financial health from supplied figures. It shows its working, then gives the answer.

This demo runs a 4-bit GGUF conversion on a free 2-core CPU, so an answer takes roughly 10–60 seconds, and results can differ
slightly from the evaluated model ([model card]({MODEL_PAGE}) · [code and experiment log]({CODE_PAGE})).
Use only figures you provide; this is a portfolio demo, **not financial advice**.
"""

with gr.Blocks(title="FinExpert") as demo:
    gr.Markdown("# FinExpert: financial Q&A with a fine-tuned 4B model")
    gr.Markdown(DESCRIPTION)
    with gr.Tab("Ask about a report"):
        context = gr.Textbox(label="Report excerpt (table and/or text)", lines=10)
        question = gr.Textbox(label="Question")
        ask = gr.Button("Answer", variant="primary")
        qa_answer = gr.Textbox(label="Final answer")
        qa_working = gr.Textbox(label="Model output (working)", lines=10)
        qa_stats = gr.Markdown()
        gr.Examples(QA_EXAMPLES, inputs=[context, question])
        ask.click(run_qa, inputs=[context, question], outputs=[qa_working, qa_answer, qa_stats])
    with gr.Tab("Classify financial health"):
        figures = gr.Textbox(label="Financial figures (₹ Cr, as sentences)", lines=5)
        classify = gr.Button("Classify", variant="primary")
        label = gr.Textbox(label="Classification")
        cls_working = gr.Textbox(label="Model output (evidence)", lines=8)
        cls_stats = gr.Markdown()
        gr.Examples(CLASSIFY_EXAMPLES, inputs=[figures])
        classify.click(run_classification, inputs=[figures], outputs=[cls_working, label, cls_stats])

if __name__ == "__main__":
    demo.queue(max_size=8).launch()
