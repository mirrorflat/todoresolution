from __future__ import annotations

import tkinter as tk

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from .models import Task, clamp

matplotlib.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

RADIUS_SCALE = 0.2
RADIUS_MIN = 0.15
RADIUS_MAX = 2.0
MOVE_RATIO = 0.6
RESIZE_RATIO = 1.3


def radius_for_resolution(resolution: float) -> float:
    return clamp((10 - resolution) * RADIUS_SCALE, RADIUS_MIN, RADIUS_MAX)


def resolution_for_radius(radius: float) -> float:
    return clamp(10 - radius / RADIUS_SCALE)


class BubbleChart(tk.Frame):
    def __init__(self, parent, on_change=None, on_select=None):
        super().__init__(parent)
        self._tasks: list[Task] = []
        self._patches: dict[int, Circle] = {}
        self._labels: dict[int, object] = {}
        self._on_change = on_change
        self._on_select = on_select
        self._drag_task: Task | None = None
        self._drag_mode: str | None = None

        self.figure = Figure(figsize=(5, 5))
        self.ax = self.figure.add_subplot(111)
        self._setup_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.canvas.mpl_connect("button_release_event", self._on_release)

    def _setup_axes(self):
        self.ax.clear()
        self.ax.set_xlim(10, 0)
        self.ax.set_ylim(10, 0)
        self.ax.set_aspect("equal")
        self.ax.set_xlabel("重要度")
        self.ax.set_ylabel("緊急度")
        self.ax.grid(True, linestyle=":", alpha=0.5)

    def set_tasks(self, tasks: list[Task]):
        # Done tasks are tracked in the table but dropped from the chart entirely.
        self._tasks = [task for task in tasks if not task.done]
        self._patches.clear()
        self._labels.clear()
        self._setup_axes()
        for task in self._tasks:
            self._add_patch(task)
        self.canvas.draw_idle()

    def _add_patch(self, task: Task):
        circle = Circle(
            (task.importance, task.urgency),
            radius_for_resolution(task.resolution),
            facecolor="#4C78A8",
            edgecolor="#2A4A6E",
            alpha=0.6,
            linewidth=1.5,
            picker=True,
        )
        self.ax.add_patch(circle)
        label = self.ax.annotate(
            _truncate(task.title),
            xy=(task.importance, task.urgency),
            xytext=(0, 0),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=8,
        )
        self._patches[id(task)] = circle
        self._labels[id(task)] = label

    def _redraw_task(self, task: Task):
        circle = self._patches.get(id(task))
        label = self._labels.get(id(task))
        if circle is None:
            return
        circle.center = (task.importance, task.urgency)
        circle.radius = radius_for_resolution(task.resolution)
        if label is not None:
            # label.xy is the annotated anchor point; set_position() would instead
            # move the offset-points text position, leaving the anchor behind.
            label.xy = (task.importance, task.urgency)
        self.canvas.draw_idle()

    def highlight(self, task: Task | None):
        for key, circle in self._patches.items():
            circle.set_linewidth(3.0 if task is not None and key == id(task) else 1.5)
            circle.set_edgecolor("#E45756" if task is not None and key == id(task) else "#2A4A6E")
        self.canvas.draw_idle()

    def _find_target(self, x: float, y: float):
        best = None
        best_dist = None
        for task in self._tasks:
            radius = radius_for_resolution(task.resolution)
            dist = ((x - task.importance) ** 2 + (y - task.urgency) ** 2) ** 0.5
            if radius <= 0 or dist / radius > RESIZE_RATIO:
                continue
            if best_dist is None or dist < best_dist:
                best = task
                best_dist = dist
        if best is None:
            return None, None
        radius = radius_for_resolution(best.resolution)
        mode = "move" if best_dist <= radius * MOVE_RATIO else "resize"
        return best, mode

    def _on_press(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        task, mode = self._find_target(event.xdata, event.ydata)
        self._drag_task = task
        self._drag_mode = mode
        if task is not None and self._on_select is not None:
            self._on_select(task)

    def _on_motion(self, event):
        if self._drag_task is None or event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        task = self._drag_task
        if self._drag_mode == "move":
            task.importance = clamp(event.xdata)
            task.urgency = clamp(event.ydata)
        elif self._drag_mode == "resize":
            dist = ((event.xdata - task.importance) ** 2 + (event.ydata - task.urgency) ** 2) ** 0.5
            radius = clamp(dist, RADIUS_MIN, RADIUS_MAX)
            task.resolution = resolution_for_radius(radius)
        self._redraw_task(task)
        if self._on_change is not None:
            self._on_change(task)

    def _on_release(self, event):
        self._drag_task = None
        self._drag_mode = None


def _truncate(title: str, limit: int = 10) -> str:
    return title if len(title) <= limit else title[: limit - 1] + "…"
