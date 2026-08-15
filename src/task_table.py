from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .models import Task

COLUMNS = ("score", "importance", "urgency", "resolution", "title")
HEADINGS = {
    "score": "総合評価",
    "importance": "重要度",
    "urgency": "緊急度",
    "resolution": "解像度",
    "title": "タスク名",
}
WIDTHS = {
    "score": 80,
    "importance": 60,
    "urgency": 60,
    "resolution": 60,
    "title": 220,
}


class TaskTable(tk.Frame):
    def __init__(self, parent, on_select=None):
        super().__init__(parent)
        self._on_select = on_select
        self._tasks: list[Task] = []
        self._iid_to_task: dict[str, Task] = {}
        self._suppress_select_event = False

        self.tree = ttk.Treeview(self, columns=COLUMNS, show="headings", selectmode="browse")
        for col in COLUMNS:
            anchor = "w" if col == "title" else "e"
            self.tree.heading(col, text=HEADINGS[col])
            self.tree.column(col, width=WIDTHS[col], anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self._handle_select)

    def set_tasks(self, tasks: list[Task]):
        self._tasks = tasks
        self.refresh()

    def refresh(self):
        selected_task = self._iid_to_task.get(
            self.tree.selection()[0]
        ) if self.tree.selection() else None

        self._suppress_select_event = True
        self.tree.delete(*self.tree.get_children())
        self._iid_to_task.clear()

        for task in sorted(self._tasks, key=lambda t: t.score, reverse=True):
            iid = str(id(task))
            self._iid_to_task[iid] = task
            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    f"{task.score:.1f}",
                    f"{task.importance:.1f}",
                    f"{task.urgency:.1f}",
                    f"{task.resolution:.1f}",
                    task.title,
                ),
            )

        if selected_task is not None:
            iid = str(id(selected_task))
            if self.tree.exists(iid):
                self.tree.selection_set(iid)
        self._suppress_select_event = False

    def select_task(self, task: Task | None):
        self._suppress_select_event = True
        if task is None:
            self.tree.selection_remove(*self.tree.selection())
        else:
            iid = str(id(task))
            if self.tree.exists(iid):
                self.tree.selection_set(iid)
                self.tree.see(iid)
        self._suppress_select_event = False

    def _handle_select(self, _event):
        if self._suppress_select_event or self._on_select is None:
            return
        selection = self.tree.selection()
        if not selection:
            return
        task = self._iid_to_task.get(selection[0])
        if task is not None:
            self._on_select(task)
