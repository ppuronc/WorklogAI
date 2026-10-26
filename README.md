# Data Engineering Project

This project provides a standard Python data engineering starter structure with a virtual environment, project package, sample ETL workflow, and testing setup.

## Project Structure

- `src/data_engineering_project/` - application source code
- `data/raw/` - raw incoming data files
- `data/processed/` - cleaned/processed outputs
- `tests/` - automated tests
- `notebooks/` - exploratory notebooks
- `requirements.txt` - Python dependencies

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate it:
   - Windows PowerShell:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - Windows Command Prompt:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
3. Install local project and dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

## Run the ETL example

```bash
python -m data_engineering_project.main
```

## CrewAI agent workflow

This project includes two equivalent ways to run the same four-agent flow:

### 1) Python-defined workflow

The direct Python version creates the `Collector`, `Aggregator`, `Validator`, and `Reporter` agents in code and runs the workflow from the project entry point.

```python
from data_engineering_project.agent_workflow import summarize_with_agents

summary = summarize_with_agents()
print(summary)
```

```bash
python -m data_engineering_project.main
```

### 2) YAML-config workflow

The project also includes a YAML file at `crewai_config.yaml` that stores the agent roles and workflow structure for configuration-based use.

```yaml
agents:
  - role: Collector
    goal: Load and inspect the latest processed data snapshot.
  - role: Aggregator
    goal: Summarize the dataset numerically and structurally.
  - role: Validator
    goal: Check for data quality issues and validation states.
  - role: Reporter
    goal: Produce a clear, stakeholder-ready summary.

workflow:
  name: data_engineering_workflow
  steps:
    - Collector
    - Aggregator
    - Validator
    - Reporter
```

```python
from data_engineering_project.agent_workflow import summarize_with_agents_from_yaml

summary = summarize_with_agents_from_yaml()
print(summary)
```

This project uses the YAML file as the declared configuration source, while the current CrewAI version in the environment still executes the compatible Python-defined workflow under the hood.

## Notes

The sample project reads an Excel file, normalizes a few fields, saves a processed CSV output, and then exposes a small agent-based summary workflow.
