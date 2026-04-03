from __future__ import annotations

import sqlite3


def insert_run(
    connection: sqlite3.Connection,
    run_id: str,
    started_at: str | None = None,
    finished_at: str | None = None,
    total_files: int | None = None,
    successful_files: int | None = None,
    failed_files: int | None = None,
    avg_confidence: float | None = None,
    notes: str | None = None,
) -> str:
    connection.execute(
        """
        INSERT INTO runs (
            run_id, started_at, finished_at, total_files,
            successful_files, failed_files, avg_confidence, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            started_at,
            finished_at,
            total_files,
            successful_files,
            failed_files,
            avg_confidence,
            notes,
        ),
    )
    return run_id


def insert_file(
    connection: sqlite3.Connection,
    run_id: str,
    original_path: str | None = None,
    filename: str | None = None,
    extension: str | None = None,
    file_size_bytes: int | None = None,
    discovered_at: str | None = None,
    processed_at: str | None = None,
    status: str | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO files (
            run_id, original_path, filename, extension,
            file_size_bytes, discovered_at, processed_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            original_path,
            filename,
            extension,
            file_size_bytes,
            discovered_at,
            processed_at,
            status,
        ),
    )
    return int(cursor.lastrowid)


def insert_prediction(
    connection: sqlite3.Connection,
    run_id: str,
    file_id: int,
    predicted_class: str | None = None,
    confidence: float | None = None,
    model_version: str | None = None,
    is_low_confidence: int | None = None,
    source_type: str | None = None,
    processed_at: str | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO predictions (
            run_id, file_id, predicted_class, confidence,
            model_version, is_low_confidence, source_type, processed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            file_id,
            predicted_class,
            confidence,
            model_version,
            is_low_confidence,
            source_type,
            processed_at,
        ),
    )
    return int(cursor.lastrowid)


def insert_error(
    connection: sqlite3.Connection,
    run_id: str,
    filename: str | None = None,
    stage: str | None = None,
    error_message: str | None = None,
    created_at: str | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO errors (run_id, filename, stage, error_message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, filename, stage, error_message, created_at),
    )
    return int(cursor.lastrowid)


def insert_review_flag(
    connection: sqlite3.Connection,
    run_id: str,
    file_id: int,
    reason: str | None = None,
    suggested_label: str | None = None,
    human_label: str | None = None,
    status: str | None = None,
    created_at: str | None = None,
    reviewed_at: str | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO review_flags (
            run_id, file_id, reason, suggested_label,
            human_label, status, created_at, reviewed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            file_id,
            reason,
            suggested_label,
            human_label,
            status,
            created_at,
            reviewed_at,
        ),
    )
    return int(cursor.lastrowid)
