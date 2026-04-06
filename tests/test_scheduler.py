from __future__ import annotations

from src.automation.scheduler import run_polling_scheduler


def test_run_polling_scheduler_run_once_executes_single_cycle(test_settings) -> None:
    calls: list[object] = []

    def job(settings):
        calls.append(settings)
        return {"status": "ok"}

    run_polling_scheduler(
        settings=test_settings,
        interval_seconds=10,
        job=job,
        run_once=True,
    )

    assert len(calls) == 1


def test_run_polling_scheduler_continues_until_keyboard_interrupt(monkeypatch, test_settings) -> None:
    calls = {"count": 0}

    def job(_settings):
        calls["count"] += 1
        return {"count": calls["count"]}

    def fake_sleep(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("src.automation.scheduler.time.sleep", fake_sleep)

    run_polling_scheduler(
        settings=test_settings,
        interval_seconds=1,
        job=job,
        run_once=False,
    )

    assert calls["count"] == 1
