from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .models import PURPOSE_COLORS, Purpose

COLUMNS = ("name",)


class PurposePanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = ttk.Treeview(
            self, columns=COLUMNS, show="headings", height=3, selectmode="none"
        )
        self.tree.heading("name", text="パーパス")
        self.tree.column("name", anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True)

        for key, (label, hexcolor) in PURPOSE_COLORS.items():
            self.tree.tag_configure(f"purpose_color_{key}", background=hexcolor or "white")

    def set_purposes(self, purposes: list[Purpose]):
        self.tree.delete(*self.tree.get_children())
        for purpose in purposes:
            self.tree.insert(
                "",
                tk.END,
                iid=purpose.name,
                values=(purpose.name,),
                tags=(f"purpose_color_{purpose.color}",),
            )
