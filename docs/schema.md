# PlantOps SQLite Schema

PlantOps uses SQLite (`sqlite3`) for local-first persistence.

- Schema creation entry point: `python -m src.cli.init_db`
- Core schema SQL: `src/storage/schema.py`

## ER overview

- A **run** has many **files**.
- A **run** has many **predictions**.
- A **file** can have one or more **predictions** (pipeline currently writes one prediction per processed file).
- A **run** has many **errors**.
- A **file** can have zero or more **review_flags**.

```text
runs (1) ───< files (many)
runs (1) ───< predictions (many)
files (1) ───< predictions (many)
runs (1) ───< errors (many)
files (1) ───< review_flags (many)
runs (1) ───< review_flags (many)
```

---

## Tables

### `runs`

Tracks one execution of a batch/pipeline job.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `run_id` | TEXT | PRIMARY KEY | Unique run identifier (e.g., timestamp + suffix). |
| `started_at` | TEXT | NULL | Run start timestamp (ISO-8601 recommended). |
| `finished_at` | TEXT | NULL | Run completion timestamp. |
| `total_files` | INTEGER | NULL | Number of discovered candidate files. |
| `successful_files` | INTEGER | NULL | Successfully processed files. |
| `failed_files` | INTEGER | NULL | Failed files count. |
| `avg_confidence` | REAL | NULL | Mean confidence across successful predictions. |
| `notes` | TEXT | NULL | Optional run metadata. |

### `files`

Tracks discovered/processed files and their lineage.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `file_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal file row identifier. |
| `run_id` | TEXT | NOT NULL, FK `runs(run_id)` ON DELETE CASCADE | Parent run. |
| `original_path` | TEXT | NULL | Source file path at discovery time. |
| `filename` | TEXT | NULL | Basename. |
| `extension` | TEXT | NULL | File extension. |
| `file_size_bytes` | INTEGER | NULL | Source file size. |
| `discovered_at` | TEXT | NULL | Discovery timestamp. |
| `processed_at` | TEXT | NULL | Processing timestamp. |
| `status` | TEXT | NULL | Lifecycle status (`queued`, `processed`, `failed`, etc.). |

### `predictions`

Stores model outputs tied to files and runs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `prediction_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal prediction identifier. |
| `run_id` | TEXT | NOT NULL, FK `runs(run_id)` ON DELETE CASCADE | Parent run. |
| `file_id` | INTEGER | NOT NULL, FK `files(file_id)` ON DELETE CASCADE | Source file reference. |
| `predicted_class` | TEXT | NULL | Predicted label. |
| `confidence` | REAL | NULL | Confidence score (0..1). |
| `model_version` | TEXT | NULL | Model identity/version. |
| `is_low_confidence` | INTEGER | NULL | 1 when confidence < threshold, else 0. |
| `source_type` | TEXT | NULL | E.g., `stub_rule`, `stub_hash`, `model`. |
| `processed_at` | TEXT | NULL | Prediction timestamp. |

### `errors`

Stores recoverable per-file/pipeline errors.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `error_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal error identifier. |
| `run_id` | TEXT | NOT NULL, FK `runs(run_id)` ON DELETE CASCADE | Parent run. |
| `filename` | TEXT | NULL | File associated with failure. |
| `stage` | TEXT | NULL | Pipeline stage (`load`, `inference`, `save`, etc.). |
| `error_message` | TEXT | NULL | Human-readable details. |
| `created_at` | TEXT | NULL | Error timestamp. |

### `review_flags`

Tracks files requiring manual review.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `review_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal review queue identifier. |
| `run_id` | TEXT | NOT NULL, FK `runs(run_id)` ON DELETE CASCADE | Parent run. |
| `file_id` | INTEGER | NOT NULL, FK `files(file_id)` ON DELETE CASCADE | Flagged file reference. |
| `reason` | TEXT | NULL | Why review was triggered. |
| `suggested_label` | TEXT | NULL | Auto-predicted label to aid reviewer. |
| `human_label` | TEXT | NULL | Reviewer-corrected label. |
| `status` | TEXT | NULL | Queue status (`pending`, `in_review`, `resolved`). |
| `created_at` | TEXT | NULL | Flag creation timestamp. |
| `reviewed_at` | TEXT | NULL | Review completion timestamp. |

---

## Indexes

Defined indexes (for common dashboard/report workloads):

- `idx_files_run_id` on `files(run_id)`
- `idx_predictions_run_id` on `predictions(run_id)`
- `idx_predictions_class` on `predictions(predicted_class)`
- `idx_review_flags_status_created_at` on `review_flags(status, created_at)`

---

## Initialization commands

```bash
python -m src.cli.init_db
```

Custom DB path:

```bash
python -m src.cli.init_db --db-path /tmp/plantops.db
```

---

## Notes for future schema evolution

- Prefer additive migrations (new tables/columns/indexes).
- Keep `run_id` immutable and externally visible in output artifacts.
- Maintain foreign-key constraints to preserve lineage integrity.
- If introducing corrections workflow, add explicit correction/audit tables rather than overloading existing prediction rows.
