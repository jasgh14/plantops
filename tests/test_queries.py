from __future__ import annotations

from src.storage.db import get_connection
from src.storage.queries import (
    average_confidence_by_class,
    disease_counts,
    healthy_vs_diseased_split,
    low_confidence_rate,
    recent_review_queue_items,
    run_level_summaries,
)
from src.storage.repositories import (
    insert_error,
    insert_file,
    insert_prediction,
    insert_review_flag,
    insert_run,
)
from src.storage.schema import init_database


def test_query_helpers_return_expected_aggregates(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    init_database(db_path)

    with get_connection(db_path) as connection:
        insert_run(connection, run_id="run-a", started_at="2026-01-01T00:00:00Z", total_files=3)
        insert_run(connection, run_id="run-b", started_at="2026-01-02T00:00:00Z", total_files=1)

        file_a1 = insert_file(connection, run_id="run-a", filename="a1.jpg")
        file_a2 = insert_file(connection, run_id="run-a", filename="a2.jpg")
        file_b1 = insert_file(connection, run_id="run-b", filename="b1.jpg")

        insert_prediction(
            connection,
            run_id="run-a",
            file_id=file_a1,
            predicted_class="healthy",
            confidence=0.95,
            is_low_confidence=0,
        )
        insert_prediction(
            connection,
            run_id="run-a",
            file_id=file_a2,
            predicted_class="leaf_spot",
            confidence=0.42,
            is_low_confidence=1,
        )
        insert_prediction(
            connection,
            run_id="run-b",
            file_id=file_b1,
            predicted_class="powdery_mildew",
            confidence=0.88,
            is_low_confidence=0,
        )

        insert_error(
            connection,
            run_id="run-a",
            filename="oops.jpg",
            stage="save",
            error_message="disk full",
        )

        insert_review_flag(
            connection,
            run_id="run-a",
            file_id=file_a2,
            reason="low confidence",
            suggested_label="leaf_spot",
            status="pending",
            created_at="2026-01-03T00:00:00Z",
        )
        insert_review_flag(
            connection,
            run_id="run-b",
            file_id=file_b1,
            reason="manual",
            suggested_label="powdery_mildew",
            status="pending",
            created_at="2026-01-04T00:00:00Z",
        )

        disease = disease_counts(connection)
        split = healthy_vs_diseased_split(connection)
        avg_conf = average_confidence_by_class(connection)
        low_rate = low_confidence_rate(connection)
        review_items = recent_review_queue_items(connection, limit=1)
        summaries = run_level_summaries(connection)

    assert {row["predicted_class"] for row in disease} == {"leaf_spot", "powdery_mildew"}
    assert split == {"healthy": 1, "diseased": 2}

    by_class = {row["predicted_class"]: row for row in avg_conf}
    assert by_class["healthy"]["avg_confidence"] == 0.95
    assert round(by_class["leaf_spot"]["avg_confidence"], 2) == 0.42
    assert round(low_rate, 2) == 0.33

    assert len(review_items) == 1
    assert review_items[0]["filename"] == "b1.jpg"

    summary_by_run = {row["run_id"]: row for row in summaries}
    assert summary_by_run["run-a"]["files_discovered"] == 2
    assert summary_by_run["run-a"]["predictions_generated"] == 2
    assert summary_by_run["run-a"]["errors_logged"] == 1
