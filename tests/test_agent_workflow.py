from data_engineering_project.agent_workflow import (
    load_workflow_config,
    summarize_with_agents,
    summarize_with_agents_from_yaml,
)


def test_agent_workflow_returns_summary():
    summary = summarize_with_agents()

    assert isinstance(summary, str)
    assert len(summary) > 40
    lower = summary.lower()
    assert "processed" in lower or "rows" in lower
    assert "validated" in lower or "status" in lower
    assert "report" in lower or "summary" in lower


def test_yaml_config_is_available_and_loadable():
    config = load_workflow_config()

    assert isinstance(config, dict)
    agents = config.get("agents", [])
    assert len(agents) >= 4
    roles = {agent["role"] for agent in agents}
    assert {"Collector", "Aggregator", "Validator", "Reporter"}.issubset(roles)

    yaml_summary = summarize_with_agents_from_yaml()
    assert isinstance(yaml_summary, str)
    assert len(yaml_summary) > 40
