import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from configs.config import config

class Database:
    def __init__(self):
        self.db_path = Path(config.sqlite_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            # Fallback inline schema creation if file not found
            schema_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                plan TEXT,
                status TEXT DEFAULT 'pending',
                project_name TEXT,
                directory TEXT,
                worker_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                output TEXT,
                verification_status TEXT DEFAULT 'unverified',
                error_message TEXT
            );
            """
        else:
            with open(schema_path, "r") as f:
                schema_sql = f.read()

        with self._get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    # --- TASKS ---
    def create_task(self, task_id, description, project_name=None, directory=None, worker_type=None, plan=None):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, description, plan, status, project_name, directory, worker_type)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
                """,
                (task_id, description, plan, project_name, directory, worker_type)
            )
            conn.commit()

    def update_task(self, task_id, status=None, finished_at=None, output=None, verification_status=None, error_message=None, plan=None):
        updates = []
        params = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if finished_at is not None:
            updates.append("finished_at = ?")
            params.append(finished_at)
        if output is not None:
            updates.append("output = ?")
            params.append(output)
        if verification_status is not None:
            updates.append("verification_status = ?")
            params.append(verification_status)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        if plan is not None:
            updates.append("plan = ?")
            params.append(plan)

        if not updates:
            return

        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        with self._get_connection() as conn:
            conn.execute(query, tuple(params))
            conn.commit()

    def get_task(self, task_id):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_tasks(self, limit=10):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- LOGS ---
    def log(self, task_id, level, message):
        # Format message in print if debug/interactive
        print(f"[{level}] {message}")
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO logs (task_id, log_level, message) VALUES (?, ?, ?)",
                (task_id, level, message)
            )
            conn.commit()

    def get_logs(self, task_id=None, limit=50):
        with self._get_connection() as conn:
            if task_id:
                cursor = conn.execute(
                    "SELECT * FROM logs WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?", 
                    (task_id, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", 
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- CONVERSATIONS ---
    def add_message(self, role, content, telegram_msg_id=None, reasoning_details=None):
        if reasoning_details is not None and not isinstance(reasoning_details, str):
            try:
                reasoning_details = json.dumps(reasoning_details)
            except Exception:
                reasoning_details = str(reasoning_details)

        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (telegram_msg_id, role, content, reasoning_details) VALUES (?, ?, ?, ?)",
                (telegram_msg_id, role, content, reasoning_details)
            )
            conn.commit()

    def get_conversation_history(self, limit=20):
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM conversations ORDER BY timestamp ASC LIMIT ?", (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- MEMORIES ---
    def set_memory(self, tag, key, value, project_name=None):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (tag, key_text, value_text, project_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key_text) DO UPDATE SET value_text = excluded.value_text, tag = excluded.tag, project_name = excluded.project_name
                """,
                (tag, key, value, project_name)
            )
            conn.commit()

    def get_memory(self, key):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM memories WHERE key_text = ?", (key,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_memories(self, query=None, tag=None, project_name=None):
        sql = "SELECT * FROM memories WHERE 1=1"
        params = []
        if tag:
            sql += " AND tag = ?"
            params.append(tag)
        if project_name:
            sql += " AND project_name = ?"
            params.append(project_name)
        if query:
            sql += " AND (key_text LIKE ? OR value_text LIKE ?)"
            params.append(f"%{query}%")
            params.append(f"%{query}%")
        
        with self._get_connection() as conn:
            cursor = conn.execute(sql, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    # --- SKILLS ---
    def set_skill(self, name, content, description=""):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO skills (name, content, description, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET content = excluded.content, description = excluded.description, last_updated = CURRENT_TIMESTAMP
                """,
                (name, content, description)
            )
            conn.commit()

    def get_skill(self, name):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM skills WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_skills(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM skills ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

# Global DB client instance
db = Database()
