# PlantOps

Starter scaffold for the PlantOps project.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starter usage

```bash
python -m src.cli.init_db
python -m src.automation.watcher
python -m src.automation.scheduler --interval-seconds 30 --job full_pipeline
python -m src.cli.generate_report --run-id <RUN_ID>
```

## Run app (Streamlit)

```bash
streamlit run app/Home.py
```

The Streamlit app includes these pages:
- Home
- Overview
- Predictions
- Trends
- Review Queue
- Reports
