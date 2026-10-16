"""FinExpert demo: a Hugging Face Space running the fine-tuned model as a 4-bit GGUF on a free CPU.

Nothing is compiled at build time: at startup the app downloads llama.cpp's prebuilt Linux server (pinned release,
SHA-256 verified before it is run) and the GGUF model, starts the server on localhost, and sends it prompts built
exactly as in training.
"""

import hashlib
import json
import os
import subprocess
import tarfile
import threading
import time
import urllib.request

import gradio as gr
from huggingface_hub import hf_hub_download

from prompts import classification_prompt, final_answer, final_label, qa_prompt

GGUF_REPO = os.environ.get("GGUF_REPO", "ManideepVarma003/finexpert-qwen3-4b-gguf")
GGUF_FILE = os.environ.get("GGUF_FILE", "finexpert-qwen3-4b-Q4_K_M.gguf")
LLAMA_TAG = "b11237"   # llama.cpp release of 28 Sep 2026
LLAMA_URL = f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_TAG}/llama-{LLAMA_TAG}-bin-ubuntu-x64.tar.gz"
LLAMA_SHA256 = "109cd87ab22542488e99964c59b92c33e5562a7db9a4e260942749aebe9fa12b"
SERVER = "http://127.0.0.1:8080"
MODEL_PAGE = "https://huggingface.co/ManideepVarma003/finexpert-qwen3-4b-lora"
CODE_PAGE = "https://github.com/mani1234765/finexpert"

_state = {"ready": False, "error": None}

# ZeroGPU hardware refuses to start a Space without at least one @spaces.GPU function. This demo runs on CPU through
# llama.cpp, so the function below is only a marker and is never called. On CPU hardware `spaces` may be absent.
try:
    import spaces

    @spaces.GPU
    def _zerogpu_marker():
        return None
except ImportError:
    pass


def install_llama_server(dest: str = "/tmp/llama") -> str:
    """Download the pinned llama.cpp release, verify its checksum, unpack it, return the server path."""
    archive = os.path.join(dest, "llama.tar.gz")
    os.makedirs(dest, exist_ok=True)
    if not os.path.exists(archive):
        urllib.request.urlretrieve(LLAMA_URL, archive)
    digest = hashlib.sha256(open(archive, "rb").read()).hexdigest()
    if digest != LLAMA_SHA256:
        os.remove(archive)
        raise RuntimeError(f"llama.cpp download checksum mismatch: {digest}")
    with tarfile.open(archive) as tar:
        try:
            tar.extractall(dest, filter="data")  # safe extraction (Python 3.10.12+ / 3.11.4+)
        except TypeError:
            tar.extractall(dest)  # older Python: archive is already checksum-verified
    server = next(os.path.join(root, f) for root, _, files in os.walk(dest) for f in files if f == "llama-server")
    os.chmod(server, 0o755)
    return server


def _get(path: str, timeout: float = 5):
    with urllib.request.urlopen(SERVER + path, timeout=timeout) as response:
        return response.status, json.loads(response.read() or b"{}")


def start_backend() -> None:
    """Download everything and start llama-server; runs in a background thread so the UI comes up immediately."""
    try:
        server = install_llama_server()
        model = hf_hub_download(repo_id=GGUF_REPO, filename=GGUF_FILE)
        env = {**os.environ, "LD_LIBRARY_PATH": os.path.dirname(server)}
        subprocess.Popen([server, "-m", model, "--host", "127.0.0.1", "--port", "8080",
                          "-c", "4096", "-np", "1", "-t", str(os.cpu_count() or 2)], env=env)
        for _ in range(600):  # up to 10 minutes for the model to load
            try:
                if _get("/health")[0] == 200:
                    _state["ready"] = True
                    return
            except OSError:
                pass
            time.sleep(1)
        raise RuntimeError("llama-server did not become ready within 10 minutes")
    except Exception as error:  # surfaced in the UI instead of failing silently
        _state["error"] = f"{type(error).__name__}: {error}"


def generate(prompt: str, max_tokens: int):
    if _state["error"]:
        raise gr.Error(f"Model failed to start: {_state['error']}")
    if not _state["ready"]:
        raise gr.Error("The model is still loading (first start takes a few minutes). Please try again shortly.")
    payload = {"prompt": prompt, "n_predict": max_tokens, "temperature": 0.0, "stop": ["<|im_end|>"],
               "cache_prompt": False}
    request = urllib.request.Request(SERVER + "/completion", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    started = time.time()
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read())
    text = result["content"].strip()
    return text, f"{result.get('tokens_predicted', '?')} tokens in {time.time() - started:.1f} s (free CPU)"


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


def status() -> str:
    if _state["error"]:
        return f"⚠️ Model failed to start: {_state['error']}"
    return "✅ Model ready" if _state["ready"] else "⏳ Loading the model (first start takes a few minutes)…"


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

This demo runs a 4-bit GGUF conversion with llama.cpp on a free 2-core CPU, so an answer takes roughly 10–60 seconds. The
conversion is accuracy-comparable to the evaluated model but not answer-identical (it matched 25 of 40 checked answers;
22 vs 24 correct). [Model card and evaluation]({MODEL_PAGE}) · [Code and experiment log]({CODE_PAGE}).
Use only figures you provide; this is a portfolio demo, **not financial advice**.
"""

with gr.Blocks(title="FinExpert") as demo:
    gr.Markdown("# FinExpert: financial Q&A with a fine-tuned 4B model")
    gr.Markdown(DESCRIPTION)
    model_status = gr.Markdown(status())
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
    gr.Timer(5).tick(status, outputs=model_status)

if __name__ == "__main__":
    threading.Thread(target=start_backend, daemon=True).start()
    demo.queue(max_size=8).launch()
