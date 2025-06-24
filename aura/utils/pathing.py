from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
data = root/"data"
processed_data = root/'data/processed'
reg_docs = data/'reg_docs'
chroma = root / 'chroma_store'
logs = root / "logs"    
models = root/'models'
reports = root/'reports'
figures = root/'reports/figures'