# AGENTS.md

## Project Goal
- Build a local-first PlantOps app for plant disease monitoring and analysis.

## Environment and Workflow
- Use Python 3.12.
- Target Windows 11.
- Use VS Code as the primary editor.
- Use a `venv`-based workflow for environment management.

## Coding Standards
- Use `pathlib` instead of `os.path`.
- Use type hints throughout the codebase.
- Write clear, modular, and readable code.
- Prefer small functions and avoid giant script files.
- Do not add unnecessary abstractions.
- Do not rewrite unrelated files.

## Preferred Libraries and Stack
- Use `pandas` for analytics.
- Use `sqlite3` for storage.
- Use Streamlit for the UI.
- Use Plotly for charts.
- Use PyYAML for configuration.
- Use `watchdog` for folder watching.
- Use `pytest` for tests.

## Reliability and Error Handling
- Implement robust logging.
- Implement graceful error handling.

## Scope Constraints
- Do not add cloud deployment, authentication, Docker, Kubernetes, or training code.
- Assume real model weights may be added later, and build around a stub model now.

## Task Completion Requirements
- Every task should finish by printing:
  1. Files created or changed.
  2. Commands to run.
  3. Assumptions made.

## Ambiguity Handling
- If a later task is ambiguous, choose the simplest working implementation and leave a short TODO.
