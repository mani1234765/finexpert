---
base_model: unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit
library_name: peft
license: apache-2.0
language: en
tags: [finance, qlora, lora, unsloth, finqa, tat-qa]
datasets: [FinQA, TAT-QA]
---

# FinExpert (Qwen3-4B, QLoRA adapter)

A LoRA adapter for **Qwen3-4B-Instruct-2507** that answers numerical questions over financial report excerpts (tables and text) and writes structured financial explanations, risk classifications and reports from supplied figures. Training code, data pipeline, evaluation and the full experiment log: <https://github.com/mani1234765/finexpert>. This is the exact adapter scored on the official test sets (run `v2-pilot-seed42`).

## Quick start
Requires a CUDA GPU (the base model is a 4-bit bitsandbytes build): `pip install transformers peft accelerate bitsandbytes`.

```python
import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

repo = "ManideepVarma003/finexpert-qwen3-4b-lora"
model = AutoPeftModelForCausalLM.from_pretrained(repo, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(repo)

SYSTEM = ("You are FinExpert, a specialized financial analysis assistant. Use only the financial information "
          "provided in the user input. Show relevant quantitative calculations when appropriate, distinguish "
          "reported facts from interpretation, and avoid inventing financial information or unsupported causal claims.")
INSTRUCTION = ('Answer the question using only the context above. Show your working first, then give the final '
               'answer on the last line in the form "Answer: <value>".')

context = "| ($ million) | 2023 | 2022 |\n|---|---|---|\n| Revenue | 1,250 | 1,100 |"
question = "What was the percentage change in revenue from 2022 to 2023?"

# Same ChatML layout as training (built by hand, no <think> block)
prompt = (f"<|im_start|>system\n{SYSTEM}<|im_end|>\n"
          f"<|im_start|>user\n{context}\n\nQuestion: {question}\n\n{INSTRUCTION}<|im_end|>\n"
          f"<|im_start|>assistant\n")
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=384, do_sample=False)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

## Intended use
- Answering questions about figures **given in the prompt** (a report excerpt or a list of metrics): changes, ratios, percentages, comparisons.
- Producing a short structured analysis of supplied metrics (explanation, risk classification, report).

**Not for:** investment advice, figures not present in the prompt, or any decision without human review. The model can miscalculate (see Limitations).

## How to prompt
Give the context, then the question, and ask for the working followed by a final line `Answer: <value>`; the training prompt format is reproduced exactly by `finexpert.evaluation.prompting` in the repository. Use greedy decoding.

## Training
| Item | Value |
|---|---|
| Base | `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit` (4-bit) |
| Method | QLoRA, r 16, alpha 16, dropout 0, all attention and MLP projections; loss on the answer only |
| Data | 300 FinQA + 500 TAT-QA training questions (audited; FinQA gold = executed program) + 240 synthetic examples |
| Recipe | 1 epoch, LR 2e-4, effective batch 8, linear schedule, warmup 5%, AdamW 8-bit, max length 2,048 |
| Hardware | 1× Tesla T4 (Kaggle), about 35 minutes |

## Evaluation
Validation subset (300 FinQA + 300 TAT-QA, never trained on):

| Model | FinQA accuracy | TAT-QA EM / F1 |
|---|---|---|
| Base model + answer-format rules (no training) | 63.3% | 61.3% / 67.2% |
| This adapter (v2-A, seed 42) | 60.0% | 66.0% / 73.8% |

Official test sets (scored once for this adapter):

| Test set | Result |
|---|---|
| FinQA (1,147 questions) | 62.0% answer accuracy (95% CI 59.1–64.8) |
| TAT-QA (1,663 questions, official scorer) | 62.1% EM / 70.2% F1 |

For reference on TAT-QA: TAGOP (the dataset paper's model) 50.1 / 58.0; GPT-4 zero-shot 71.9 / 79.7; human experts 84.1 / 90.8.

Selected among four fine-tuned runs by a rule registered before the final run (see the repository's experiment log). On these QA benchmarks the adapter matches a well-prompted base model (no significant difference) while answering in about 1/6 of the tokens; it also produces the structured synthetic-task outputs the base model cannot (classification 6–8/10 vs 0/10).

## Limitations
- Accuracy falls on multi-step calculations: 26% on 3+ step FinQA validation questions (a reasoning-trained variant reached 52–59% at about 4× the answer length). Arithmetic slips occur even when the right figures are chosen.
- Classification labels come from a rule-based scheme and were evaluated on only 10 examples.
- English, US-company reports (FinQA, TAT-QA) and synthetic ₹ Cr scenarios; not evaluated on other markets or formats.

## Citation of training data
- Chen et al., *FinQA: A Dataset of Numerical Reasoning over Financial Data*, EMNLP 2021 (CC BY 4.0).
- Zhu et al., *TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance*, ACL 2021 (CC BY 4.0).
