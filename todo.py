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


# ─────────────────────────────────────────────
# CRUD operations
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────

STATUS_ICON    = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
PRIORITY_LABEL = {1: "▪ Low", 2: "▫ Low+", 3: "◆ Med", 4: "◈ High", 5: "★ Urgent"}


def _print_table(rows):
    col_widths = [4, 32, 14, 9, 10, 10]
    headers    = ["ID", "Title", "Status", "Pri", "Due", "Created"]
    sep        = "─" * (sum(col_widths) + len(col_widths) * 3 + 1)

    print()
    print(sep)
    print(_row_fmt(headers, col_widths))
    print(sep)

    for row in rows:
        due          = row["due_date"][:10]  if row["due_date"]    else "—"
        created      = row["created_at"][:10] if row["created_at"] else "—"
        status_str   = f"{STATUS_ICON.get(row['status'], '')} {row['status']}"
        priority_str = PRIORITY_LABEL.get(row["priority"], "—") if row["priority"] else "—"
        title_str    = row["title"][:30] + ("…" if len(row["title"]) > 30 else "")

        print(_row_fmt([str(row["id"]), title_str, status_str, priority_str, due, created], col_widths))

        if row["description"]:
            desc = row["description"]
            print(f"         ↳ {desc[:70]}{'…' if len(desc) > 70 else ''}")

    print(sep)
    print(f"  {len(rows)} task(s)\n")


def _row_fmt(cells, widths):
    parts = [f" {str(c):<{w}} " for c, w in zip(cells, widths)]
    return "│".join([""] + parts + [""])


