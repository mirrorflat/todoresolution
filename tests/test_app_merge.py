from src import app as app_module
from src import db


def test_extract_from_file_merge_behavior(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    md_file = tmp_path / "tasks.md"
    md_file.write_text("⬜ タスクA - 期限 今日\n", encoding="utf-8")
    monkeypatch.setattr(app_module.filedialog, "askopenfilename", lambda **kwargs: str(md_file))

    app = app_module.App()
    app.update_idletasks()

    try:
        # 1) initial extract from file picks up the single task with default values
        app.on_extract_from_file()
        app.update_idletasks()
        assert [t.title for t in app.tasks] == ["タスクA"]
        app.tasks[0].urgency = 8.0
        app.tasks[0].importance = 6.0
        app.tasks[0].resolution = 1.0

        # 2) re-extract with an added task must keep タスクA's edited values
        md_file.write_text("⬜ タスクA - 期限 今日\n⬜ タスクB - 期限 今日\n", encoding="utf-8")
        app.on_extract_from_file()
        app.update_idletasks()
        titles = {t.title: t for t in app.tasks}
        assert set(titles) == {"タスクA", "タスクB"}
        assert (
            titles["タスクA"].urgency,
            titles["タスクA"].importance,
            titles["タスクA"].resolution,
        ) == (8.0, 6.0, 1.0)
        assert titles["タスクB"].urgency == 5.0  # default, untouched
    finally:
        app.destroy()


def test_extract_from_file_no_selection_is_noop(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(app_module.filedialog, "askopenfilename", lambda **kwargs: "")

    app = app_module.App()
    app.update_idletasks()

    try:
        app.on_extract_from_file()
        app.update_idletasks()
        assert app.tasks == []
    finally:
        app.destroy()


def test_extract_merge_behavior(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(
        app_module, "fetch_today_digest_body", lambda: "⬜ タスクA - 期限 今日\n"
    )
    app = app_module.App()
    app.update_idletasks()

    try:
        # 1) initial extract picks up the single task with default values
        app.on_extract()
        app.update_idletasks()
        assert [t.title for t in app.tasks] == ["タスクA"]
        app.tasks[0].urgency = 8.0
        app.tasks[0].importance = 6.0
        app.tasks[0].resolution = 1.0

        # 2) re-extract with an added task must keep タスクA's edited values
        monkeypatch.setattr(
            app_module,
            "fetch_today_digest_body",
            lambda: "⬜ タスクA - 期限 今日\n⬜ タスクB - 期限 今日\n",
        )
        app.on_extract()
        app.update_idletasks()
        titles = {t.title: t for t in app.tasks}
        assert set(titles) == {"タスクA", "タスクB"}
        assert (titles["タスクA"].urgency, titles["タスクA"].importance, titles["タスクA"].resolution) == (
            8.0,
            6.0,
            1.0,
        )
        assert titles["タスクB"].urgency == 5.0  # default, untouched

        # 3) re-extract with タスクA removed must drop it
        monkeypatch.setattr(
            app_module, "fetch_today_digest_body", lambda: "⬜ タスクB - 期限 今日\n"
        )
        app.on_extract()
        app.update_idletasks()
        assert [t.title for t in app.tasks] == ["タスクB"]

        # 4) a duplicated title in one extraction must not collide as the
        #    same object (would crash the Treeview on duplicate iid)
        monkeypatch.setattr(
            app_module,
            "fetch_today_digest_body",
            lambda: "⬜ 重複タスク - 期限 今日\n⬜ 重複タスク - 期限 今日\n",
        )
        app.on_extract()
        app.update_idletasks()
        assert len(app.tasks) == 2
        assert app.tasks[0] is not app.tasks[1]

        # re-extracting the same duplicated body again must still not crash
        app.on_extract()
        app.update_idletasks()
        assert len(app.tasks) == 2

        # 5) Reset must put every task's (importance, urgency) back to (5, 5)
        #    without touching resolution
        for task in app.tasks:
            task.importance = 9.0
            task.urgency = 1.0
            task.resolution = 3.0
        app.on_reset()
        app.update_idletasks()
        for task in app.tasks:
            assert task.importance == 5.0
            assert task.urgency == 5.0
            assert task.resolution == 3.0

        # 6) a bubble's text label must follow its circle when dragged
        #    (regression: Annotation.set_position() moves the offset, not
        #    the anchor, so the label used to stay near its original spot)
        task = app.tasks[0]
        task.importance = 8.0
        task.urgency = 2.0
        app.chart._redraw_task(task)
        circle = app.chart._patches[id(task)]
        label = app.chart._labels[id(task)]
        assert circle.center == (8.0, 2.0)
        assert label.xy == (8.0, 2.0)
    finally:
        app.destroy()
