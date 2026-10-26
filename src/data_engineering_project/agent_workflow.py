from __future__ import annotations

import pandas as pd
from ollama import chat


# ---------------------------------------------------------
# Ollama configuration
# ---------------------------------------------------------

MODEL = "llama3.2:3b"


# ---------------------------------------------------------
# Ollama call
# ---------------------------------------------------------

def call_ollama(prompt: str) -> str:

    response = chat(
        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional worklog analyst. "
                    "Use only the supplied values. "
                    "Do not recalculate totals. "
                    "Do not invent information."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        options={
            "num_ctx": 2048,
            "temperature": 0.2,
        },
    )

    return response["message"]["content"]


# ---------------------------------------------------------
# Employee reporting
# ---------------------------------------------------------

def generate_employee_summary(
    employee: str,
    df_emp: pd.DataFrame,
) -> str:
    """Generate an AI worklog summary for one employee."""

    # -----------------------------------------------------
    # Calculate metrics using Pandas
    # -----------------------------------------------------

    total_hours = df_emp["hours_numeric"].sum()

    valid_hours = df_emp.loc[
        df_emp["record_valid"],
        "hours_numeric",
    ].sum()

    invalid_hours = df_emp.loc[
        ~df_emp["record_valid"],
        "hours_numeric",
    ].sum()

    valid_records = int(
        df_emp["record_valid"].sum()
    )

    invalid_records_count = int(
        (~df_emp["record_valid"]).sum()
    )


    # -----------------------------------------------------
    # Charge-code breakdown
    # -----------------------------------------------------

    breakdown = (
        df_emp
        .groupby(
            ["charge_code", "valid_charge_code"],
            dropna=False,
        )["hours_numeric"]
        .sum()
        .reset_index()
    )

    breakdown_lines = []

    for _, row in breakdown.iterrows():

        status = (
            "VALID"
            if row["valid_charge_code"]
            else "INVALID"
        )

        breakdown_lines.append(
            f"- {row['charge_code']}: "
            f"{row['hours_numeric']} hours "
            f"({status})"
        )

    breakdown_str = "\n".join(breakdown_lines)


    # -----------------------------------------------------
    # Invalid records
    # -----------------------------------------------------

    invalid_df = df_emp.loc[
        ~df_emp["record_valid"]
    ]

    if invalid_df.empty:

        issues_str = "No validation issues."

    else:

        issue_lines = []

        for _, row in invalid_df.iterrows():

            issue_lines.append(
                f"- Date: {row['work_date']}, "
                f"Project: {row['project']}, "
                f"Charge Code: {row['charge_code']}, "
                f"Hours: {row['hours']}, "
                f"Issue: {row['validation_message']}"
            )

        issues_str = "\n".join(issue_lines)


    # -----------------------------------------------------
    # Build LLM prompt
    # -----------------------------------------------------

    prompt = f"""
Prepare a concise management-ready worklog report.

Employee:
{employee}

Worklog metrics:
- Total numeric hours: {total_hours}
- Valid hours: {valid_hours}
- Invalid hours: {invalid_hours}
- Valid records: {valid_records}
- Invalid records: {invalid_records_count}

Charge code breakdown:
{breakdown_str}

Validation issues:
{issues_str}

Reporting instructions:

1. Provide a short overall worklog summary.
2. Report the supplied hour values exactly as provided.
3. Highlight validation issues.
4. Identify invalid charge codes when supplied.
5. Mention invalid hour entries when supplied.
6. Do not infer reasons for errors.
7. Do not invent missing information.
8. Do not recalculate the supplied metrics.
9. Keep the report concise and professional.
"""

    return call_ollama(prompt)


# ---------------------------------------------------------
# Generate reports for all employees
# ---------------------------------------------------------

def summarize_with_agents(
    df: pd.DataFrame,
) -> dict[str, str]:
    """Generate Ollama summaries for every employee."""

    summaries = {}

    for employee, df_emp in df.groupby(
        "employee_name"
    ):

        summaries[employee] = (
            generate_employee_summary(
                employee,
                df_emp,
            )
        )

    return summaries