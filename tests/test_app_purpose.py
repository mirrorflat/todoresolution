from src import app as app_module
from src import db
from src.models import Purpose


def test_purpose_create_adds_purpose_with_chosen_color(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.simpledialog, "askstring", lambda *a, **k: "健康")

    app = app_module.App()
    app.update_idletasks()
    try:
        monkeypatch.setattr(app, "_ask_purpose_color", lambda: "green")
        app.on_purpose_create()

        assert [p.name for p in app.purposes] == ["健康"]
        assert app.purposes[0].color == "green"
    finally:
        app.destroy()


def test_purpose_create_rejects_duplicate_name(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    shown = []
    monkeypatch.setattr(app_module.messagebox, "showerror", lambda *a, **k: shown.append(a))
    monkeypatch.setattr(app_module.simpledialog, "askstring", lambda *a, **k: "健康")

    app = app_module.App()
    app.update_idletasks()
    try:
        app.purposes = [Purpose(name="健康", color="red")]
        app.on_purpose_create()

        assert len(shown) == 1
        assert len(app.purposes) == 1
    finally:
        app.destroy()


def test_purpose_create_blocked_beyond_max(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    shown = []
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: shown.append(a))

    app = app_module.App()
    app.update_idletasks()
    try:
        app.purposes = [Purpose(name=f"目的{i}") for i in range(app_module.MAX_PURPOSES)]
        app.on_purpose_create()

        assert len(shown) == 1
        assert len(app.purposes) == app_module.MAX_PURPOSES
    finally:
        app.destroy()


def test_purpose_delete_clears_it_from_assigned_tasks(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.messagebox, "askyesno", lambda *a, **k: True)

    app = app_module.App()
    app.update_idletasks()
    try:
        app.purposes = [Purpose(name="健康", color="green")]
        app._merge_extracted_titles(["タスクA"])
        app.tasks[0].purpose = "健康"

        app.on_purpose_delete("健康")

        assert app.purposes == []
        assert app.tasks[0].purpose is None
    finally:
        app.destroy()


def test_assign_purpose_without_selection_shows_info(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    shown = []
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: shown.append(a))

    app = app_module.App()
    app.update_idletasks()
    try:
        app.on_assign_purpose("健康")
        assert len(shown) == 1
    finally:
        app.destroy()


def test_assign_purpose_sets_selected_task(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app.purposes = [Purpose(name="健康", color="green")]
        app._merge_extracted_titles(["タスクA"])
        app.on_table_selected(app.tasks[0])

        app.on_assign_purpose("健康")
        assert app.tasks[0].purpose == "健康"

        app.on_assign_purpose(None)
        assert app.tasks[0].purpose is None
    finally:
        app.destroy()


def test_purposes_survive_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    app = app_module.App()
    app.update_idletasks()
    try:
        app.purposes = [Purpose(name="健康", color="green"), Purpose(name="仕事", color="blue")]
        app._merge_extracted_titles(["タスクA"])
        app.tasks[0].purpose = "健康"
        app.on_save()
    finally:
        app.destroy()

    reloaded_purposes = {p.name: p for p in db.load_purposes()}
    assert set(reloaded_purposes) == {"健康", "仕事"}
    assert reloaded_purposes["健康"].color == "green"

    reloaded_tasks = db.load_tasks()
    assert reloaded_tasks[0].purpose == "健康"
