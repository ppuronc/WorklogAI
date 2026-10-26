from __future__ import annotations

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Registry configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

REGISTRY_PATH = (
    BASE_DIR
    / "data"
    / "secure"
    / "token_registry.csv"
)

REGISTRY_COLUMNS = [
    "enterprise_id",
    "employee_id",
    "employee_name",
    "token_number",
    "enterprise_token",
    "employee_token",
    "person_token",
]


# ---------------------------------------------------------
# Registry functions
# ---------------------------------------------------------

def load_registry() -> pd.DataFrame:
    """Load the persistent token registry or create an empty one."""

    if not REGISTRY_PATH.exists():
        return pd.DataFrame(columns=REGISTRY_COLUMNS)

    registry = pd.read_csv(
        REGISTRY_PATH,
        dtype={
            "enterprise_id": "string",
            "employee_id": "string",
            "employee_name": "string",
            "token_number": "Int64",
            "enterprise_token": "string",
            "employee_token": "string",
            "person_token": "string",
        },
    )

    missing_columns = set(REGISTRY_COLUMNS) - set(registry.columns)

    if missing_columns:
        raise ValueError(
            "Token registry is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    return registry[REGISTRY_COLUMNS]


def save_registry(registry: pd.DataFrame) -> None:
    """Save the token registry to its protected location."""

    REGISTRY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    registry.to_csv(
        REGISTRY_PATH,
        index=False,
    )


def normalize_identity_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize identity fields before matching them to the registry."""

    cleaned = df.copy()

    required_columns = [
        "enterprise_id",
        "employee_id",
        "employee_name",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in cleaned.columns
    ]

    if missing_columns:
        raise ValueError(
            "Input data is missing required columns: "
            + ", ".join(missing_columns)
        )

    for column in required_columns:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.strip()
        )

    invalid_enterprise_ids = (
        cleaned["enterprise_id"].isna()
        | cleaned["enterprise_id"].eq("")
    )

    if invalid_enterprise_ids.any():
        raise ValueError(
            "enterprise_id cannot be blank because it is "
            "the master tokenization key."
        )

    return cleaned


def update_registry(
    df: pd.DataFrame,
    registry: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reuse existing tokens and allocate sequential tokens
    to new enterprise IDs.
    """

    employees = (
        df[
            [
                "enterprise_id",
                "employee_id",
                "employee_name",
            ]
        ]
        .drop_duplicates()
    )

    # Detect conflicting identities inside the current input.
    conflicts = (
        employees
        .groupby("enterprise_id")
        .agg(
            employee_id_count=("employee_id", "nunique"),
            employee_name_count=("employee_name", "nunique"),
        )
        .reset_index()
    )

    conflicting_ids = conflicts.loc[
        (conflicts["employee_id_count"] > 1)
        | (conflicts["employee_name_count"] > 1),
        "enterprise_id",
    ].tolist()

    if conflicting_ids:
        raise ValueError(
            "The same enterprise_id is associated with multiple "
            "employee IDs or names: "
            + ", ".join(conflicting_ids)
        )

    employees = (
        employees
        .drop_duplicates(subset=["enterprise_id"])
        .sort_values("enterprise_id")
        .reset_index(drop=True)
    )

    existing_enterprise_ids = set(
        registry["enterprise_id"]
        .dropna()
        .astype(str)
    )

    if registry.empty:
        next_token_number = 1
    else:
        token_numbers = pd.to_numeric(
            registry["token_number"],
            errors="coerce",
        )

        maximum_token = token_numbers.max()

        next_token_number = (
            1
            if pd.isna(maximum_token)
            else int(maximum_token) + 1
        )

    new_rows = []

    for _, employee in employees.iterrows():

        enterprise_id = str(employee["enterprise_id"])

        if enterprise_id in existing_enterprise_ids:
            continue

        token_number = next_token_number

        new_rows.append(
            {
                "enterprise_id": enterprise_id,
                "employee_id": str(employee["employee_id"]),
                "employee_name": str(employee["employee_name"]),
                "token_number": token_number,
                "enterprise_token": (
                    f"ENT_{token_number:06d}"
                ),
                "employee_token": (
                    f"EMP_{token_number:06d}"
                ),
                "person_token": (
                    f"PERSON_{token_number:06d}"
                ),
            }
        )

        existing_enterprise_ids.add(enterprise_id)
        next_token_number += 1

    if new_rows:
        registry = pd.concat(
            [
                registry,
                pd.DataFrame(new_rows),
            ],
            ignore_index=True,
        )

    return registry[REGISTRY_COLUMNS]


# ---------------------------------------------------------
# Masking
# ---------------------------------------------------------

def mask_dataframe(
    df: pd.DataFrame,
    registry: pd.DataFrame,
) -> pd.DataFrame:
    """Mask employee identity fields using enterprise_id."""

    masked = df.copy()

    lookup = registry[
        [
            "enterprise_id",
            "enterprise_token",
            "employee_token",
            "person_token",
        ]
    ].copy()

    masked = masked.merge(
        lookup,
        on="enterprise_id",
        how="left",
        validate="many_to_one",
    )

    missing_tokens = masked["enterprise_token"].isna()

    if missing_tokens.any():
        missing_ids = (
            masked.loc[
                missing_tokens,
                "enterprise_id",
            ]
            .drop_duplicates()
            .astype(str)
            .tolist()
        )

        raise ValueError(
            "No registry token found for enterprise_id: "
            + ", ".join(missing_ids)
        )

    masked["enterprise_id"] = masked["enterprise_token"]
    masked["employee_id"] = masked["employee_token"]
    masked["employee_name"] = masked["person_token"]

    masked = masked.drop(
        columns=[
            "enterprise_token",
            "employee_token",
            "person_token",
        ]
    )

    return masked


# ---------------------------------------------------------
# Unmasking
# ---------------------------------------------------------

def unmask_text(
    text: str,
    registry: pd.DataFrame,
) -> str:
    """Restore identity tokens found inside an AI report."""

    replacements = {}

    for _, row in registry.iterrows():
        replacements[str(row["enterprise_token"])] = str(
            row["enterprise_id"]
        )

        replacements[str(row["employee_token"])] = str(
            row["employee_id"]
        )

        replacements[str(row["person_token"])] = str(
            row["employee_name"]
        )

    # Replace longer values first to reduce partial matches.
    for token in sorted(
        replacements,
        key=len,
        reverse=True,
    ):
        text = text.replace(
            token,
            replacements[token],
        )

    return text


# ---------------------------------------------------------
# Main masking entry point
# ---------------------------------------------------------

def prepare_masked_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normalize input, update the persistent registry,
    and return masked data plus the registry.
    """

    normalized = normalize_identity_columns(df)

    registry = load_registry()

    registry = update_registry(
        normalized,
        registry,
    )

    save_registry(registry)

    masked = mask_dataframe(
        normalized,
        registry,
    )

    return masked, registry