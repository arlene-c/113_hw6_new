#!/usr/bin/env python3
"""
todo.py — Interactive SQLite To-Do List
Run once with: python todo.py
Then type commands at the prompt. Type 'help' for usage, 'quit' to exit.
"""

import sqlite3
import shlex
import sys

DB_PATH = "todo.db"

# ─────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                status      TEXT    NOT NULL DEFAULT 'pending'
                                    CHECK(status IN ('pending', 'in_progress', 'completed')),
                priority    INTEGER CHECK(priority BETWEEN 1 AND 5),
                created_at  DATETIME NOT NULL DEFAULT (datetime('now')),
                due_date    DATETIME
            )
        """)
        conn.commit()


# CRUD: Create Operation 

def create_task(title, description=None, priority=None, due_date=None):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
            (title, description, priority, due_date)
        )
        conn.commit()
        task_id = cursor.lastrowid
    print(f"  ✅ Task #{task_id} created: \"{title}\"")

