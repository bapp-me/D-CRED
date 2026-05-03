from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

LENDING_CLUB_URL = (
    "https://zenodo.org/records/11295916/files/"
    "LC_loans_granting_model_dataset.csv?download=1"
)
LENDING_CLUB_FILENAME = "LC_loans_granting_model_dataset.csv"
LENDING_CLUB_MD5 = "b019384d6bc65bf2a3e839362e4ff502"

UCI_DEFAULT_URL = (
    "https://archive.ics.uci.edu/static/public/350/"
    "default+of+credit+card+clients.zip"
)
UCI_DEFAULT_ZIP = "default_credit_card_clients.zip"

GERMAN_CREDIT_URL = (
    "https://archive.ics.uci.edu/static/public/144/"
    "statlog+german+credit+data.zip"
)
GERMAN_CREDIT_ZIP = "statlog_german_credit_data.zip"

DEFAULT_COST_RATIOS = (2.0, 5.0, 10.0)
DEFAULT_LGDS = (0.4, 0.6, 0.8)
DEFAULT_ROIS = (0.05, 0.10, 0.15)
DEFAULT_ALPHAS = (0.05, 0.10, 0.20)
