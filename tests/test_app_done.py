from src import app as app_module
from src import db


def test_done_without_selection_shows_info_and_does_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    shown = []
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: shown.append(a))

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA"])
        app.on_done()
        assert len(shown) == 1
        assert app.tasks[0].done is False
    finally:
        app.destroy()


def test_done_marks_task_and_removes_it_from_the_chart(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA", "タスクB"])
        target = next(t for t in app.tasks if t.title == "タスクA")
        app.on_table_selected(target)

        app.on_done()

        assert target.done is True
        # Values are preserved, only its done flag changes.
        assert [t.title for t in app.tasks] == ["タスクA", "タスクB"]
        assert id(target) not in app.chart._patches
    finally:
        app.destroy()


def test_undone_restores_task_to_the_chart(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA"])
        target = app.tasks[0]
        app.on_table_selected(target)
        app.on_done()
        assert target.done is True

        app.on_undone()

        assert target.done is False
        assert id(target) in app.chart._patches
    finally:
        app.destroy()


def test_undone_without_selection_shows_info(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    shown = []
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: shown.append(a))

    app = app_module.App()
    app.update_idletasks()
    try:
        app.on_undone()
        assert len(shown) == 1
    finally:
        app.destroy()


def test_done_task_values_survive_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app._merge_extracted_titles(["タスクA"])
        app.tasks[0].urgency = 9.0
        app.on_table_selected(app.tasks[0])
        app.on_done()
        app.on_save()
    finally:
        app.destroy()

    reloaded = db.load_tasks()
    assert len(reloaded) == 1
    assert reloaded[0].title == "タスクA"
    assert reloaded[0].urgency == 9.0
    assert reloaded[0].done is True
