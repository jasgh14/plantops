from __future__ import annotations

from pathlib import Path

from src.pipeline.review_logic import route_to_review, should_flag_for_review
from src.storage.db import get_connection
from src.storage.repositories import insert_file, insert_run
from src.storage.schema import init_database


def test_should_flag_for_review() -> None:
    assert should_flag_for_review(0.55, 0.6)
    assert not should_flag_for_review(0.6, 0.6)


def test_route_to_review_creates_flag_and_copy(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    init_database(db_path)

    source = tmp_path / "leaf.jpg"
    source.write_bytes(b"abc")

    with get_connection(db_path) as connection:
        insert_run(connection, run_id="run-1")
        file_id = insert_file(connection, run_id="run-1", filename="leaf.jpg")

        flagged = route_to_review(
            source_path=source,
            review_dir=tmp_path / "review",
            run_id="run-1",
            file_id=file_id,
            predicted_class="leaf_spot",
            confidence=0.2,
            threshold=0.6,
            connection=connection,
        )

        row = connection.execute("SELECT COUNT(*) AS c FROM review_flags").fetchone()

    assert flagged is True
    assert row["c"] == 1
    assert (tmp_path / "review" / "run-1" / "leaf.jpg").exists()
