import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings

DEFAULT_CHROMA_DIR = "/app/data/chroma_db"   
DEFAULT_COLLECTION = "regs_v1"

def getenv_dual(lower: str, upper: str, default: str) -> str:
    return os.getenv(lower) or os.getenv(upper) or default

def get_reg_client():
    persist = getenv_dual("chroma_persist_dir", "CHROMA_PERSIST_DIR", DEFAULT_CHROMA_DIR)
    return chromadb.PersistentClient(path=persist, settings=Settings())

def get_reg_collection(client=None):
    name = getenv_dual("chroma_collection_name", "CHROMA_COLLECTION_NAME", DEFAULT_COLLECTION)
    c = client or get_reg_client()
    try:
        return c.get_collection(name)
    except Exception as e:
        raise RuntimeError(
            f"Chroma collection '{name}' not found at '{getenv_dual('chroma_persist_dir','CHROMA_PERSIST_DIR', DEFAULT_CHROMA_DIR)}'. "
            "Ensure data/chroma_db is included in the image and env vars point to it."
        ) from e

def search_regs(query: str, k: int = 4) -> List[Dict]:
    coll = get_reg_collection()
    res = coll.query(query_texts=[query], n_results=k)
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