import sys
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from . import db
from .bubble_chart import BubbleChart
from .models import PURPOSE_COLORS, Purpose, Task
from .outlook_reader import MailNotFoundError, fetch_today_digest_body
from .purpose_panel import PurposePanel
from .task_parser import parse_onenote_print_tasks, parse_top_level_tasks
from .task_table import TaskTable

MAX_PURPOSES = 4

if getattr(sys, "frozen", False):
    # PyInstaller --onefile extracts bundled data files (added via --add-data)
    # into this per-run temp dir, unlike sys.executable's own (persistent) folder.
    _ICON_PATH = Path(sys._MEIPASS) / "icon.ico"
else:
    _ICON_PATH = Path(__file__).resolve().parent.parent / "icon.ico"


def _underline_index(label: str) -> int:
    # Labels are written as e.g. "Delete(L)"; the mnemonic is the character
    # right after the last "(" so Alt+L (or, via a menu, Alt→T→L) triggers it.
    return label.rfind("(") + 1


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("todoresolution")
        self.geometry("1200x700")
        if _ICON_PATH.exists():
            # --icon on the PyInstaller build only sets the .exe's own icon
            # (Explorer/taskbar); the window's title-bar icon is Tk's default
            # feather unless set explicitly here.
            self.iconbitmap(default=str(_ICON_PATH))

        self.tasks: list[Task] = []
        self.selected_task: Task | None = None
        self.purposes: list[Purpose] = []

        self._build_menu()

        status_frame = tk.Frame(self)
        status_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.status_var = tk.StringVar(value="")
        tk.Label(status_frame, textvariable=self.status_var, fg="gray").pack(side=tk.LEFT)

        content = tk.Frame(self)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=70)
        content.columnconfigure(1, weight=30)
        content.rowconfigure(0, weight=0)
        content.rowconfigure(1, weight=1)

        self.purpose_panel = PurposePanel(content)
        self.purpose_panel.grid(row=0, column=1, sticky="new")

        self.chart = BubbleChart(
            content, on_change=self.on_task_changed, on_select=self.on_bubble_selected
        )
        self.chart.grid(row=0, column=0, rowspan=2, sticky="nsew")

        self.table = TaskTable(content, on_select=self.on_table_selected)
        self.table.grid(row=1, column=1, sticky="nsew", pady=(8, 0))

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.purposes = db.load_purposes()
        self.purpose_panel.set_purposes(self.purposes)
        self.table.set_purposes(self.purposes)
        self._refresh_purpose_menus()

        self.tasks = db.load_tasks()
        if self.tasks:
            self.chart.set_tasks(self.tasks)
            self.table.set_tasks(self.tasks)
            self.status_var.set(f"前回終了時の状態を復元しました({len(self.tasks)} 件)")

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        task_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(
            label="タスク(T)", menu=task_menu, underline=_underline_index("タスク(T)")
        )
        for label, command in (
            ("Add(A)", self.on_add),
            ("Done(D)", self.on_done),
            ("Undone(U)", self.on_undone),
        ):
            task_menu.add_command(label=label, underline=_underline_index(label), command=command)
        task_menu.add_separator()
        task_menu.add_command(
            label="Delete(L)", underline=_underline_index("Delete(L)"), command=self.on_delete
        )
        task_menu.add_separator()
        self._task_purpose_menu = tk.Menu(task_menu, tearoff=0)
        task_menu.add_cascade(
            label="パーパス(P)",
            menu=self._task_purpose_menu,
            underline=_underline_index("パーパス(P)"),
        )

        purpose_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(
            label="パーパス(P)", menu=purpose_menu, underline=_underline_index("パーパス(P)")
        )
        purpose_menu.add_command(
            label="Create(C)", underline=_underline_index("Create(C)"), command=self.on_purpose_create
        )
        self._purpose_delete_menu = tk.Menu(purpose_menu, tearoff=0)
        purpose_menu.add_cascade(
            label="Delete(L)",
            menu=self._purpose_delete_menu,
            underline=_underline_index("Delete(L)"),
        )

        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(
            label="管理(M)", menu=manage_menu, underline=_underline_index("管理(M)")
        )
        for label, command in (
            ("Extract(E)", self.on_extract),
            ("Extract from File(F)", self.on_extract_from_file),
        ):
            manage_menu.add_command(
                label=label, underline=_underline_index(label), command=command
            )
        manage_menu.add_separator()
        for label, command in (
            ("Reset(R)", self.on_reset),
            ("Save(S)", self.on_save),
            ("Close(C)", self.on_close),
        ):
            manage_menu.add_command(
                label=label, underline=_underline_index(label), command=command
            )

    def _refresh_purpose_menus(self):
        self._task_purpose_menu.delete(0, tk.END)
        self._task_purpose_menu.add_command(
            label="なし", command=lambda: self.on_assign_purpose(None)
        )
        for purpose in self.purposes:
            self._task_purpose_menu.add_command(
                label=purpose.name,
                command=lambda name=purpose.name: self.on_assign_purpose(name),
            )

        self._purpose_delete_menu.delete(0, tk.END)
        if not self.purposes:
            self._purpose_delete_menu.add_command(label="(パーパスがありません)", state=tk.DISABLED)
        for purpose in self.purposes:
            self._purpose_delete_menu.add_command(
                label=purpose.name,
                command=lambda name=purpose.name: self.on_purpose_delete(name),
            )

    def on_purpose_create(self):
        if len(self.purposes) >= MAX_PURPOSES:
            messagebox.showinfo(
                "Create", f"パーパスは{MAX_PURPOSES}つまでしか作成できません。"
            )
            return
        name = simpledialog.askstring("Create", "パーパス名を入力してください:", parent=self)
        if name is None:
            return
        name = name.strip()
        if not name:
            return
        if any(p.name == name for p in self.purposes):
            messagebox.showerror("Create", f"「{name}」は既に存在します。")
            return
        color = self._ask_purpose_color()
        if color is None:
            return
        self.purposes.append(Purpose(name=name, color=color))
        self.purpose_panel.set_purposes(self.purposes)
        self.table.set_purposes(self.purposes)
        self._refresh_purpose_menus()

    def on_purpose_delete(self, name: str):
        if not messagebox.askyesno("Delete", f"パーパス「{name}」を削除しますか?"):
            return
        self.purposes = [p for p in self.purposes if p.name != name]
        for task in self.tasks:
            if task.purpose == name:
                task.purpose = None
        self.purpose_panel.set_purposes(self.purposes)
        self.table.set_purposes(self.purposes)
        self._refresh_purpose_menus()

    def on_assign_purpose(self, name: str | None):
        if self.selected_task is None:
            messagebox.showinfo(
                "パーパス", "パーパスを設定するタスクをテーブルまたはバブルチャートで選択してください。"
            )
            return
        self.selected_task.purpose = name
        self.table.set_tasks(self.tasks)

    def _ask_purpose_color(self) -> str | None:
        dialog = tk.Toplevel(self)
        dialog.title("色を選択")
        dialog.transient(self)
        dialog.resizable(False, False)
        result: dict[str, str | None] = {"color": None}

        def choose(key: str):
            result["color"] = key
            dialog.destroy()

        for i, (key, (label, hexcolor)) in enumerate(PURPOSE_COLORS.items()):
            tk.Button(
                dialog,
                text=label,
                width=6,
                bg=hexcolor or "white",
                command=lambda k=key: choose(k),
            ).grid(row=i // 4, column=i % 4, padx=4, pady=4)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.grab_set()
        self.wait_window(dialog)
        return result["color"]

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

        self._merge_extracted_titles(parse_onenote_print_tasks(body))

    def _merge_extracted_titles(self, titles: list[str]):
        existing_by_title = {task.title: task for task in self.tasks}
        new_tasks = []
        for title in titles:
            # pop so a duplicate title in this extraction can't bind the same
            # existing Task object twice (would collide as one GUI element)
            task = existing_by_title.pop(title, None)
            new_tasks.append(task if task is not None else Task(title=title))
        self.tasks = new_tasks
        # identity check: Task's dataclass __eq__ compares field values, so two
        # untouched duplicate-titled tasks would otherwise look interchangeable
        if not any(t is self.selected_task for t in self.tasks):
            self.selected_task = None
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)
        self.status_var.set(f"{len(self.tasks)} 件のタスクを読み込みました")

    def on_add(self):
        title = simpledialog.askstring("Add", "タスク名を入力してください:", parent=self)
        if title is None:
            return
        title = title.strip()
        if not title:
            return
        task = Task(title=title)
        self.tasks.append(task)
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)

    def on_done(self):
        if self.selected_task is None:
            messagebox.showinfo(
                "Done", "Done にするタスクをテーブルまたはバブルチャートで選択してください。"
            )
            return
        self.selected_task.done = True
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)

    def on_undone(self):
        if self.selected_task is None:
            messagebox.showinfo(
                "Undone", "Undone にするタスクをテーブルで選択してください。"
            )
            return
        self.selected_task.done = False
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)

    def on_reset(self):
        for task in self.tasks:
            task.importance = 5.0
            task.urgency = 5.0
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)

    def on_task_changed(self, _task: Task):
        self.table.refresh()

    def on_bubble_selected(self, task: Task):
        self.selected_task = task
        self.table.select_task(task)
        self.chart.highlight(task)

    def on_table_selected(self, task: Task):
        self.selected_task = task
        self.chart.highlight(task)

    def on_delete(self):
        if self.selected_task is None:
            messagebox.showinfo(
                "Delete", "削除するタスクをテーブルまたはバブルチャートで選択してください。"
            )
            return
        if not messagebox.askyesno("Delete", f"「{self.selected_task.title}」を削除しますか?"):
            return
        # identity-based filter: Task's dataclass __eq__ compares field values,
        # so list.remove() could drop the wrong duplicate-titled task instead
        self.tasks = [t for t in self.tasks if t is not self.selected_task]
        self.selected_task = None
        self.chart.set_tasks(self.tasks)
        self.table.set_tasks(self.tasks)

    def on_save(self):
        db.save_tasks(self.tasks)
        db.save_purposes(self.purposes)
        self.status_var.set("保存しました")

    def on_close(self):
        db.save_tasks(self.tasks)
        db.save_purposes(self.purposes)
        self.destroy()


def main():
    App().mainloop()
