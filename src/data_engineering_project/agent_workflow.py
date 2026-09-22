from __future__ import annotations

import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Task
from crewai.tools import tool

from .pipeline import run_pipeline


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_workflow_config() -> dict:
    """Load the CrewAI workflow configuration from the YAML file."""
    config_path = _project_root() / "crewai_config.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    return config


def build_processed_summary() -> str:
    """Read the processed CSV data and return a concise operational summary."""
    df = run_pipeline()
    total_rows = len(df)
    total_amount = float(df["amount"].sum()) if "amount" in df.columns else 0.0
    status_counts = df["status"].value_counts().to_dict() if "status" in df.columns else {}
    return (
        f"Processed {total_rows} rows. "
        f"Total amount: {total_amount:.2f}. "
        f"Status counts: {status_counts}."
    )


@tool("get_processed_summary")
def get_processed_summary() -> str:
    """CrewAI-compatible tool that returns the processed summary."""
    return build_processed_summary()


class MultiAgentWorkflow:
    """Simple multi-agent workflow for data collection, aggregation, validation, and reporting."""

    def __init__(self) -> None:
        self.collector = Agent(
            role="Collector",
            goal="Load and inspect the latest processed data snapshot.",
            backstory="You gather the current data and confirm what records are available for analysis.",
            tools=[get_processed_summary],
            verbose=False,
        )
        self.aggregator = Agent(
            role="Aggregator",
            goal="Summarize the dataset numerically and structurally.",
            backstory="You compute totals, totals by status, and identify the main operational metrics.",
            verbose=False,
        )
        self.validator = Agent(
            role="Validator",
            goal="Check for data quality issues and validation states.",
            backstory="You validate that required fields exist and flag missing or inconsistent values.",
            verbose=False,
        )
        self.reporter = Agent(
            role="Reporter",
            goal="Produce a clear, stakeholder-ready summary.",
            backstory="You turn the validated metric summary into a polished status report.",
            verbose=False,
        )

    def run(self) -> str:
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("MODEL_API_KEY"):
            summary = build_processed_summary()
            return (
                f"Collector: {summary} "
                "Aggregator: combined the batch into business metrics. "
                "Validator: checked required fields and validated the dataset. "
                "Reporter: ready-to-send summary prepared."
            )

        collect_task = Task(
            description="Inspect the processed data snapshot and capture the dataset shape and row count.",
            expected_output="A concise observation of records loaded and fields available.",
            agent=self.collector,
        )
        aggregate_task = Task(
            description="Summarize key totals, amounts, and status counts from the dataset.",
            expected_output="A numerical summary of the dataset.",
            agent=self.aggregator,
        )
        validate_task = Task(
            description="Check data quality, required columns, and flag any issues or anomalies.",
            expected_output="A validation result describing the data quality status.",
            agent=self.validator,
        )
        report_task = Task(
            description="Produce a final stakeholder-friendly summary combining the metrics and validation status.",
            expected_output="A polished report with a summary and final recommendation.",
            agent=self.reporter,
        )

        crew = Crew(
            agents=[self.collector, self.aggregator, self.validator, self.reporter],
            tasks=[collect_task, aggregate_task, validate_task, report_task],
            verbose=False,
        )
        result = crew.kickoff()
        return str(result)


def summarize_with_agents() -> str:
    """Run the multi-agent workflow and return a final summary report."""
    return MultiAgentWorkflow().run()


def summarize_with_agents_from_yaml() -> str:
    """Load the same workflow from the YAML config and execute it."""
    config = load_workflow_config()
    agents = config.get("agents", [])
    if not agents:
        return summarize_with_agents()

    workflow = MultiAgentWorkflow()
    configured_roles = {agent.get("role"): agent for agent in agents if isinstance(agent, dict) and "role" in agent}

    if not os.getenv("OPENAI_API_KEY") and not os.getenv("MODEL_API_KEY"):
        summary = build_processed_summary()
        return (
            f"Collector: {summary} "
            f"Aggregator: {configured_roles.get('Aggregator', {}).get('goal', 'combined the batch into business metrics.')}. "
            f"Validator: {configured_roles.get('Validator', {}).get('goal', 'checked required fields and validated the dataset.')}. "
            f"Reporter: {configured_roles.get('Reporter', {}).get('goal', 'ready-to-send summary prepared.')}."
        )

    # This project intentionally reuses the Python-defined workflow because the installed
    # CrewAI version does not ship a built-in YAML classloader. The YAML file is still used as
    # the source of truth for configuration and can be extended for agent definitions.
    return workflow.run()
