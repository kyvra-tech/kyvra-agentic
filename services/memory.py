from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

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
            # Note: user_voices table is removed in favor of global voice.md
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_items (
                    url        TEXT    NOT NULL,
                    module     TEXT    NOT NULL,
                    title      TEXT    NOT NULL DEFAULT '',
                    seen_at    TEXT    NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (url, module)
                )
            """)
            # Analytics feedback loop: one signal per (user_id, story_url) per UTC calendar day
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_signals (
                    key        TEXT    PRIMARY KEY,
                    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_signals (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL,
                    story_url  TEXT    NOT NULL,
                    delta      REAL    NOT NULL,
                    date_utc   TEXT    NOT NULL,
                    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        logger.info("[Memory] SQLite initialized at %s", _DB_PATH)
    except sqlite3.OperationalError as e:
        logger.error("[Memory] Failed to initialize SQLite: %s", e)
        raise


VOICE_FILE = Path("voice.md")

def save_voice_profile(user_id: int, voice: str) -> None:
    """Save the global voice/style description to voice.md (user_id is ignored)."""
    try:
        if not voice:
            if VOICE_FILE.exists():
                VOICE_FILE.unlink()
            logger.info("[Memory] Cleared global voice profile (voice.md deleted).")
        else:
            VOICE_FILE.write_text(voice, encoding="utf-8")
            logger.info("[Memory] Saved global voice profile to %s", VOICE_FILE)
    except Exception as e:
        logger.error("[Memory] Failed to save global voice profile: %s", e)


def get_voice_profile(user_id: int) -> str | None:
    """Return the global voice description from voice.md, or None if not set."""
    try:
        if VOICE_FILE.exists():
            return VOICE_FILE.read_text(encoding="utf-8").strip()
        return None
    except Exception as e:
        logger.error("[Memory] Failed to load global voice profile: %s", e)
        return None


# ── Seen-item tracking (story continuity / Phase 1) ───────────────────────────

def get_seen_urls(module: str, days: int = 7) -> set[str]:
    """Return URLs already reported for this module within the last N days.

    Returns empty set on any DB error so pipeline degrades gracefully.
    """
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT url FROM seen_items
                WHERE module = ?
                  AND seen_at >= datetime('now', ?)
                """,
                (module, f"-{days} days"),
            ).fetchall()
            return {row["url"] for row in rows}
    except sqlite3.OperationalError as e:
        logger.warning("[Memory] get_seen_urls failed, treating as empty: %s", e)
        return set()


def mark_seen(urls: list[str], module: str) -> None:
    """Record URLs as seen for this module. Duplicate-safe (REPLACE)."""
    if not urls:
        return
    try:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO seen_items (url, module, seen_at)
                VALUES (?, ?, datetime('now'))
                """,
                [(url, module) for url in urls],
            )
            conn.commit()
        logger.info("[Memory] Marked %d items as seen for module '%s'", len(urls), module)
    except sqlite3.OperationalError as e:
        logger.warning("[Memory] mark_seen failed (report still delivered): %s", e)


# ── Performance signal tracking (analytics feedback loop / T-028) ─────────────

def record_performance_signal(user_id: int, story_url: str, delta: float, date_utc: str) -> bool:
    """Record a performance signal.

    Returns True if recorded, False if duplicate (same user_id + story_url + date_utc).
    delta is clamped to [-5, +5] by the caller.
    """
    key = f"{user_id}:{story_url}:{date_utc}"
    try:
        with _connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM seen_signals WHERE key = ?", (key,)
            ).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO seen_signals (key) VALUES (?)", (key,)
            )
            conn.execute(
                """INSERT INTO performance_signals (user_id, story_url, delta, date_utc)
                   VALUES (?, ?, ?, ?)""",
                (user_id, story_url, delta, date_utc),
            )
            conn.commit()
        logger.info("[Memory] Performance signal recorded: user=%s delta=%+.1f url=%s", user_id, delta, story_url)
        return True
    except sqlite3.OperationalError as e:
        logger.error("[Memory] record_performance_signal failed: %s", e)
        return False


def get_source_performance(days: int = 30) -> dict[str, float]:
    """Return average performance delta per source from the last N days.

    Joins performance_signals with seen_items to map story_url → source name.
    Returns a dict of {source_name: avg_delta} for sources that have signals.
    Used by the analyst node to boost/penalize sources based on real engagement.
    """
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT si.source, AVG(ps.delta) as avg_delta, COUNT(*) as n
                FROM performance_signals ps
                JOIN seen_items si ON ps.story_url = si.url
                WHERE ps.date_utc >= date('now', ?)
                GROUP BY si.source
                HAVING n >= 2
                """,
                (f"-{days} days",),
            ).fetchall()
            return {row["source"]: round(row["avg_delta"], 2) for row in rows}
    except sqlite3.OperationalError as e:
        logger.warning("[Memory] get_source_performance failed, returning empty: %s", e)
        return {}

