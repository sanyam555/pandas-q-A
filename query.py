from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from sandbox import run_code_safely, ensure_output_visible

PERSIST_DIR = "chroma_db"

SCHEMA_DESCRIPTION = """The DataFrame `df` has these columns:
- name (string): person's name
- age (integer): person's age
- city (string): city name
- score (float): a numeric score

Example rows:
   name    age city score
0  Alice   25  NYC  85.5
1  Bob     32  LA   92.1
"""

PROMPT_TEMPLATE = """You are a pandas coding assistant. Answer using ONLY the numbered context passages below, which are excerpts from the official pandas documentation.

Rules:
1. Use only information and function names present in the context. Do not invent functions or parameters that aren't shown.
2. Provide a short explanation, then a single Python code block using a DataFrame called `df` (already defined, don't redefine it).
3. End every explanatory sentence with the citation number for that fact, like this example:
"Use groupby() to split data into groups. [2] Then apply an aggregation like mean() to each group. [4]"
4. If the context doesn't contain enough information, say exactly: "Not found in the provided context."
5. Be concise.

Context passages:
The data you're working with:
{schema}

{context}

Question: {question}

Answer:"""

prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question","schema"])


def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)


def extract_code_block(answer_text):
    if "```" not in answer_text:
        return None
    parts = answer_text.split("```")
    code = parts[1]
    if code.startswith("python"):
        code = code[len("python"):]
    return code.strip()


def answer_question(query, k=5):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)

    context = "\n\n".join(
        f"[{i+1}] (from \"{d.metadata['title']}\")\n{d.page_content}" for i, d in enumerate(docs)
    )
    final_prompt = prompt.format(context=context, question=query, schema=SCHEMA_DESCRIPTION)

    llm = OllamaLLM(model="llama3.2")
    answer = llm.invoke(final_prompt)

    code = extract_code_block(answer)
    execution_result = run_code_safely(ensure_output_visible(code)) if code else None

    return {"answer": answer, "docs": docs, "code": code, "execution_result": execution_result}


if __name__ == "__main__":
    query = "How do I group a DataFrame by one column and compute the mean of another column?"
    result = answer_question(query)

    print("Answer:\n", result["answer"])
    print("\nExtracted code:\n", result["code"])
    if result["execution_result"]:
        print("\nExecution result:")
        print("  success:", result["execution_result"]["success"])
        print("  output:", result["execution_result"]["output"])
        print("  error:", result["execution_result"]["error"])