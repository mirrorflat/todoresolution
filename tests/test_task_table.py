import tkinter as tk

from src.models import PURPOSE_COLORS, Purpose, Task
from src.task_table import TaskTable


def test_done_tasks_sort_below_active_tasks_by_score():
    root = tk.Tk()
    try:
        table = TaskTable(root)
        low_score_active = Task(title="低スコア", urgency=1.0, importance=1.0, resolution=10.0)
        high_score_done = Task(
            title="高スコアDone", urgency=10.0, importance=10.0, resolution=0.0, done=True
        )
        high_score_active = Task(title="高スコア", urgency=10.0, importance=10.0, resolution=0.0)

        table.set_tasks([low_score_active, high_score_done, high_score_active])

        assert list(table.tree.get_children()) == [
            str(id(high_score_active)),
            str(id(low_score_active)),
            str(id(high_score_done)),
        ]
    finally:
        root.destroy()


def test_done_task_keeps_its_score_values_untouched():
    root = tk.Tk()
    try:
        table = TaskTable(root)
        task = Task(title="タスク", urgency=7.0, importance=6.0, resolution=1.0, done=True)
        table.set_tasks([task])

        values = table.tree.item(str(id(task)), "values")
        assert values[0] == f"{task.score:.1f}"
        assert values[1] == f"{task.importance:.1f}"
        assert values[2] == f"{task.urgency:.1f}"
        assert values[3] == f"{task.resolution:.1f}"
    finally:
        root.destroy()


def test_done_row_has_done_tag_and_title_text_is_unmodified():
    root = tk.Tk()
    try:
        table = TaskTable(root)
        done_task = Task(title="完了タスク", done=True)
        active_task = Task(title="通常タスク", done=False)
        table.set_tasks([done_task, active_task])

        assert table.tree.item(str(id(done_task)), "tags") == ("done",)
        assert not table.tree.item(str(id(active_task)), "tags")

        # The strikethrough is a real overstrike font on the "done" tag, not
        # a change to the displayed text, so titles must render unmodified.
        done_title = table.tree.item(str(id(done_task)), "values")[-1]
        active_title = table.tree.item(str(id(active_task)), "values")[-1]
        assert done_title == done_task.title
        assert active_title == active_task.title
    finally:
        root.destroy()


def test_done_tag_font_has_overstrike_enabled():
    root = tk.Tk()
    try:
        table = TaskTable(root)
        font_name = table.tree.tag_configure("done", "font")
        assert font_name
        import tkinter.font as tkfont

        assert tkfont.Font(font=font_name).actual("overstrike") == 1
    finally:
        root.destroy()


def test_task_with_purpose_gets_purpose_colored_row():
    root = tk.Tk()
    try:
        table = TaskTable(root)
        table.set_purposes([Purpose(name="健康", color="green")])
        task = Task(title="タスクA", purpose="健康")
        table.set_tasks([task])

        tags = table.tree.item(str(id(task)), "tags")
        assert len(tags) == 1
        assert str(table.tree.tag_configure(tags[0], "background")) == PURPOSE_COLORS["green"][1]
    finally:
        root.destroy()


def test_done_purpose_task_shows_done_styling_not_purpose_color():
    # Done state must win visually over a purpose color assignment.
    root = tk.Tk()
    try:
        table = TaskTable(root)
        table.set_purposes([Purpose(name="健康", color="green")])
        task = Task(title="タスクA", purpose="健康", done=True)
        table.set_tasks([task])

        assert table.tree.item(str(id(task)), "tags") == ("done",)
    finally:
        root.destroy()


def test_task_with_purpose_removed_after_purpose_cleared_falls_back_to_no_tag():
    root = tk.Tk()
    try:
        table = TaskTable(root)
        table.set_purposes([Purpose(name="健康", color="green")])
        task = Task(title="タスクA", purpose="健康")
        table.set_tasks([task])

        # Simulate the purpose having been deleted app-side.
        task.purpose = None
        table.set_purposes([])

        assert not table.tree.item(str(id(task)), "tags")
    finally:
        root.destroy()
