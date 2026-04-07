# PlantOps

PlantOps is a **local-first plant disease monitoring and analysis toolkit** built around a simple, reliable pipeline: discover images, validate files, run model inference (currently a deterministic stub model), persist results in SQLite, surface low-confidence predictions for review, and generate operational reports.

It is designed for practical day-to-day workflows on a single machine (Windows 11 target, Python + Streamlit stack), without cloud complexity.

---

## Overview

PlantOps includes:

- CLI tools for one-off and batch prediction.
- A pipeline runner that writes run/file/prediction/review/error records to SQLite.
- Automation utilities:
  - inbox file watcher
  - polling scheduler
- Analytics and report generation (Markdown + JSON + Plotly HTML assets).
- Streamlit dashboard pages for overview, predictions, trends, review queue, and reports.

---

## Why PlantOps exists

Plant disease workflows often start messy: ad-hoc folders, manual checks, and hard-to-reproduce decisions. PlantOps provides a disciplined baseline that is:

- **Local-first**: no required cloud services.
- **Auditable**: each run, file, prediction, and review flag is recorded.
- **Review-friendly**: low-confidence predictions can be triaged.
- **Extensible**: stub model now, production model later without rewriting the pipeline.

---

## Repo structure

```text
plantops/
├─ app/                    # Streamlit UI
├─ configs/                # App and logging config
├─ data/                   # Inbox/processed/archive/review/corrected dirs
├─ docs/                   # Architecture + schema docs
├─ models/                 # Model artifacts and model documentation
├─ outputs/                # Generated predictions, plots, reports, logs
├─ src/
│  ├─ analytics/           # Query-backed analytics + plotting/export helpers
│  ├─ automation/          # File watcher, scheduler, automation jobs
│  ├─ cli/                 # CLI entry modules
│  ├─ inference/           # Pre/postprocess + model loading + stub classifier
│  ├─ pipeline/            # Discovery, validation, per-file + batch orchestration
│  ├─ reports/             # Markdown report generation
│  ├─ storage/             # SQLite schema, repositories, query helpers
│  └─ settings.py          # YAML + env settings loading
└─ tests/                  # Pytest suite
```

---

## Install

> Recommended: Python 3.12, venv workflow.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux (bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

Default config file: `configs/config.yaml`.

You can override config path at runtime:

```bash
export PLANTOPS_CONFIG_PATH=/absolute/path/to/config.yaml
```

(Windows PowerShell: `$env:PLANTOPS_CONFIG_PATH = 'C:\\path\\to\\config.yaml'`)

Environment variables can override key settings such as DB path, outputs path, and threshold.

---

## Core commands

### 1) `init_db`

Initialize SQLite schema:

```bash
python -m src.cli.init_db
# or
python -m src.cli.init_db --db-path ./data/plantops.db
```

### 2) `predict_one`

Run prediction on a single image:

```bash
python -m src.cli.predict_one --image ./data/inbox/sample_leaf.jpg
```

### 3) `predict_batch`

Run batch pipeline on a directory:

```bash
python -m src.cli.predict_batch --input-dir ./data/inbox
```

Optional archive copy:

```bash
python -m src.cli.predict_batch --input-dir ./data/inbox --archive-processed
```

### 4) `run_pipeline`

Run the main inbox batch flow using configured inbox path:

```bash
python -m src.cli.run_pipeline
```

### 5) `watcher`

Watch inbox and run pipeline once files are stable:

```bash
python -m src.automation.watcher --stable-seconds 3 --poll-seconds 1
```

### 6) `scheduler`

Polling scheduler for automation jobs:

```bash
python -m src.automation.scheduler --interval-seconds 30 --job full_pipeline
python -m src.automation.scheduler --interval-seconds 3600 --job daily_report
```

Single-cycle mode:

```bash
python -m src.automation.scheduler --interval-seconds 30 --job full_pipeline --run-once
```

### 7) Streamlit dashboard

```bash
streamlit run app/Home.py
```

### 8) Report generation

```bash
python -m src.cli.generate_report --run-id <RUN_ID>
```

Outputs include:

- `outputs/reports/<RUN_ID>_report.md`
- `outputs/reports/<RUN_ID>_summary.json`
- `outputs/plots/<RUN_ID>/*.html`
- `outputs/reports/data/<RUN_ID>/*.csv`

---

## Stub model behavior

The current classifier is deterministic and filename-driven:

- Files containing `healthy` => class `healthy` (high confidence).
- Files containing known disease keywords (`blight`, `rust`, `spot`, `mildew`, `rot`, `scab`) => mapped class.
- Otherwise, deterministic hash fallback picks a class + confidence.

This enables repeatable local testing and pipeline validation before shipping a real model.

---

## How to plug in a real model

1. Add real model artifacts under `models/`.
2. Update/extend loader behavior in `src/inference/model_loader.py`.
3. Keep the predictor contract stable (`predicted_class`, `confidence`, `source_type`, `notes`).
4. Preserve postprocessing logic (threshold handling, timestamps, output schema).
5. Add/adjust tests for real model I/O and confidence calibration.

Tip: Keep stub fallback available behind config (`use_stub_model`) for smoke tests and CI reliability.

---

## Sample workflow

```bash
# 1) setup
python -m src.cli.init_db

# 2) place test images in data/inbox
# e.g. tomato_healthy_001.jpg, pepper_blight_002.jpg

# 3) run pipeline
python -m src.cli.run_pipeline

# 4) inspect generated outputs
# - outputs/predictions/<RUN_ID>/results.csv
# - outputs/predictions/<RUN_ID>/summary.json

# 5) generate report
python -m src.cli.generate_report --run-id <RUN_ID>

# 6) open dashboard
streamlit run app/Home.py
```

---

## Limitations (current state)

- Stub model is heuristic-only and not biologically accurate.
- Local file system assumptions; no distributed workers.
- No authentication/authorization (intentionally out of scope).
- No model training pipeline in this repository.
- Watcher and scheduler are process-based and intended for local operations.

---

## Future improvements

- Real model integration with model registry metadata.
- Better calibration and confidence explainability.
- Human review tooling for correction feedback loops.
- Richer anomaly detection and trend alerts.
- Packaging and install ergonomics for field deployments.

---

## Testing

Run all tests:

```bash
pytest -q
```

Run a subset:

```bash
pytest -q tests/test_end_to_end.py tests/test_report_generation.py
```
