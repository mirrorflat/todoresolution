from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

from . import db
from .bubble_chart import BubbleChart
from .models import Task
from .outlook_reader import MailNotFoundError, fetch_today_digest_body
from .task_parser import parse_top_level_tasks
from .task_table import TaskTable


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("todoresolution")
        self.geometry("1200x700")

        self.tasks: list[Task] = []

        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(button_frame, text="Extract", width=10, command=self.on_extract).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tk.Button(
            button_frame, text="Extract from File", command=self.on_extract_from_file
        ).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(button_frame, text="Reset", width=10, command=self.on_reset).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tk.Button(button_frame, text="Close", width=10, command=self.on_close).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Save", width=10, command=self.on_save).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        self.status_var = tk.StringVar(value="")
        tk.Label(button_frame, textvariable=self.status_var, fg="gray").pack(
            side=tk.LEFT, padx=15
        )

        content = tk.Frame(self)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=65)
        content.columnconfigure(1, weight=35)
        content.rowconfigure(0, weight=1)

        self.chart = BubbleChart(
            content, on_change=self.on_task_changed, on_select=self.on_bubble_selected
        )
        self.chart.grid(row=0, column=0, sticky="nsew")

        self.table = TaskTable(content, on_select=self.on_table_selected)
        self.table.grid(row=0, column=1, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tasks = db.load_tasks()
        if self.tasks:
            self.chart.set_tasks(self.tasks)
            self.table.set_tasks(self.tasks)
            self.status_var.set(f"前回終了時の状態を復元しました({len(self.tasks)} 件)")

    def on_extract(self):
        try:
            body = fetch_today_digest_body()
        except MailNotFoundError as exc:
            messagebox.showerror("Extract", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Extract", f"Outlookからの取得に失敗しました:\n{exc}")
            return

        self._merge_extracted_titles(parse_top_level_tasks(body))

    def on_extract_from_file(self):
        path = filedialog.askopenfilename(
            title="Extract from File",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            body = Path(path).read_text(encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("Extract from File", f"ファイルの読み込みに失敗しました:\n{exc}")
            return

        self._merge_extracted_titles(parse_top_level_tasks(body))

    def _merge_extracted_titles(self, titles: list[str]):
        existing_by_title = {task.title: task for task in self.tasks}
        new_tasks = []
        for title in titles:
            # pop so a duplicate title in this extraction can't bind the same
            # existing Task object twice (would collide as one GUI element)
            task = existing_by_title.pop(title, None)
            new_tasks.append(task if task is not None else Task(title=title))
        self.tasks = new_tasks
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)
        self.status_var.set(f"{len(self.tasks)} 件のタスクを読み込みました")

    def on_reset(self):
        for task in self.tasks:
            task.importance = 5.0
            task.urgency = 5.0
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)

    def on_task_changed(self, _task: Task):
        self.table.refresh()

    def on_bubble_selected(self, task: Task):
        self.table.select_task(task)
        self.chart.highlight(task)

    def on_table_selected(self, task: Task):
        self.chart.highlight(task)

    def on_save(self):
        db.save_tasks(self.tasks)
        self.status_var.set("保存しました")

    def on_close(self):
        db.save_tasks(self.tasks)
        self.destroy()


def main():
    App().mainloop()
