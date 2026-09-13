from src import app as app_module
from src import db


def test_add_appends_task_with_default_values(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.simpledialog, "askstring", lambda *a, **k: "新しいタスク")

    app = app_module.App()
    app.update_idletasks()
    try:
        app.on_add()

        assert [t.title for t in app.tasks] == ["新しいタスク"]
        task = app.tasks[0]
        assert (task.urgency, task.importance, task.resolution) == (5.0, 5.0, 5.0)
    finally:
        app.destroy()


def test_add_appends_without_disturbing_existing_tasks(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA"])
        app.tasks[0].urgency = 8.0

        monkeypatch.setattr(app_module.simpledialog, "askstring", lambda *a, **k: "タスクB")
        app.on_add()

        assert [t.title for t in app.tasks] == ["タスクA", "タスクB"]
        assert app.tasks[0].urgency == 8.0  # untouched
    finally:
        app.destroy()


def test_add_cancelled_dialog_is_noop(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.simpledialog, "askstring", lambda *a, **k: None)

    app = app_module.App()
    app.update_idletasks()
    try:
        app.on_add()
        assert app.tasks == []
    finally:
        app.destroy()


def test_add_blank_title_is_noop(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.simpledialog, "askstring", lambda *a, **k: "   ")

    app = app_module.App()
    app.update_idletasks()
    try:
        app.on_add()
        assert app.tasks == []
    finally:
        app.destroy()
