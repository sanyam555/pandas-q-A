# Pandas RAG Coding Assistant

A RAG-powered pandas coding assistant with execution-based verification — generated code isn't just displayed, it's actually run in a safety-checked sandbox to confirm it works, and "fixes" are verified the same way before being shown as correct.

## Pipeline
Scrape official pandas docs (indexing, merging, groupby, missing data, reshaping) → chunk → embed + store (Chroma) → retrieve → generate code (local Llama 3.2 via Ollama) → execute in a sandboxed subprocess → report pass/fail with real output.

## Features
- **Ask a question**: get an explanation + working code, grounded in real pandas docs, cited by passage.
- **Fix my code**: paste broken code, get the real captured error, a documented fix, and proof the fix actually runs.
- **Golden-answer evaluation** (`evaluate.py`): automated tests checked against known-correct values, not just "did it crash."

## Setup
1. `pip install -r requirements.txt`
2. Install [Ollama](https://ollama.com) and run `ollama pull llama3.2`
3. `python ingest_and_index.py` (scrapes docs, builds the vector DB)
4. `streamlit run app.py`

Note: this project requires Ollama running locally (`localhost:11434`) for generation — it isn't set up for cloud hosting out of the box, since local LLM inference needs it running on the same machine.

## Findings
- Execution success is not the same as correctness: a generated fix used `'min'` instead of `'mean'` in an aggregation, produced no error, and still passed a naive "did it crash" check. This motivated building golden-answer tests with known-correct expected values.
- Missing schema context caused hallucinated placeholder column names (e.g. `"column_to_group_by"`) even though the pandas API usage itself was correct — the model had no way to know real column names since we never told it.
- The model didn't reliably follow a "always print your result" instruction; fixed by deterministically post-processing generated code with Python's `ast` module to guarantee output visibility, rather than relying on the model remembering.
- The local model (Llama 3.2, 3B) is not fully consistent across repeated runs on identical input — the same broken code was fixed correctly in one run and incorrectly in another.