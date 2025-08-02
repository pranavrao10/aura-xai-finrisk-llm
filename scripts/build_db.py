import os
import json
import pathlib
import argparse
from typing import List, Dict, Iterator, Tuple
import chromadb
from chromadb.config import Settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pypdf import PdfReader
from openai import OpenAI, APIError, RateLimitError, APITimeoutError


ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_DIR = ROOT/"data"/"raw"/"reg_docs"      
DB_DIR = ROOT/"data"/"chroma_db"              
COLLECTION_NAME = os.getenv("chroma_collection_name", "regs_v1")

MAX_CHARS = 1800
OVERLAP = 150
BATCH_SIZE = 64
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

def read_pdf_iter(path: pathlib.Path) -> Iterator[str]:
    reader = PdfReader(str(path))
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        yield txt

def read_txt_iter(path: pathlib.Path) -> Iterator[str]:
    yield path.read_text(encoding="utf-8", errors="ignore")

def normalize(s: str) -> str:
    return " ".join(s.split())

def chunk_iter(text_iter: Iterator[str], max_chars: int, overlap: int) -> Iterator[str]:
    buf = ""
    for block in text_iter:
        buf += " " + normalize(block)
        while len(buf) >= max_chars:
            yield buf[:max_chars]
            buf = buf[max_chars - overlap:]
            if buf[0:1] == " ":
                buf = buf[1:]
    if buf.strip():
        yield buf.strip()

def scan_raw_docs(raw_dir: pathlib.Path) -> List[Dict]:
    idx_path = raw_dir / "index.json"
    if idx_path.exists():
        items = json.loads(idx_path.read_text())
    else:
        items = []
        for p in sorted(raw_dir.glob("*")):
            if p.suffix.lower() in (".pdf", ".txt"):
                items.append({
                    "id": p.stem,
                    "short": p.stem,
                    "path": str(p),
                    "url": "",
                    "type": p.suffix.lower().lstrip(".")
                })
    out = []
    for it in items:
        p = pathlib.Path(it["path"])
        if p.exists():
            out.append(it)
    return out

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=1, max=20),
    retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError, ConnectionError))
)
def embed_batch(texts: List[str]) -> List[List[float]]:
    client = OpenAI()
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def add_chunks_streaming(
    docs_meta: List[Dict],
    client: chromadb.PersistentClient,
    collection_name: str,
    batch_size: int,
    max_chars: int,
    overlap: int,
    limit_docs: int | None,
    limit_chunks: int | None,
    recreate: bool,
) -> Tuple[int, int]:
    if recreate:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    coll = client.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})

    total_chunks = 0
    total_docs = 0

    ids: List[str] = []
    docs: List[str] = []
    metas: List[Dict] = []

    def flush():
        nonlocal ids, docs, metas
        if not ids:
            return
        vecs = embed_batch(docs)
        coll.add(ids=ids, embeddings=vecs, documents=docs, metadatas=metas)
        ids.clear(); docs.clear(); metas.clear()

    for di, meta in enumerate(docs_meta):
        if limit_docs is not None and di >= limit_docs:
            break
        p = pathlib.Path(meta["path"])
        text_stream = read_pdf_iter(p) if meta["type"] == "pdf" else read_txt_iter(p)

        chunk_i = 0
        for chunk in chunk_iter(text_stream, max_chars=max_chars, overlap=overlap):
            cid = f"{meta['id']}::{chunk_i}"
            ids.append(cid)
            docs.append(chunk)
            metas.append({
                "doc_id": meta["id"],
                "short": meta.get("short", meta["id"]),
                "url": meta.get("url", ""),
                "chunk_index": chunk_i
            })
            chunk_i += 1
            total_chunks += 1

            if len(ids) >= batch_size:
                flush()

            if limit_chunks is not None and total_chunks >= limit_chunks:
                break

        total_docs += 1
        if limit_chunks is not None and total_chunks >= limit_chunks:
            break

    flush()
    return total_docs, total_chunks

def main():
    parser = argparse.ArgumentParser(description="Build Chroma DB (streaming, low-memory).")
    parser.add_argument("--raw-dir", default=str(RAW_DIR), help="folder with PDFs/TXTs or index.json")
    parser.add_argument("--db-dir",  default=str(DB_DIR),  help="Chroma persistence dir")
    parser.add_argument("--collection", default=COLLECTION_NAME, help="Chroma collection name")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--max-chars",  type=int, default=MAX_CHARS)
    parser.add_argument("--overlap",    type=int, default=OVERLAP)
    parser.add_argument("--limit-docs", type=int, default=None, help="debug: index only first N docs")
    parser.add_argument("--limit-chunks", type=int, default=None, help="debug: stop after N chunks")
    parser.add_argument("--no-recreate", action="store_true", help="do not delete collection first")
    args = parser.parse_args()

    raw_dir = pathlib.Path(args.raw_dir)
    db_dir = pathlib.Path(args.db_dir)
    db_dir.mkdir(parents=True, exist_ok=True)

    items = scan_raw_docs(raw_dir)
    if not items:
        print(f"No documents found in {raw_dir}. Aborting.")
        return

    client = chromadb.PersistentClient(path=str(db_dir), settings=Settings(anonymized_telemetry=False))

    recreate = not args.no_recreate
    docs_done, chunks_done = add_chunks_streaming(
        docs_meta=items,
        client=client,
        collection_name=args.collection,
        batch_size=args.batch_size,
        max_chars=args.max_chars,
        overlap=args.overlap,
        limit_docs=args.limit_docs,
        limit_chunks=args.limit_chunks,
        recreate=recreate,
    )

    print(f"Indexed docs: {docs_done}  •  chunks: {chunks_done}  ->  {db_dir}  (collection: {args.collection})")

if __name__ == "__main__":
    main()