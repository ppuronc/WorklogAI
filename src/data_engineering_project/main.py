from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .pipeline import run_pipeline
from .agent_workflow import summarize_with_agents
from .mask import prepare_masked_data, unmask_text


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)


def main():
    """Run ETL, mask sensitive data, generate AI reports,
    restore identities, display reports, and save output.
    """

    # -----------------------------------------------------
    # Step 1: Run ETL pipeline
    # -----------------------------------------------------

    print("Starting data pipeline...")

    result = run_pipeline()

    print("\nPipeline completed successfully.")


    # -----------------------------------------------------
    # Step 2: Display processed data
    # -----------------------------------------------------

    print("\nProcessed Data:")
    print(result)


    # -----------------------------------------------------
    # Step 3: Create masked copy for Ollama
    # -----------------------------------------------------

    masked_result, token_registry = prepare_masked_data(
        result
    )

    print(
        "\nSensitive identity fields masked "
        "before AI processing."
    )


    # -----------------------------------------------------
    # Step 4: Generate AI reports using MASKED data
    # -----------------------------------------------------

    print("\nGenerating AI worklog reports...\n")

    masked_summaries = summarize_with_agents(
        masked_result
    )


    # -----------------------------------------------------
    # Step 5: Restore identities and display reports
    # -----------------------------------------------------

    report_sections = []

    for masked_employee, masked_summary in (
        masked_summaries.items()
    ):

        # Restore employee identity
        employee = unmask_text(
            masked_employee,
            token_registry,
        )

        # Restore identities/tokens contained in AI output
        summary = unmask_text(
            masked_summary,
            token_registry,
        )

        report_section = (
            "=" * 60
            + f"\nEmployee: {employee}\n"
            + "=" * 60
            + f"\n{summary}\n"
        )

        # Display final unmasked report
        print(report_section)

        # Store same report for file output
        report_sections.append(
            report_section
        )


    # -----------------------------------------------------
    # Step 6: Save final UNMASKED AI summary report
    # -----------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_file = (
        PROCESSED_DIR
        / f"WorklogAI_Summary_report_{timestamp}.txt"
    )

    full_report = "\n".join(
        report_sections
    )

    report_file.write_text(
        full_report,
        encoding="utf-8"
    )


    # -----------------------------------------------------
    # Step 7: Completion message
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("WORKLOG AI REPORT COMPLETED")
    print("=" * 60)

    print(
        f"Summary report saved to:\n{report_file}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
