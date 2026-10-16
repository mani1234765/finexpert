---
title: FinExpert
emoji: 📊
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.25.0
python_version: "3.11"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Financial Q&A with a fine-tuned Qwen3-4B (QLoRA) on CPU
---

# FinExpert demo

Runs the FinExpert model (Qwen3-4B + QLoRA adapter, merged and converted to a 4-bit GGUF) on a free CPU.

- Model card and evaluation: https://huggingface.co/ManideepVarma003/finexpert-qwen3-4b-lora
- Code and experiment log: https://github.com/mani1234765/finexpert

Nothing is compiled: at startup the app downloads llama.cpp's prebuilt server (pinned, SHA-256 verified) and the model, which takes a few minutes on the first start.
