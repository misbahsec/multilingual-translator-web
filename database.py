"""
SQLite storage for translation history.

Kept deliberately simple (no ORM) -- a single table is enough for a
final-year-project demo. Swap in SQLAlchemy later if the schema grows.
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "translations.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            source_lang TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            auto_detected INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_translation(original, translated, src_code, tgt_code, auto_detected=False):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO translations
            (original_text, translated_text, source_lang, target_lang, auto_detected, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            original,
            translated,
            src_code,
            tgt_code,
            1 if auto_detected else 0,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_history(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM translations ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_history():
    conn = get_connection()
    conn.execute("DELETE FROM translations")
    conn.commit()
    conn.close()
