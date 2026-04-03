# Data Schema

PlantOps uses a lightweight SQLite storage layer (`sqlite3`, no ORM) for run metadata,
file tracking, model predictions, errors, and human review queue records.

## Tables

### `runs`

| Column | Type | Notes |
|---|---|---|
| `run_id` | TEXT | Primary key |
| `started_at` | TEXT | Run start timestamp (ISO-8601 recommended) |
| `finished_at` | TEXT | Run completion timestamp |
| `total_files` | INTEGER | Files discovered in run |
| `successful_files` | INTEGER | Successfully processed files |
| `failed_files` | INTEGER | Failed files |
| `avg_confidence` | REAL | Aggregate prediction confidence |
| `notes` | TEXT | Optional run-level notes |

### `files`

| Column | Type | Notes |
|---|---|---|
| `file_id` | INTEGER | Primary key, autoincrement |
| `run_id` | TEXT | Foreign key to `runs.run_id` |
| `original_path` | TEXT | Source path at discovery time |
| `filename` | TEXT | Basename |
| `extension` | TEXT | File extension |
| `file_size_bytes` | INTEGER | File size in bytes |
| `discovered_at` | TEXT | Discovery timestamp |
| `processed_at` | TEXT | Processing timestamp |
| `status` | TEXT | Lifecycle status (`queued`, `processed`, `failed`, etc.) |

### `predictions`

| Column | Type | Notes |
|---|---|---|
| `prediction_id` | INTEGER | Primary key, autoincrement |
| `run_id` | TEXT | Foreign key to `runs.run_id` |
| `file_id` | INTEGER | Foreign key to `files.file_id` |
| `predicted_class` | TEXT | Predicted class label |
| `confidence` | REAL | Model confidence score |
| `model_version` | TEXT | Model version used |
| `is_low_confidence` | INTEGER | 1 if below threshold, otherwise 0 |
| `source_type` | TEXT | E.g. `stub`, `model`, `human` |
| `processed_at` | TEXT | Prediction timestamp |

### `errors`

| Column | Type | Notes |
|---|---|---|
| `error_id` | INTEGER | Primary key, autoincrement |
| `run_id` | TEXT | Foreign key to `runs.run_id` |
| `filename` | TEXT | File associated with error |
| `stage` | TEXT | Pipeline stage (`load`, `infer`, `save`, etc.) |
| `error_message` | TEXT | Error details |
| `created_at` | TEXT | Error timestamp |

### `review_flags`

| Column | Type | Notes |
|---|---|---|
| `review_id` | INTEGER | Primary key, autoincrement |
| `run_id` | TEXT | Foreign key to `runs.run_id` |
| `file_id` | INTEGER | Foreign key to `files.file_id` |
| `reason` | TEXT | Why review is needed |
| `suggested_label` | TEXT | Suggested class label |
| `human_label` | TEXT | Human-reviewed class label |
| `status` | TEXT | Queue state (`pending`, `in_review`, `resolved`) |
| `created_at` | TEXT | Queue insert timestamp |
| `reviewed_at` | TEXT | Human review timestamp |

## Initialization

Initialize schema with:

```bash
python -m src.cli.init_db
```

Optionally provide a custom database path:

```bash
python -m src.cli.init_db --db-path /tmp/plantops.db
```
