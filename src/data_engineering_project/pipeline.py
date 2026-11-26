
from __future__ import annotations

from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

WORKLOG_CSV_PATH = BASE_DIR / "data" / "raw" / "Worklog.csv"
CHARGECODES_CSV_PATH = BASE_DIR / "data" / "raw" / "StandardsChargeCodes.csv"

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


    worklog["enterprise_id"] = (
        worklog["enterprise_id"]
        .astype(str)
        .str.strip()
    )

    # Convert period
    worklog["period"] = pd.to_datetime(
        worklog["period"],
        errors="coerce"
                    
    )

    # Convert date
    worklog["date"] = pd.to_datetime(
        worklog["date"],
        errors="coerce"
                    
    )

    worklog["charge_code"] = (
        worklog["charge_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

                       
    worklog["charge_code_description"] = (
        worklog["charge_code_description"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    worklog["chargeability_status"] = (
        worklog["chargeability_status"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Convert hours to numeric.
    # Example: "abc" becomes NaN.
    worklog["hours"] = pd.to_numeric(
        worklog["hours"],
        errors="coerce"
    )

    worklog["tr_status"] = (
        worklog["tr_status"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    worklog["bal3"] = (
        worklog["bal3"]
        .astype(str)
        .str.strip()
        .str.upper()
    )     

    # -----------------------------------------------------
    # Clean ChargeCodes data
    # -----------------------------------------------------
#charge_code	charge_code_description	chargeability_status	isvalid	isstandard
    chargecodes["charge_code"] = (
        chargecodes["charge_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    chargecodes["charge_code_description"] =(
        chargecodes["charge_code_description"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    chargecodes["chargeability_status"] = (
        chargecodes["chargeability_status"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    chargecodes["isvalid"] = (
        chargecodes["isvalid"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("true")
    )

    chargecodes["isstandard"] = (
        chargecodes["isstandard"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("true")
    )

    worklog_chargecodes = worklog[
        [
        "charge_code",
        "charge_code_description",
        "chargeability_status",
        ]
    ].copy()
   
    # Add Additional columns to worklog_chargecodes
    worklog_chargecodes["isvalid"] = True
    worklog_chargecodes["isstandard"] = True

    # Concatenate worklog_chargecodes with chargecodes DataFrame
    worklog_chargecodes = pd.concat(
            [worklog_chargecodes, chargecodes],
            ignore_index=True
        )
    # create final wbs catalog
    worklog_chargecodes = (
            worklog_chargecodes
            .groupby([
                "charge_code",
                "charge_code_description",
                "chargeability_status",
                "isvalid",
                "isstandard"
            ])
            .size()
            .reset_index(name="Count")
        )   
    # -----------------------------------------------------
    # Merge Worklog with ChargeCodes
    # -----------------------------------------------------

    merged = worklog.merge(
        worklog_chargecodes,
        on="charge_code",
        how="left",
    )

    # -----------------------------------------------------
    # Validation rules
    # -----------------------------------------------------

    # Charge code must exist and be marked valid
    merged["valid_charge_code"] = (
        merged["isvalid"].fillna(False)
    )

    # Hours must be numeric and non-negative
    merged["valid_hours"] = (
        merged["hours"].notna()
        & (merged["hours"] >= 0)
    )

    # Date must successfully convert to a date
    merged["valid_work_date"] = (
        merged["date"].notna()
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
