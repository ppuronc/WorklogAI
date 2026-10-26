from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_EXCEL_PATH = RAW_DATA_DIR / "sample_data.xlsx"
PROCESSED_CSV_PATH = PROCESSED_DATA_DIR / "processed_data.csv"
