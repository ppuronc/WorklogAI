from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

from .pipeline import run_pipeline
from .agent_workflow import summarize_with_agents
from .mask import prepare_masked_data, unmask_text
from .excel_report import create_excel_report


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------
# Local folders
# ---------------------------------------------------------

RAW_DIR = (
    BASE_DIR
    / "data"
    / "raw"
)

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)


# ---------------------------------------------------------
# SharePoint-synced folders
# ---------------------------------------------------------

SHAREPOINT_INPUT_DIR = Path(
    r"C:\Users\sayantan.deb\OneDrive - Accenture\TM\AI and Data Practice - Talent Management\Worklog AI\Inputs"
)

SHAREPOINT_REPORT_DIR = Path(
    r"C:\Users\sayantan.deb\OneDrive - Accenture\TM\AI and Data Practice - Talent Management\Worklog AI\Outputs"
)


# ---------------------------------------------------------
# Required input files
# ---------------------------------------------------------

REQUIRED_INPUT_FILES = [
    "Worklog.csv",
    "StandardsChargeCodes.csv",
]


# ---------------------------------------------------------
# Fixed SharePoint output filename
# ---------------------------------------------------------

SHAREPOINT_REPORT_NAME = (
    "WorklogAI_Report_Latest.xlsx"
)


# =========================================================
# HELPER FUNCTION 1
# COPY SHAREPOINT INPUT FILES TO LOCAL RAW FOLDER
# =========================================================

def copy_sharepoint_inputs() -> None:
    """
    Copy required source files from the SharePoint-synced
    Inputs folder into the local data/raw folder.

    Existing local files are overwritten.
    """

    print("\n" + "=" * 60)
    print("STEP 1: COPY SHAREPOINT INPUT FILES")
    print("=" * 60)

    # Verify SharePoint input folder
    if not SHAREPOINT_INPUT_DIR.exists():
        raise FileNotFoundError(
            "SharePoint input folder does not exist:\n"
            f"{SHAREPOINT_INPUT_DIR}"
        )

    # Create local raw folder if necessary
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Verify ALL required files before copying
    # -----------------------------------------------------

    missing_files = []

    for file_name in REQUIRED_INPUT_FILES:

        source_file = (
            SHAREPOINT_INPUT_DIR
            / file_name
        )

        if not source_file.exists():
            missing_files.append(file_name)

    if missing_files:
        raise FileNotFoundError(
            "Required SharePoint input files are missing: "
            + ", ".join(missing_files)
        )

    # -----------------------------------------------------
    # Copy files to local raw folder
    # -----------------------------------------------------

    for file_name in REQUIRED_INPUT_FILES:

        source_file = (
            SHAREPOINT_INPUT_DIR
            / file_name
        )

        destination_file = (
            RAW_DIR
            / file_name
        )

        shutil.copy2(
            source_file,
            destination_file,
        )

        if not destination_file.exists():
            raise FileNotFoundError(
                "Input file could not be copied locally:\n"
                f"{destination_file}"
            )

        print(f"Copied: {file_name}")

    print(
        "\nSharePoint input files copied successfully "
        "to local raw folder."
    )


# =========================================================
# HELPER FUNCTION 2
# PUBLISH LATEST REPORT TO SHAREPOINT
# =========================================================

def publish_report_to_sharepoint(
    excel_report_file: Path,
) -> Path:
    """
    Copy the latest timestamped Excel report to the
    SharePoint-synced Outputs folder using a fixed filename.

    Existing WorklogAI_Report_Latest.xlsx is overwritten.
    """

    print("\n" + "=" * 60)
    print("STEP 7: PUBLISH LATEST REPORT TO SHAREPOINT")
    print("=" * 60)

    # -----------------------------------------------------
    # Verify locally generated report
    # -----------------------------------------------------

    if not excel_report_file.exists():
        raise FileNotFoundError(
            "Local Excel report does not exist:\n"
            f"{excel_report_file}"
        )

    # -----------------------------------------------------
    # Verify SharePoint output folder
    # -----------------------------------------------------

    if not SHAREPOINT_REPORT_DIR.exists():
        raise FileNotFoundError(
            "SharePoint-synced output folder does not exist:\n"
            f"{SHAREPOINT_REPORT_DIR}"
        )

    # -----------------------------------------------------
    # Fixed SharePoint report filename
    # -----------------------------------------------------

    sharepoint_report_file = (
        SHAREPOINT_REPORT_DIR
        / SHAREPOINT_REPORT_NAME
    )

    print("\nLocal source:")
    print(excel_report_file)

    print("\nSharePoint destination:")
    print(sharepoint_report_file)

    # -----------------------------------------------------
    # Copy and overwrite previous SharePoint report
    # -----------------------------------------------------

    shutil.copy2(
        excel_report_file,
        sharepoint_report_file,
    )

    # -----------------------------------------------------
    # Verify copy
    # -----------------------------------------------------

    if not sharepoint_report_file.exists():
        raise FileNotFoundError(
            "Report could not be copied to SharePoint:\n"
            f"{sharepoint_report_file}"
        )

    print(
        "\nLatest report successfully published "
        "to SharePoint."
    )

    return sharepoint_report_file


