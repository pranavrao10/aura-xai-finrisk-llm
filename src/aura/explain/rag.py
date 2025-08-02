from __future__ import annotations
import os
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from openai import OpenAI

repo_root = Path(__file__).resolve().parents[3]
DEFAULT_LOCAL_DIR = str(repo_root / "data" / "chroma_db")
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "regs_v1")
DEFAULT_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", os.getenv("chroma_persist_dir", DEFAULT_LOCAL_DIR))
EMBED_MODEL = os.getenv("CHROMA_EMBED_MODEL", "text-embedding-3-small") 


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set; required for RAG query embeddings.")
    return OpenAI(api_key=api_key)


def _embed_texts(texts: List[str]) -> List[List[float]]:
    client = _openai_client()
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def get_reg_client() -> chromadb.PersistentClient:
    persist_dir = DEFAULT_PERSIST_DIR
    if not os.path.isdir(persist_dir):
        raise RuntimeError(
            f"Chroma persist directory not found: {persist_dir} "
            "(set CHROMA_PERSIST_DIR to the folder that contains your Chroma DB)."
        )
    return chromadb.PersistentClient(path=persist_dir, settings=Settings())


def get_reg_collection(client: Optional[chromadb.PersistentClient] = None):
    coll_name = DEFAULT_COLLECTION
    c = client or get_reg_client()
    try:
        return c.get_collection(coll_name)
    except Exception as e:
        raise RuntimeError(
            f"Chroma collection '{coll_name}' not found in '{DEFAULT_PERSIST_DIR}'. "
            "Did you build the DB (scripts/build_db.py) and do env vars point to the right folder?"
        ) from e


def search_regs(query: str, k: int = 4) -> List[Dict]:
    coll = get_reg_collection()
    vec = _embed_texts([query])[0]  
    res = coll.query(query_embeddings=[vec], n_results=k)

    out: List[Dict] = []
    docs = res.get("documents") or [[]]
    metas = res.get("metadatas") or [[]]
    if not docs or not docs[0]:
        return out

    for doc, meta in zip(docs[0], metas[0]):
        meta = meta or {}
        out.append({
            "text": doc or "",
            "short": meta.get("short", ""),
            "url": meta.get("url", ""),
            "doc_id": meta.get("doc_id", ""),
            "chunk_index": meta.get("chunk_index", 0),
        })
    return out


def format_citations(snippets: List[Dict]) -> str:
    lines = []
    for s in snippets:
        cite = s.get("short") or s.get("doc_id") or "unknown"
        link = f" ({s['url']})" if s.get("url") else ""
        body = s.get("text") or ""
        lines.append(f"[{cite}]{link}\n{body}\n")
    return "\n".join(lines)