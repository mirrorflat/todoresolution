from src import db
from src.models import Task


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    tasks = [
        Task(title="タスクA", urgency=3.0, importance=7.5, resolution=2.0),
        Task(title="タスクB", urgency=9.0, importance=1.0, resolution=8.5),
    ]
    db.save_tasks(tasks)

    loaded = db.load_tasks()
    loaded_by_title = {t.title: t for t in loaded}

    assert set(loaded_by_title) == {"タスクA", "タスクB"}
    assert loaded_by_title["タスクA"].urgency == 3.0
    assert loaded_by_title["タスクA"].importance == 7.5
    assert loaded_by_title["タスクA"].resolution == 2.0


def test_save_replaces_previous_state(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    db.save_tasks([Task(title="旧タスク")])
    db.save_tasks([Task(title="新タスク")])

    loaded = db.load_tasks()
    assert [t.title for t in loaded] == ["新タスク"]


def test_load_empty_db_returns_empty_list(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    assert db.load_tasks() == []
