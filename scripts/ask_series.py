"""Ask FinExpert a series of questions about one example, one question at a time.

The model was trained on one question per prompt, so each question is sent as a separate, fresh request with the
full context, in exactly the training format. Requires Ollama with the `finexpert` model (see the README).

Input file: the context first, then a line containing only ---, then one question per line.

    uv run python scripts/ask_series.py my_example.txt
"""

import json
import sys
import urllib.request

INSTRUCTION = ('Answer the question using only the context above. Show your working first, then give the final '
               'answer on the last line in the form "Answer: <value>".')
OLLAMA = "http://localhost:11434/api/chat"


def ask(context: str, question: str, model: str = "finexpert") -> str:
    user = f"{context.strip()}\n\nQuestion: {question.strip()}\n\n{INSTRUCTION}"
    body = {"model": model, "messages": [{"role": "user", "content": user}], "stream": False,
            "options": {"temperature": 0}}
    request = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read())["message"]["content"].strip()


def parse(text: str) -> tuple[str, list[str]]:
    if "\n---\n" not in f"\n{text}\n":
        sys.exit("Put a line containing only --- between the context and the questions.")
    context, questions = f"\n{text}\n".split("\n---\n", 1)
    return context.strip(), [q.strip() for q in questions.splitlines() if q.strip()]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    context, questions = parse(open(sys.argv[1], encoding="utf-8").read())
    for number, question in enumerate(questions, 1):
        print(f"\n=== Q{number}: {question}")
        try:
            print(ask(context, question))
        except OSError as error:
            sys.exit(f"Could not reach Ollama at {OLLAMA} ({error}). Is the Ollama app running?")


if __name__ == "__main__":
    main()
