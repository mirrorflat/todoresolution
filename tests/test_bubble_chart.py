import tkinter as tk

from src.bubble_chart import BubbleChart
from src.models import Task


class _FakeEvent:
    def __init__(self, inaxes, xdata, ydata):
        self.inaxes = inaxes
        self.xdata = xdata
        self.ydata = ydata


def test_done_tasks_are_dropped_from_the_chart():
    root = tk.Tk()
    try:
        chart = BubbleChart(root)
        active_task = Task(title="通常タスク")
        done_task = Task(title="完了タスク", done=True)

        chart.set_tasks([active_task, done_task])

        assert id(active_task) in chart._patches
        assert id(done_task) not in chart._patches
        assert chart._tasks == [active_task]
    finally:
        root.destroy()


def test_axes_stay_within_the_original_0_to_10_range():
    root = tk.Tk()
    try:
        chart = BubbleChart(root)
        assert chart.ax.get_xlim() == (10.0, 0.0)
        assert chart.ax.get_ylim() == (10.0, 0.0)
    finally:
        root.destroy()


def test_dragging_clamps_both_axes_to_10():
    root = tk.Tk()
    try:
        chart = BubbleChart(root)
        task = Task(title="タスク")
        chart.set_tasks([task])

        chart._drag_task = task
        chart._drag_mode = "move"
        chart._on_motion(_FakeEvent(chart.ax, 25.0, 15.0))

        assert task.importance == 10.0
        assert task.urgency == 10.0
    finally:
        root.destroy()
