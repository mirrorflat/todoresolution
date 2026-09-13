import tkinter as tk

from src.models import PURPOSE_COLORS, Purpose
from src.purpose_panel import PurposePanel


def test_set_purposes_shows_each_purpose_with_its_color():
    root = tk.Tk()
    try:
        panel = PurposePanel(root)
        panel.set_purposes([Purpose(name="健康", color="green"), Purpose(name="仕事", color="none")])

        assert list(panel.tree.get_children()) == ["健康", "仕事"]
        assert panel.tree.item("健康", "values") == ("健康",)

        health_tag = panel.tree.item("健康", "tags")[0]
        assert str(panel.tree.tag_configure(health_tag, "background")) == PURPOSE_COLORS["green"][1]

        work_tag = panel.tree.item("仕事", "tags")[0]
        # "none" has no hex value, so the tag falls back to a plain white background.
        assert str(panel.tree.tag_configure(work_tag, "background")) == "white"
    finally:
        root.destroy()


def test_set_purposes_clears_previous_rows():
    root = tk.Tk()
    try:
        panel = PurposePanel(root)
        panel.set_purposes([Purpose(name="健康", color="green")])
        panel.set_purposes([Purpose(name="仕事", color="blue")])

        assert list(panel.tree.get_children()) == ["仕事"]
    finally:
        root.destroy()
