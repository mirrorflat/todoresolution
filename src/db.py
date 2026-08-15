import sys
import sqlite3
from pathlib import Path

from .models import Task

if getattr(sys, "frozen", False):
    # PyInstaller --onefile extracts modules into a fresh temp dir per run,
    # so __file__-relative paths would silently discard saved data on exit.
    _BASE_DIR = Path(sys.executable).resolve().parent
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = _BASE_DIR / "todoresolution.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            title TEXT PRIMARY KEY,
            urgency REAL NOT NULL,
            importance REAL NOT NULL,
            resolution REAL NOT NULL
        )
        """
    )
    return conn


def load_tasks():
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT title, urgency, importance, resolution FROM tasks"
        ).fetchall()
    finally:
        conn.close()
    return [
        Task(title=title, urgency=urgency, importance=importance, resolution=resolution)
        for title, urgency, importance, resolution in rows
    ]


def save_tasks(tasks) -> None:
    conn = _connect()
    try:
        with conn:
            conn.execute("DELETE FROM tasks")
            conn.executemany(
                "INSERT OR REPLACE INTO tasks (title, urgency, importance, resolution) "
                "VALUES (?, ?, ?, ?)",
                [(t.title, t.urgency, t.importance, t.resolution) for t in tasks],
            )
    finally:
        conn.close()