# ─────────────────────────────────────────────
# Command parsing
# ─────────────────────────────────────────────

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║                 📋  TO-DO LIST — COMMANDS                    ║
╠══════════════════════════════════════════════════════════════╣
║  add  <title> [options]         Add a new task               ║
║    -d  "description"            Optional details             ║
║    -p  1-5                      Priority (5 = urgent)        ║
║    --due YYYY-MM-DD             Due date                     ║
║                                                              ║
║  list [options]                 List tasks                   ║
║    --sort smart|priority|due|created|status                  ║
║           smart    = active first, then priority, then due   ║
║           priority = highest priority first                  ║
║           due      = soonest deadline first                  ║
║           created  = newest first                            ║
║           status   = grouped by status                       ║
║    --status pending|in_progress|completed  (filter)          ║
║    --priority 1-5               Filter by exact priority     ║
║    --hide-done                  Hide completed tasks         ║
║                                                              ║
║  get  <id>                      Show one task                ║
║  complete <id>                  Mark task as completed       ║
║  update <id> [options]          Edit a task                  ║
║    -t  "new title"                                           ║
║    -d  "new description"                                     ║
║    -s  pending|in_progress|completed                         ║
║    -p  1-5                                                   ║
║    --due YYYY-MM-DD                                          ║
║  delete <id>                    Delete a task                ║
║                                                              ║
║  help                           Show this help               ║
║  quit / exit                    Exit the app                 ║
╚══════════════════════════════════════════════════════════════╝
"""

VALID_STATUSES = {"pending", "in_progress", "completed"}
VALID_SORTS    = {"smart", "priority", "due", "created", "status"}


def parse_flags(tokens):
    positional, flags = [], {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-d", "--description") and i + 1 < len(tokens):
            flags["description"] = tokens[i + 1]; i += 2
        elif tok in ("-t", "--title") and i + 1 < len(tokens):
            flags["title"] = tokens[i + 1]; i += 2
        elif tok in ("-p", "--priority") and i + 1 < len(tokens):
            flags["priority"] = tokens[i + 1]; i += 2
        elif tok in ("-s", "--status") and i + 1 < len(tokens):
            flags["status"] = tokens[i + 1]; i += 2
        elif tok == "--due" and i + 1 < len(tokens):
            flags["due_date"] = tokens[i + 1]; i += 2
        elif tok == "--sort" and i + 1 < len(tokens):
            flags["sort"] = tokens[i + 1]; i += 2
        elif tok == "--hide-done":
            flags["hide_done"] = True; i += 1
        else:
            positional.append(tok); i += 1
    return positional, flags


def validate_priority(val):
    try:
        p = int(val)
        if 1 <= p <= 5:
            return p
    except (TypeError, ValueError):
        pass
    print(f"  ⚠️  Priority must be 1–5, got: {val!r}")
    return None


def dispatch(line):
    try:
        tokens = shlex.split(line)
    except ValueError as e:
        print(f"  ⚠️  Parse error: {e}")
        return

    if not tokens:
        return

    cmd, rest = tokens[0].lower(), tokens[1:]

    if cmd in ("quit", "exit", "q"):
        print("  Bye!")
        sys.exit(0)

    elif cmd == "help":
        print(HELP_TEXT)

    elif cmd == "add":
        positional, flags = parse_flags(rest)
        if not positional:
            print("  ⚠️  Usage: add <title> [-d description] [-p 1-5] [--due YYYY-MM-DD]")
            return
        title    = " ".join(positional)
        priority = validate_priority(flags["priority"]) if "priority" in flags else None
        if "priority" in flags and priority is None:
            return
        create_task(title, flags.get("description"), priority, flags.get("due_date"))

    elif cmd == "list":
        _, flags = parse_flags(rest)
        sort = flags.get("sort", "smart")
        if sort not in VALID_SORTS:
            print(f"  ⚠️  --sort must be one of: {', '.join(VALID_SORTS)}")
            return
        status = flags.get("status")
        if status and status not in VALID_STATUSES:
            print(f"  ⚠️  --status must be one of: {', '.join(VALID_STATUSES)}")
            return
        priority = validate_priority(flags["priority"]) if "priority" in flags else None
        if "priority" in flags and priority is None:
            return
        list_tasks(status=status, priority=priority, sort=sort,
                   show_completed=not flags.get("hide_done", False))

    elif cmd == "get":
        if not rest:
            print("  ⚠️  Usage: get <id>"); return
        try:
            get_task(int(rest[0]))
        except ValueError:
            print("  ⚠️  ID must be a number")

    elif cmd == "complete":
        if not rest:
            print("  ⚠️  Usage: complete <id>"); return
        try:
            complete_task(int(rest[0]))
        except ValueError:
            print("  ⚠️  ID must be a number")

    elif cmd == "update":
        if not rest:
            print("  ⚠️  Usage: update <id> [-t title] [-d desc] [-s status] [-p 1-5] [--due date]")
            return
        try:
            task_id = int(rest[0])
        except ValueError:
            print("  ⚠️  ID must be a number"); return
        _, flags = parse_flags(rest[1:])
        priority = validate_priority(flags["priority"]) if "priority" in flags else None
        if "priority" in flags and priority is None:
            return
        status = flags.get("status")
        if status and status not in VALID_STATUSES:
            print(f"  ⚠️  Status must be one of: {', '.join(VALID_STATUSES)}")
            return
        update_task(task_id, title=flags.get("title"), description=flags.get("description"),
                    status=status, priority=priority, due_date=flags.get("due_date"))

    elif cmd == "delete":
        if not rest:
            print("  ⚠️  Usage: delete <id>"); return
        try:
            task_id = int(rest[0])
        except ValueError:
            print("  ⚠️  ID must be a number"); return

        with get_connection() as conn:
            row = conn.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            print(f"  ❌ No task with ID #{task_id}")
            return

        confirm = input(f"  ⚠️  Are you sure you want to delete task #{task_id}: \"{row['title']}\"? (y/N) ").strip().lower()
        if confirm in ("y", "yes"):
            delete_task(task_id)
        else:
            print("  Cancelled.")

    else:
        print(f" Unknown command: '{cmd}'. Type 'help' for usage.")


# ─────────────────────────────────────────────
# Main interactive loop
# ─────────────────────────────────────────────

def main():
    init_db()
    print("╔═══════════════════════════════════╗")
    print("║   📋  To-Do List  |  type 'help'  ║")
    print("╚═══════════════════════════════════╝")

    while True:
        try:
            line = input("\n› ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye!")
            break
        if line:
            dispatch(line)


if __name__ == "__main__":
    main()