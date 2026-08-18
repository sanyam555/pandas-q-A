from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from sandbox import run_code_safely
from query import load_vectorstore, extract_code_block, SCHEMA_DESCRIPTION

FIX_PROMPT_TEMPLATE = """You are a pandas debugging assistant. A user's code failed with an error. Use ONLY the numbered context passages below (excerpts from official pandas documentation) to help fix it.

Rules:
1. Use only information and function names present in the context. Do not invent functions or parameters that aren't shown.
2. Briefly explain what was wrong, citing the passage number like [1].
3. Then provide a single corrected Python code block using the DataFrame `df` (already defined, don't redefine it). Always wrap your final result in print(...).
4. Be concise.

The data you're working with:
{schema}

Context passages:
{context}

Broken code:
{broken_code}

Error it produced:
{error_message}

Answer:"""

fix_prompt = PromptTemplate(
    template=FIX_PROMPT_TEMPLATE,
    input_variables=["context", "schema", "broken_code", "error_message"],
)


def fix_code(broken_code, k=5):
    first_attempt = run_code_safely(broken_code)

    if first_attempt["success"]:
        return {"already_worked": True, "execution_result": first_attempt}

    error_message = first_attempt["error"]

    search_query = f"{broken_code}\n{error_message}"
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(search_query)

    context = "\n\n".join(
        f"[{i+1}] (from \"{d.metadata['title']}\")\n{d.page_content}" for i, d in enumerate(docs)
    )

    final_prompt = fix_prompt.format(
        context=context, schema=SCHEMA_DESCRIPTION,
        broken_code=broken_code, error_message=error_message,
    )

    llm = OllamaLLM(model="llama3.2")
    answer = llm.invoke(final_prompt)

    fixed_code = extract_code_block(answer)
    fix_execution_result = run_code_safely(fixed_code) if fixed_code else None

    return {
        "already_worked": False,
        "original_error": error_message,
        "answer": answer,
        "docs": docs,
        "fixed_code": fixed_code,
        "fix_execution_result": fix_execution_result,
    }


if __name__ == "__main__":
    broken_code = "df.groupby('cty')['score'].mean()"  # typo: 'cty' instead of 'city'
    result = fix_code(broken_code)

    if result["already_worked"]:
        print("The code already worked, nothing to fix!")
    else:
        print("Original error:\n", result["original_error"])
        print("\nModel's explanation + fix:\n", result["answer"])
        print("\nFixed code:\n", result["fixed_code"])
        print("\nDid the fix actually work?")
        print("  success:", result["fix_execution_result"]["success"])
        print("  output:", result["fix_execution_result"]["output"])
        print("  error:", result["fix_execution_result"]["error"])