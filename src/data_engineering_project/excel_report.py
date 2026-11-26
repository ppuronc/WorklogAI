from __future__ import annotations

from pathlib import Path

import pandas as pd


def create_excel_report(
    processed_df: pd.DataFrame,
    summaries: dict[str, str],
    output_path: Path,
) -> Path:
    """
    Create a formatted WorklogAI Excel report.

    Sheets:
    1. Executive Summary
    2. Worklog Details
    3. Invalid Records
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    details_df = processed_df.copy()

    # Convert dates into a clean Excel-friendly format
    if "work_date" in details_df.columns:
        details_df["work_date"] = pd.to_datetime(
            details_df["work_date"],
            errors="coerce",
        ).dt.date

    # -----------------------------------------------------
    # Build employee summary table
    # -----------------------------------------------------

    summary_rows = []

    for employee, employee_df in details_df.groupby(
        "enterprise_id"
    ):
        total_hours = employee_df[
            "hours"
        ].sum()

        valid_hours = employee_df.loc[
            employee_df["record_valid"],
            "hours",
        ].sum()

        invalid_hours = employee_df.loc[
            ~employee_df["record_valid"],
            "hours",
        ].sum()

        valid_records = int(
            employee_df["record_valid"].sum()
        )

        invalid_records = int(
            (~employee_df["record_valid"]).sum()
        )

        summary_rows.append(
            {
                "Employee": employee,
                "Total Hours": total_hours,
                "Valid Hours": valid_hours,
                "Invalid Hours": invalid_hours,
                "Valid Records": valid_records,
                "Invalid Records": invalid_records,
                "Status": (
                    "Valid"
                    if invalid_records == 0
                    else "Needs Review"
                ),
                "AI Summary": summaries.get(
                    employee,
                    "Summary unavailable",
                ),
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    invalid_df = details_df.loc[
        ~details_df["record_valid"]
    ].copy()

    # -----------------------------------------------------
    # Create Excel workbook
    # -----------------------------------------------------

    with pd.ExcelWriter(
        output_path,
        engine="xlsxwriter",
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Executive Summary",
            index=False,
        )

        details_df.to_excel(
            writer,
            sheet_name="Worklog Details",
            index=False,
        )

        invalid_df.to_excel(
            writer,
            sheet_name="Invalid Records",
            index=False,
        )

        workbook = writer.book

        # -------------------------------------------------
        # Shared formatting
        # -------------------------------------------------

        title_format = workbook.add_format(
            {
                "bold": True,
                "font_color": "white",
                "bg_color": "#1F4E78",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )

        valid_format = workbook.add_format(
            {
                "bg_color": "#E2F0D9",
                "font_color": "#375623",
            }
        )

        invalid_format = workbook.add_format(
            {
                "bg_color": "#FCE4D6",
                "font_color": "#9C0006",
                "bold": True,
            }
        )

        wrap_format = workbook.add_format(
            {
                "text_wrap": True,
                "valign": "top",
            }
        )

        hours_format = workbook.add_format(
            {
                "num_format": "0.00",
            }
        )

        # -------------------------------------------------
        # Executive Summary formatting
        # -------------------------------------------------

        summary_sheet = writer.sheets[
            "Executive Summary"
        ]

        summary_sheet.freeze_panes(1, 0)
        summary_sheet.autofilter(
            0,
            0,
            len(summary_df),
            len(summary_df.columns) - 1,
        )

        for column_number, column_name in enumerate(
            summary_df.columns
        ):
            summary_sheet.write(
                0,
                column_number,
                column_name,
                title_format,
            )

        summary_sheet.set_column("A:A", 22)
        summary_sheet.set_column("B:D", 14, hours_format)
        summary_sheet.set_column("E:F", 14)
        summary_sheet.set_column("G:G", 16)
        summary_sheet.set_column("H:H", 65, wrap_format)

        status_column = summary_df.columns.get_loc(
            "Status"
        )

        summary_sheet.conditional_format(
            1,
            status_column,
            len(summary_df),
            status_column,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Needs Review",
                "format": invalid_format,
            },
        )

        summary_sheet.conditional_format(
            1,
            status_column,
            len(summary_df),
            status_column,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Valid",
                "format": valid_format,
            },
        )

        # -------------------------------------------------
        # Worklog Details formatting
        # -------------------------------------------------

        details_sheet = writer.sheets[
            "Worklog Details"
        ]

        details_sheet.freeze_panes(1, 0)
        details_sheet.autofilter(
            0,
            0,
            len(details_df),
            len(details_df.columns) - 1,
        )

        for column_number, column_name in enumerate(
            details_df.columns
        ):
            details_sheet.write(
                0,
                column_number,
                column_name,
                title_format,
            )

        details_sheet.set_column(
            0,
            len(details_df.columns) - 1,
            16,
        )

        # Wider text columns
        for column in [
            "employee_name",
            "project",
            "description",
            "validation_message",
        ]:
            if column in details_df.columns:
                column_index = details_df.columns.get_loc(
                    column
                )

                details_sheet.set_column(
                    column_index,
                    column_index,
                    28,
                    wrap_format,
                )

        # Highlight the entire invalid row
        if (
            not details_df.empty
            and "record_valid" in details_df.columns
        ):
            valid_column_index = (
                details_df.columns.get_loc(
                    "record_valid"
                )
            )

            excel_column = (
                _excel_column_name(
                    valid_column_index
                )
            )

            details_sheet.conditional_format(
                1,
                0,
                len(details_df),
                len(details_df.columns) - 1,
                {
                    "type": "formula",
                    "criteria": (
                        f"=${excel_column}2=FALSE"
                    ),
                    "format": invalid_format,
                },
            )

        # -------------------------------------------------
        # Invalid Records formatting
        # -------------------------------------------------

        invalid_sheet = writer.sheets[
            "Invalid Records"
        ]

        invalid_sheet.freeze_panes(1, 0)

        for column_number, column_name in enumerate(
            invalid_df.columns
        ):
            invalid_sheet.write(
                0,
                column_number,
                column_name,
                title_format,
            )

        invalid_sheet.set_column(
            0,
            max(len(invalid_df.columns) - 1, 0),
            18,
        )

        if "validation_message" in invalid_df.columns:
            message_index = invalid_df.columns.get_loc(
                "validation_message"
            )

            invalid_sheet.set_column(
                message_index,
                message_index,
                35,
                wrap_format,
            )

        if not invalid_df.empty:
            invalid_sheet.conditional_format(
                1,
                0,
                len(invalid_df),
                len(invalid_df.columns) - 1,
                {
                    "type": "no_errors",
                    "format": invalid_format,
                },
            )

    return output_path


def _excel_column_name(
    zero_based_column: int,
) -> str:
    """Convert a zero-based column number to an Excel column name."""

    column_number = zero_based_column + 1
    column_name = ""

    while column_number:
        column_number, remainder = divmod(
            column_number - 1,
            26,
        )

        column_name = (
            chr(65 + remainder)
            + column_name
        )

    return column_name