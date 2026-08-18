import time
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

PAGES = [
    "https://pandas.pydata.org/docs/user_guide/indexing.html",
    "https://pandas.pydata.org/docs/user_guide/merging.html",
    "https://pandas.pydata.org/docs/user_guide/groupby.html",
    "https://pandas.pydata.org/docs/user_guide/missing_data.html",
    "https://pandas.pydata.org/docs/user_guide/reshaping.html",
]

PERSIST_DIR = "chroma_db"


def fetch_page(url):
    response = requests.get(url, headers={"User-Agent": "pandas-rag-learning-project"})
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else url

    main = soup.find(id="main-content") or soup.find("main") or soup.find("article")
    if main is None:
        raise ValueError(f"Could not find main content container for {url}")

    for tag in main.find_all(["nav", "button", "script", "style"]):
        tag.decompose()

    text = main.get_text(separator=" ", strip=True)
    return Document(page_content=text, metadata={"title": title, "url": url})


def main():
    print("Scraping pandas docs...")
    documents = []
    for url in PAGES:
        doc = fetch_page(url)
        documents.append(doc)
        print(f"  {doc.metadata['title']!r}: {len(doc.page_content)} characters")
        print(f"  preview: {doc.page_content[:200]}...\n")
        time.sleep(1)

    print("Chunking...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    print("Embedding + storing in Chroma...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=PERSIST_DIR)
    print(f"Done. Vector DB saved to ./{PERSIST_DIR}")


if __name__ == "__main__":
    main()