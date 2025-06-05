from pathlib import Path

root = Path(__file__).resolve().parents[3]
processed_data = root/'data/processed'
models = root/'models'
reports = root/'reports'
figures = root/'reports/figures'