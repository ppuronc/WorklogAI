from __future__ import annotations

from .agent_workflow import summarize_with_agents
from .pipeline import run_pipeline


def main() -> None:
    """Run the ETL example pipeline and the CrewAI workflow."""
    print("Starting data pipeline...")
    result = run_pipeline()
    print(f"Processed rows: {len(result)}")
    print(result.head().to_string(index=False))
    print("Pipeline finished successfully.")

    print("\nRunning CrewAI data-agent summary...")
    summary = summarize_with_agents()
    print(summary)


if __name__ == "__main__":
    main()
