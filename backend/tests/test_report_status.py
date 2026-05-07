import asyncio

from app.modules.meeting import repository


class FakePool:
    def __init__(self):
        self.executed = []

    async def execute(self, sql, *args):
        self.executed.append((sql, args))

    async def fetchrow(self, sql, *args):
        return {
            "room_id": args[0],
            "report_status": "processing",
            "report_error": None,
            "report_requested_at": None,
            "ended_at": None,
            "has_report": False,
        }


def test_set_report_status_records_queued_timestamp(monkeypatch):
    pool = FakePool()
    monkeypatch.setattr(repository.db, "pool", pool)

    asyncio.run(repository.set_report_status("room-a", "queued"))

    sql, args = pool.executed[0]
    assert "report_requested_at" in sql
    assert args == ("queued", "room-a")


def test_save_meeting_report_marks_completed(monkeypatch):
    pool = FakePool()
    monkeypatch.setattr(repository.db, "pool", pool)

    asyncio.run(repository.save_meeting_report("room-a", "{}"))

    sql, args = pool.executed[0]
    assert "report_status = 'completed'" in sql
    assert args == ("{}", "room-a")


def test_get_report_status_returns_status_shape(monkeypatch):
    pool = FakePool()
    monkeypatch.setattr(repository.db, "pool", pool)

    status = asyncio.run(repository.get_report_status("room-a"))

    assert status["room_id"] == "room-a"
    assert status["report_status"] == "processing"
    assert status["has_report"] is False
