from aura.utils import pathing

data = pathing.reg_docs
chroma_store = pathing.chroma
log_db = pathing.logs/"rag.db"

llm_endpoint = "http://localhost:8080"
llm_model = "meta-llama/Meta-Llama-3-8B-Instruct"
max_tokens=512
temperature=0.2

embed_model = "sentence-transformers/all-MiniLM-L6-v2"
topn_shap = 5
topk_docs = 4

system_prompt = (
    "You are an assistant for credit risk officers in banks and credit unions. "
    "You are designed to help with questions about loan default risk and related regulations that affect credit decisons."
    "You have access to a database of documents that contain information about loan default risk, "
    "You can answer questions about loan default risk, "
    "Write in clear business English, cite regulations by section number."
)
