import sqlite3

from src import db
from src.models import Purpose, Task


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


def test_done_flag_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    db.save_tasks([Task(title="完了済み", done=True), Task(title="未完了", done=False)])

    loaded_by_title = {t.title: t for t in db.load_tasks()}
    assert loaded_by_title["完了済み"].done is True
    assert loaded_by_title["未完了"].done is False


def test_pre_existing_db_without_done_column_is_migrated(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)

    # Simulate a database created before the "done" column existed.
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE tasks (
            title TEXT PRIMARY KEY,
            urgency REAL NOT NULL,
            importance REAL NOT NULL,
            resolution REAL NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO tasks (title, urgency, importance, resolution) VALUES (?, ?, ?, ?)",
        ("旧タスク", 4.0, 6.0, 3.0),
    )
    conn.commit()
    conn.close()

    loaded = db.load_tasks()
    assert len(loaded) == 1
    assert loaded[0].title == "旧タスク"
    assert loaded[0].done is False  # migrated column defaults to not-done

    db.save_tasks(loaded)
    reloaded = db.load_tasks()
    assert reloaded[0].done is False


def test_purpose_field_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    db.save_tasks([Task(title="タスクA", purpose="健康"), Task(title="タスクB", purpose=None)])

    loaded_by_title = {t.title: t for t in db.load_tasks()}
    assert loaded_by_title["タスクA"].purpose == "健康"
    assert loaded_by_title["タスクB"].purpose is None


def test_purposes_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    db.save_purposes([Purpose(name="健康", color="green"), Purpose(name="仕事", color="blue")])

    loaded_by_name = {p.name: p for p in db.load_purposes()}
    assert set(loaded_by_name) == {"健康", "仕事"}
    assert loaded_by_name["健康"].color == "green"


def test_pre_existing_db_without_purpose_column_is_migrated(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)

    # Simulate a database created before "done"/"purpose" columns existed.
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE tasks (
            title TEXT PRIMARY KEY,
            urgency REAL NOT NULL,
            importance REAL NOT NULL,
            resolution REAL NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO tasks (title, urgency, importance, resolution) VALUES (?, ?, ?, ?)",
        ("旧タスク", 4.0, 6.0, 3.0),
    )
    conn.commit()
    conn.close()

    loaded = db.load_tasks()
    assert len(loaded) == 1
    assert loaded[0].purpose is None