# =========================================================
# MAIN WORKLOGAI WORKFLOW
# =========================================================

def main() -> None:
    """
    Execute the complete WorklogAI workflow.

    SharePoint Inputs
        -> Local Raw Files
        -> ETL / Validation
        -> Identity Masking
        -> Ollama Analysis
        -> Identity Restoration
        -> Excel Reporting
        -> Local Historical Archive
        -> SharePoint Latest Report
    """

    print("\n" + "=" * 60)
    print("WORKLOGAI PROCESS STARTED")
    print("=" * 60)


    # =====================================================
    # STEP 1
    # COPY SHAREPOINT INPUT FILES TO LOCAL RAW
    # =====================================================

    copy_sharepoint_inputs()


    # =====================================================
    # STEP 2
    # RUN ETL AND VALIDATION PIPELINE
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 2: RUN ETL AND VALIDATION PIPELINE")
    print("=" * 60)

    result = run_pipeline()

    if result is None:
        raise RuntimeError(
            "Pipeline did not return a DataFrame."
        )

    if result.empty:
        raise ValueError(
            "Pipeline returned an empty DataFrame."
        )

    print(
        "\nPipeline completed successfully."
    )

    print(
        f"Records processed: {len(result)}"
    )


    # =====================================================
    # STEP 3
    # DISPLAY PROCESSED DATA
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 3: PROCESSED DATA")
    print("=" * 60)

    print(result)


    # =====================================================
    # STEP 4
    # MASK SENSITIVE DATA BEFORE OLLAMA
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 4: MASK SENSITIVE IDENTITIES")
    print("=" * 60)

    masked_result, token_registry = (
        prepare_masked_data(result)
    )

    print(
        "\nSensitive identity fields successfully "
        "masked before AI processing."
    )


    # =====================================================
    # STEP 5
    # GENERATE AI WORKLOG SUMMARIES
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 5: GENERATE AI WORKLOG SUMMARIES")
    print("=" * 60)

    masked_summaries = summarize_with_agents(
        masked_result
    )

    if not masked_summaries:
        raise RuntimeError(
            "No AI worklog summaries were generated."
        )

    print(
        f"\nAI summaries generated: "
        f"{len(masked_summaries)}"
    )


    # =====================================================
    # STEP 6
    # RESTORE IDENTITIES AND CREATE EXCEL REPORT
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 6: CREATE FINAL EXCEL REPORT")
    print("=" * 60)

    unmasked_summaries: dict[str, str] = {}

    # -----------------------------------------------------
    # Restore employee identities
    # -----------------------------------------------------

    for masked_employee, masked_summary in (
        masked_summaries.items()
    ):

        employee = unmask_text(
            masked_employee,
            token_registry,
        )

        summary = unmask_text(
            masked_summary,
            token_registry,
        )

        unmasked_summaries[
            employee
        ] = summary

        # Display restored AI summary
        print("\n" + "-" * 60)
        print(f"Employee: {employee}")
        print("-" * 60)
        print(summary)


    # -----------------------------------------------------
    # Create local processed folder
    # -----------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------------------
    # Generate timestamped local filename
    # -----------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    excel_report_file = (
        PROCESSED_DIR
        / f"WorklogAI_Report_{timestamp}.xlsx"
    )


    # -----------------------------------------------------
    # Create formatted Excel workbook
    # -----------------------------------------------------

    create_excel_report(
        processed_df=result,
        summaries=unmasked_summaries,
        output_path=excel_report_file,
    )


    # -----------------------------------------------------
    # Verify Excel report creation
    # -----------------------------------------------------

    if not excel_report_file.exists():
        raise FileNotFoundError(
            "Excel report was not created:\n"
            f"{excel_report_file}"
        )

    print(
        "\nLocal historical Excel report created:"
    )

    print(
        excel_report_file
    )


    # =====================================================
    # STEP 7
    # PUBLISH LATEST EXCEL REPORT TO SHAREPOINT
    # =====================================================

    sharepoint_report_file = (
        publish_report_to_sharepoint(
            excel_report_file
        )
    )


    # =====================================================
    # STEP 8
    # FINAL COMPLETION SUMMARY
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 8: WORKLOGAI PROCESS COMPLETED")
    print("=" * 60)

    print("\nSharePoint input location:")
    print(SHAREPOINT_INPUT_DIR)

    print("\nLocal raw input location:")
    print(RAW_DIR)

    print("\nLocal historical report:")
    print(excel_report_file)

    print("\nLatest SharePoint report:")
    print(sharepoint_report_file)

    print("\nExecution summary:")
    print(
        f"  Records processed       : {len(result)}"
    )

    print(
        f"  Employee reports created: "
        f"{len(unmasked_summaries)}"
    )

    print(
        f"  SharePoint report       : "
        f"{SHAREPOINT_REPORT_NAME}"
    )

    print("\n" + "=" * 60)
    print("WORKLOGAI EXECUTION SUCCESSFUL")
    print("=" * 60)


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()