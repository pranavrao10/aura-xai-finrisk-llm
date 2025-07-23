from __future__ import annotations
from pathlib import Path
import os

ROOT = Path(os.getenv("AURA_ROOT", Path(__file__).resolve().parents[3]))

DATA_DIR  = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REG_DOCS_DIR = DATA_DIR / "reg_docs"

CHROMA_DIR = ROOT / "chroma_store"
LOG_DIR = ROOT / "logs"
MODEL_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


root = ROOT
models = MODEL_DIR
reports = REPORTS_DIR