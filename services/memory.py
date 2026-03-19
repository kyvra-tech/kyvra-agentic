import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DB_PATH = Path("kyvra.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    try:
        with _connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_voices (
                    user_id   INTEGER PRIMARY KEY,
                    voice     TEXT    NOT NULL,
                    updated_at TEXT   NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        logger.info("[Memory] SQLite initialized at %s", _DB_PATH)
    except sqlite3.OperationalError as e:
        logger.error("[Memory] Failed to initialize SQLite: %s", e)
        raise


def save_voice_profile(user_id: int, voice: str) -> None:
    """Upsert a user's voice/style description."""
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO user_voices (user_id, voice, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    voice = excluded.voice,
                    updated_at = excluded.updated_at
                """,
                (user_id, voice),
            )
            conn.commit()
    except sqlite3.OperationalError as e:
        logger.error("[Memory] Failed to save voice profile for user %s: %s", user_id, e)


def get_voice_profile(user_id: int) -> str | None:
    """Return the user's saved voice description, or None if not set."""
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT voice FROM user_voices WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row["voice"] if row else None
    except sqlite3.OperationalError as e:
        logger.error("[Memory] Failed to load voice profile for user %s: %s", user_id, e)
        return None
