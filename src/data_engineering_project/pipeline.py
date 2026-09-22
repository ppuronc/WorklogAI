from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import PROCESSED_CSV_PATH, RAW_EXCEL_PATH


def ensure_sample_data(file_path: str | None = None) -> str:
    """Create a simple sample Excel file if the raw dataset does not exist."""
    source = Path(file_path) if file_path else RAW_EXCEL_PATH
    source.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        sample_df = pd.DataFrame(
            {
                "Order ID": [1, 2, 3],
                "Customer": ["Alice", "Bob", "Charlie"],
                "Amount": [120.5, 210.0, 95.25],
                "Status": ["active", "pending", "active"],
            }
        )
        sample_df.to_excel(source, index=False)
    return str(source)


def load_raw_data(file_path: str | None = None) -> pd.DataFrame:
    """Load raw Excel data."""
    source = ensure_sample_data(file_path)
    return pd.read_excel(source)


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize sample data."""
    cleaned = df.copy()
    cleaned.columns = [str(col).strip().lower().replace(" ", "_") for col in cleaned.columns]
    if "amount" in cleaned.columns:
        cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce").fillna(0)
    if "status" in cleaned.columns:
        cleaned["status"] = cleaned["status"].astype(str).str.strip().str.lower()
    return cleaned


def run_pipeline(file_path: str | None = None) -> pd.DataFrame:
    """Run the ETL pipeline and persist processed output."""
    df = load_raw_data(file_path)
    transformed = transform_data(df)
    PROCESSED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    transformed.to_csv(PROCESSED_CSV_PATH, index=False)
    return transformed
