from pathlib import Path
import fitz
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from aura.rag.config import data, chroma_store, embed_model   



def pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    return "\n".join(p.get_text() for p in doc)

def main() -> None:
    data.mkdir(parents=True, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    embedder = HuggingFaceEmbeddings(model_name=embed_model)

    docs = []
    for fp in data.iterdir():
        text = pdf_text(fp) if fp.suffix.lower() == ".pdf" else fp.read_text()
        for chunk in splitter.split_text(text):
            docs.append({"page_content": chunk, "metadata": {"source": fp.name}})

    store = Chroma.from_documents(
        documents=docs,
        embedding=embedder,
        persist_directory=str(chroma_store),
        collection_name="reg_chunks",
    )
    store.persist()
    print(f"Indexed {len(docs):,} chunks ➜ {chroma_store}")

if __name__ == "__main__":
    main()