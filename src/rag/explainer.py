import json, sqlite3, datetime as dt
from functools import lru_cache
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceTextGenInference
from aura.rag.config import (                   
    chroma_store, embed_model, topn_shap, topk_docs,
    system_prompt, llm_endpoint, llm_model,
    max_tokens, temperature, log_db
)

embed = HuggingFaceEmbeddings(model_name=embed_model)
vs = Chroma(
              embedding_function=embed,
              persist_directory=str(chroma_store),
              collection_name="reg_chunks",
          )
retriever: VectorStoreRetriever= vs.as_retriever(k=topk_docs)

llm = HuggingFaceTextGenInference(
    inference_server_url=llm_endpoint,
    model_id=llm_model,
    max_new_tokens=max_tokens,
    temperature=temperature,
    timeout=45,
)

template = PromptTemplate.from_template(
"""\
{sys}

### Customer
{cust}

### Prediction
Probability_of_Default: {pd:.2%}

### Top SHAP Drivers
{drivers}

### Relevant Policy Excerpts
{ctx}

### Task
In ≤200 words, explain the decision, reference excerpts like [1], and end with a mitigation suggestion.\
""")

def driver_table(shap: Dict[str, float]) -> str:
    items = sorted(shap.items(), key=lambda kv: abs(kv[1]), reverse=True)[:topn_shap]
    return "\n".join(f"- {k}: {v:+.3f}" for k, v in items)

def policy_context(query_terms: List[str]) -> str:
    q = " ".join(query_terms)
    docs = retriever.get_relevant_documents(q)
    return "\n".join(
        f"[{i+1}] {d.page_content[:300]}... ({d.metadata['source']})"
        for i, d in enumerate(docs)
    )

def log(row) -> None:
    log_db.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(log_db)
    conn.execute("""CREATE TABLE IF NOT EXISTS rag_logs
                    (ts TEXT, cust TEXT, pd REAL, shap TEXT, expl TEXT)""")
    conn.execute("INSERT INTO rag_logs VALUES (?,?,?,?,?)", row)
    conn.commit(); conn.close()

def explain(customer: Dict[str, Any],
            pd: float,
            shap: Dict[str, float]) -> str:
    ctx = policy_context(list(shap)[:topn_shap])
    prompt = template.format(
        sys=system_prompt,
        cust=json.dumps(customer, default=str),
        pd=pd,
        drivers=driver_table(shap),
        ctx=ctx,
    )
    answer: str = llm.invoke(prompt)

    log((dt.datetime.utcnow().isoformat(),
        json.dumps(customer), pd,
        json.dumps(shap), answer))
    return answer