from src import app as app_module
from src import db
from src.models import Task


def test_delete_without_selection_shows_info_and_does_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    shown = []
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: shown.append(a))

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA"])
        app.on_delete()
        assert len(shown) == 1
        assert [t.title for t in app.tasks] == ["タスクA"]
    finally:
        app.destroy()


def test_delete_confirmed_removes_selected_task(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.messagebox, "askyesno", lambda *a, **k: True)

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA", "タスクB"])
        target = next(t for t in app.tasks if t.title == "タスクA")
        app.on_table_selected(target)

        app.on_delete()

        assert [t.title for t in app.tasks] == ["タスクB"]
        assert app.selected_task is None
    finally:
        app.destroy()


def test_delete_cancelled_keeps_task(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.messagebox, "askyesno", lambda *a, **k: False)

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA"])
        app.on_table_selected(app.tasks[0])

        app.on_delete()

        assert [t.title for t in app.tasks] == ["タスクA"]
        assert app.selected_task is app.tasks[0]
    finally:
        app.destroy()


def test_delete_duplicate_titled_task_removes_only_the_selected_object(tmp_path, monkeypatch):
    # Two tasks with identical field values are == under Task's dataclass
    # __eq__, so deletion must be identity-based or it could drop the wrong one.
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.messagebox, "askyesno", lambda *a, **k: True)

    app = app_module.App()
    app.update_idletasks()
    try:
        first = Task(title="重複タスク")
        second = Task(title="重複タスク")
        assert first == second
        app.tasks = [first, second]
        app.on_table_selected(second)

        app.on_delete()

        assert app.tasks == [first]
        assert app.tasks[0] is first
    finally:
        app.destroy()


def test_selected_task_cleared_when_removed_by_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA", "タスクB"])
        app.on_table_selected(next(t for t in app.tasks if t.title == "タスクA"))

        app._merge_extracted_titles(["タスクB"])  # タスクA dropped from the source

        assert app.selected_task is None
    finally:
        app.destroy()
