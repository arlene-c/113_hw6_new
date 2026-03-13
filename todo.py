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


def list_tasks(status=None, priority=None, sort="smart", show_completed=True):
    """
    sort options:
      smart     — in_progress first, then pending, then done; priority desc; due date asc
      priority  — highest priority first
      due       — soonest due date first (nulls last)
      created   — newest first
      status    — grouped by status
    """
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if priority is not None:
        query += " AND priority = ?"
        params.append(priority)
    if not show_completed:
        query += " AND status != 'completed'"

    ORDER_CLAUSES = {
        "smart":    ("CASE status WHEN 'in_progress' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END, "
                     "priority DESC NULLS LAST, "
                     "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC"),
        "priority": ("priority DESC NULLS LAST, "
                     "CASE status WHEN 'in_progress' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END"),
        "due":      ("CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC, "
                     "priority DESC NULLS LAST"),
        "created":  "created_at DESC",
        "status":   ("CASE status WHEN 'in_progress' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END, "
                     "priority DESC NULLS LAST"),
    }

    query += f" ORDER BY {ORDER_CLAUSES.get(sort, ORDER_CLAUSES['smart'])}"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        print("  No tasks found.")
        return

    _print_table(rows)



def get_task(task_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        print(f"  ❌ No task with ID #{task_id}")
        return
    _print_table([row])


def update_task(task_id, title=None, description=None, status=None, priority=None, due_date=None):
    fields, params = [], []
    if title       is not None: fields.append("title = ?");       params.append(title)
    if description is not None: fields.append("description = ?"); params.append(description)
    if status      is not None: fields.append("status = ?");      params.append(status)
    if priority    is not None: fields.append("priority = ?");    params.append(priority)
    if due_date    is not None: fields.append("due_date = ?");    params.append(due_date)

    if not fields:
        print("  Nothing to update — use flags like -t, -s, -p, --due")
        return

    params.append(task_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
        changes = conn.total_changes
        conn.commit()

    print(f"  ✏️  Task #{task_id} updated." if changes else f"  ❌ No task with ID #{task_id}")

def delete_task(task_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        changes = conn.total_changes
        conn.commit()
    print(f"  🗑️  Task #{task_id} deleted." if changes else f"  ❌ No task with ID #{task_id}")


def complete_task(task_id):
    update_task(task_id, status="completed")
