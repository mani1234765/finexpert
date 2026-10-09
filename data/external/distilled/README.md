# Distilled reasoning targets

Output of the notebook's `distill` mode (self-distillation / rejection sampling): the base model answers the training questions of a mix with the format-rules prompt; answers verified correct by the evaluation scorers (plus quality checks in `src/finexpert/data/distill.py`) become reasoning targets. One row per question: `accepted`, `rejection_reason`, the base model's raw answer and, if accepted, the new `target`.

These files are committed (an exception in `.gitignore`) because regenerating them costs hours of GPU time. Training uses them via `DISTILLED_TARGETS` in the notebook config.
