import sys
import sqlite3
from pathlib import Path

from .models import Purpose, Task

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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS purposes (
            name TEXT PRIMARY KEY,
            color TEXT NOT NULL
        )
        """
    )
    # CREATE TABLE IF NOT EXISTS doesn't alter a table that already existed
    # before these columns were introduced, so add them separately.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "done" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN done INTEGER NOT NULL DEFAULT 0")
    if "purpose" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN purpose TEXT")
    return conn


def load_tasks():
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT title, urgency, importance, resolution, done, purpose FROM tasks"
        ).fetchall()
    finally:
        conn.close()
    return [
        Task(
            title=title,
            urgency=urgency,
            importance=importance,
            resolution=resolution,
            done=bool(done),
            purpose=purpose,
        )
        for title, urgency, importance, resolution, done, purpose in rows
    ]


def save_tasks(tasks) -> None:
    conn = _connect()
    try:
        with conn:
            conn.execute("DELETE FROM tasks")
            conn.executemany(
                "INSERT OR REPLACE INTO tasks "
                "(title, urgency, importance, resolution, done, purpose) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (t.title, t.urgency, t.importance, t.resolution, int(t.done), t.purpose)
                    for t in tasks
                ],
            )
    finally:
        conn.close()


def load_purposes() -> list[Purpose]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT name, color FROM purposes").fetchall()
    finally:
        conn.close()
    return [Purpose(name=name, color=color) for name, color in rows]


def save_purposes(purposes: list[Purpose]) -> None:
    conn = _connect()
    try:
        with conn:
            conn.execute("DELETE FROM purposes")
            conn.executemany(
                "INSERT OR REPLACE INTO purposes (name, color) VALUES (?, ?)",
                [(p.name, p.color) for p in purposes],
            )
    finally:
        conn.close()
