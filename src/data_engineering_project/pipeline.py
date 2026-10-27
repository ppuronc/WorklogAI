
from __future__ import annotations

from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

WORKLOG_CSV_PATH = BASE_DIR / "data" / "raw" / "Worklog.csv"
CHARGECODES_CSV_PATH = BASE_DIR / "data" / "raw" / "ChargeCodes.csv"

PROCESSED_CSV_PATH = (
    BASE_DIR / "data" / "processed" / "worklog_chargecode.csv"
)


# ---------------------------------------------------------
# Load raw data
# ---------------------------------------------------------

def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load Worklog and ChargeCodes CSV files."""

    if not WORKLOG_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Worklog file not found: {WORKLOG_CSV_PATH}"
        )

    if not CHARGECODES_CSV_PATH.exists():
        raise FileNotFoundError(
            f"ChargeCodes file not found: {CHARGECODES_CSV_PATH}"
        )

    worklog_df = pd.read_csv(WORKLOG_CSV_PATH)
    chargecodes_df = pd.read_csv(CHARGECODES_CSV_PATH)

    return worklog_df, chargecodes_df


# ---------------------------------------------------------
# Transform and validate data
# ---------------------------------------------------------

def transform_data(
    worklog_df: pd.DataFrame,
    chargecodes_df: pd.DataFrame,
) -> pd.DataFrame:
    """Clean Worklog data and validate it against ChargeCodes."""

    worklog = worklog_df.copy()
    chargecodes = chargecodes_df.copy()

    # Normalize column names
    worklog.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in worklog.columns
    ]

    chargecodes.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in chargecodes.columns
    ]

    # -----------------------------------------------------
    # Clean Worklog fields
    # -----------------------------------------------------

    worklog["employee_id"] = (
        worklog["employee_id"]
        .astype(str)
        .str.strip()
    )

    worklog["employee_name"] = (
        worklog["employee_name"]
        .astype(str)
        .str.strip()
    )

    worklog["project"] = (
        worklog["project"]
        .astype(str)
        .str.strip()
    )

    worklog["charge_code"] = (
        worklog["charge_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Convert work date
    worklog["work_date"] = pd.to_datetime(
        worklog["work_date"],
        errors="coerce"
    )

    # Convert hours to numeric.
    # Example: "abc" becomes NaN.
    worklog["hours_numeric"] = pd.to_numeric(
        worklog["hours"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Clean ChargeCodes data
    # -----------------------------------------------------

    chargecodes["charge_code"] = (
        chargecodes["charge_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    chargecodes["is_valid"] = (
        chargecodes["is_valid"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("true")
    )

    # -----------------------------------------------------
    # Merge Worklog with ChargeCodes
    # -----------------------------------------------------

    merged = worklog.merge(
        chargecodes,
        on="charge_code",
        how="left",
    )

    # -----------------------------------------------------
    # Validation rules
    # -----------------------------------------------------

    # Charge code must exist and be marked valid
    merged["valid_charge_code"] = (
        merged["is_valid"].fillna(False)
    )

    # Hours must be numeric and non-negative
    merged["valid_hours"] = (
        merged["hours_numeric"].notna()
        & (merged["hours_numeric"] >= 0)
    )

    # Date must successfully convert to a date
    merged["valid_work_date"] = (
        merged["work_date"].notna()
    )

    # Overall record validity
    merged["record_valid"] = (
        merged["valid_charge_code"]
        & merged["valid_hours"]
        & merged["valid_work_date"]
    )

    # -----------------------------------------------------
    # Validation message
    # -----------------------------------------------------

    def get_validation_message(row) -> str:

        issues = []

        if not row["valid_charge_code"]:
            issues.append("Invalid charge code")

        if not row["valid_hours"]:
            issues.append("Invalid hours")

        if not row["valid_work_date"]:
            issues.append("Invalid work date")

        if not issues:
            return "Valid record"

        return "; ".join(issues)

    merged["validation_message"] = merged.apply(
        get_validation_message,
        axis=1,
    )

    return merged


# ---------------------------------------------------------
# Run pipeline
# ---------------------------------------------------------

def run_pipeline() -> pd.DataFrame:
    """Run the Worklog ETL pipeline and save processed output."""

    print("Loading raw data...")

    worklog_df, chargecodes_df = load_raw_data()

    print(f"Worklog records loaded: {len(worklog_df)}")
    print(f"Charge codes loaded: {len(chargecodes_df)}")

    print("Transforming and validating data...")

    transformed = transform_data(
        worklog_df,
        chargecodes_df,
    )

    # Create output directory if it doesn't already exist
    PROCESSED_CSV_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    transformed.to_csv(
        PROCESSED_CSV_PATH,
        index=False,
    )

    print(f"Processed file created: {PROCESSED_CSV_PATH}")

    print(
        f"Valid records: "
        f"{transformed['record_valid'].sum()}"
    )

    print(
        f"Invalid records: "
        f"{(~transformed['record_valid']).sum()}"
    )

    return transformed
