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
                    source     TEXT    NOT NULL DEFAULT '',
                    seen_at    TEXT    NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (url, module)
                )
            """)
            # Check if columns exist in seen_items
            cursor = conn.execute("PRAGMA table_info(seen_items)")
            columns = [row[1] for row in cursor.fetchall()]
            if "source" not in columns:
                conn.execute("ALTER TABLE seen_items ADD COLUMN source TEXT NOT NULL DEFAULT ''")
            if "title" not in columns:
                conn.execute("ALTER TABLE seen_items ADD COLUMN title TEXT NOT NULL DEFAULT ''")
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

# ── Language preference (global, file-based) ──────────────────────────────────

LANG_FILE = Path("lang.txt")
SUPPORTED_LANGUAGES = {"en": "English", "ja": "Japanese (日本語)"}
DEFAULT_LANGUAGE = "en"


def save_language(lang: str) -> None:
    """Save the global language preference to lang.txt."""
    lang = lang.strip().lower()
    if lang not in SUPPORTED_LANGUAGES:
        logger.warning("[Memory] Unsupported language '%s', defaulting to 'en'", lang)
        lang = DEFAULT_LANGUAGE
    try:
        LANG_FILE.write_text(lang, encoding="utf-8")
        logger.info("[Memory] Saved global language preference: %s", lang)
    except Exception as e:
        logger.error("[Memory] Failed to save language preference: %s", e)


def get_language() -> str:
    """Return the global language code ('en' or 'ja'). Defaults to 'en'."""
    try:
        if LANG_FILE.exists():
            lang = LANG_FILE.read_text(encoding="utf-8").strip().lower()
            return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        return DEFAULT_LANGUAGE
    except Exception as e:
        logger.error("[Memory] Failed to load language preference: %s", e)
        return DEFAULT_LANGUAGE


def get_language_instruction(lang: str | None = None) -> str:
    """Return a prompt instruction block for the given language.

    Returns empty string for English (default), explicit instruction for JA.
    """
    lang = lang or get_language()
    if lang == "ja":
        return "\n\nIMPORTANT: Write the ENTIRE output in Japanese (日本語). Use natural, fluent Japanese."
    return ""


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


def mark_seen(items: list[str] | list[Any], module: str) -> None:
    """Record URLs or ScoredItem/dict objects as seen for this module. Duplicate-safe (REPLACE)."""
    if not items:
        return
    rows = []
    for item in items:
        if isinstance(item, str):
            rows.append((item, "", ""))
        else:
            url = str(getattr(item, "url", "") or "")
            source = str(getattr(item, "source", "") or "")
            title = str(getattr(item, "title", "") or "")
            if not url and isinstance(item, dict):
                url = str(item.get("url", "") or "")
                source = str(item.get("source", "") or "")
                title = str(item.get("title", "") or "")
            rows.append((url, source, title))

    try:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO seen_items (url, module, source, title, seen_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                [(r[0], module, r[1], r[2]) for r in rows],
            )
            conn.commit()
        logger.info("[Memory] Marked %d items as seen for module '%s'", len(items), module)
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

