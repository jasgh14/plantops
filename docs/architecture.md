# PlantOps Architecture

This document describes PlantOps as a local-first pipeline for plant image disease monitoring.

## System flow (high level)

1. **Ingestion**
   - Images arrive in `inbox_dir`.
   - `discover_images` filters by configured file extensions.
   - `validate_image` / preprocessing enforces image readability and metadata extraction.

2. **Inference**
   - `predict_image` preprocesses image metadata and invokes the loaded classifier.
   - Current default is `StubClassifier` for deterministic behavior.
   - Postprocessing normalizes output fields and computes `is_low_confidence`.

3. **Storage**
   - SQLite schema stores run-level and file-level lineage.
   - Repository helpers insert rows into `runs`, `files`, `predictions`, `errors`, `review_flags`.

4. **Analytics**
   - SQL-backed query helpers aggregate class counts, confidence stats, trends, and run summaries.
   - Analytics data feeds both reports and Streamlit views.

5. **Review loop**
   - Low-confidence predictions are flagged via `review_logic`.
   - Flagged files are copied to run-scoped review folders for manual triage.

6. **Reporting**
   - `generate_run_report` creates Markdown report, summary JSON, plots, and CSV exports.
   - Report artifacts are written under `outputs/`.

7. **Automation**
   - **Watcher**: event + stability-based inbox monitor that triggers full pipeline.
   - **Scheduler**: polling loop for recurring jobs (`full_pipeline`, `daily_report`).

---

## Component map

- `src/pipeline/`
  - File discovery, validation, per-file processing, and batch orchestration.
- `src/inference/`
  - Classifier interface, model loading, stub classifier, preprocess/postprocess.
- `src/storage/`
  - DB connection, schema initialization, repositories, and query helpers.
- `src/analytics/`
  - Data aggregation, plotting, and export helpers.
- `src/reports/`
  - Report template and generation logic.
- `src/automation/`
  - Watcher, scheduler, and job wrappers.
- `src/cli/`
  - Operational entry points.
- `app/`
  - Streamlit dashboard pages.

---

## Data lifecycle

### Ingestion path

`inbox` → discovered & validated images → batch processor

### Processing path

validated image → prediction → persistence (file + prediction + optional review flag) → move to processed

### Reporting path

DB records → analytics queries → plots/CSV/JSON → Markdown report

---

## Reliability notes

- DB schema is initialized before pipeline runs.
- Foreign keys are enabled for referential integrity.
- Per-file failures are logged in `errors` and do not crash entire batch run.
- Low-confidence handling is explicit and persisted.
- End-to-end CLI usage is test-covered with the stub model.

---

## Extension points

- Replace/extend model loader behavior in `src/inference/model_loader.py`.
- Add new automation jobs in `src/automation/jobs.py`.
- Extend review status transitions and correction writeback flow.
- Add domain-specific analytics/reports with additional query helpers.
