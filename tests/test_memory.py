"""Unit tests for services/memory.py — seen_items table (Phase 1: story continuity).

Uses an in-memory SQLite DB (tmp file per test) to avoid touching kyvra.db.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import services.memory as memory


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Redirect all memory.py DB calls to a fresh temp file for each test."""
    db_file = tmp_path / "test_kyvra.db"
    with patch.object(memory, "_DB_PATH", db_file):
        memory.init_db()
        yield db_file


# ── init_db ───────────────────────────────────────────────────────────────────

class TestInitDb:
    def test_creates_seen_items_table(self, isolated_db):
        conn = sqlite3.connect(isolated_db)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "seen_items" in tables

    def test_voice_profile_file_operations(self, tmp_path):
        test_voice_file = tmp_path / "test_voice.md"
        with patch.object(memory, "VOICE_FILE", test_voice_file):
            assert memory.get_voice_profile(123) is None
            memory.save_voice_profile(123, "Test Voice")
            assert memory.get_voice_profile(123) == "Test Voice"
            memory.save_voice_profile(123, "")
            assert memory.get_voice_profile(123) is None

    def test_idempotent(self, isolated_db):
        # Calling init_db again should not raise
        memory.init_db()


# ── mark_seen ─────────────────────────────────────────────────────────────────

class TestMarkSeen:
    def test_marks_urls(self, isolated_db):
        memory.mark_seen(["https://x.com/a", "https://x.com/b"], "tech")
        seen = memory.get_seen_urls("tech")
        assert "https://x.com/a" in seen
        assert "https://x.com/b" in seen

    def test_duplicate_safe(self, isolated_db):
        memory.mark_seen(["https://x.com/a"], "tech")
        memory.mark_seen(["https://x.com/a"], "tech")  # no error
        seen = memory.get_seen_urls("tech")
        assert len(seen) == 1

    def test_empty_list_noop(self, isolated_db):
        memory.mark_seen([], "tech")  # no error
        assert memory.get_seen_urls("tech") == set()

    def test_module_isolation(self, isolated_db):
        memory.mark_seen(["https://x.com/a"], "tech")
        # Same URL in a different module should NOT appear when querying crypto
        seen_crypto = memory.get_seen_urls("crypto")
        assert "https://x.com/a" not in seen_crypto


# ── get_seen_urls ─────────────────────────────────────────────────────────────

class TestGetSeenUrls:
    def test_returns_set(self, isolated_db):
        memory.mark_seen(["https://x.com/a"], "tech")
        result = memory.get_seen_urls("tech")
        assert isinstance(result, set)

    def test_empty_when_nothing_marked(self, isolated_db):
        assert memory.get_seen_urls("tech") == set()

    def test_respects_days_window(self, isolated_db):
        # Insert an old entry directly (bypassing mark_seen's datetime('now'))
        conn = sqlite3.connect(isolated_db)
        conn.execute(
            "INSERT INTO seen_items (url, module, seen_at) VALUES (?, ?, ?)",
            ("https://x.com/old", "tech", "2020-01-01 00:00:00"),
        )
        conn.commit()
        conn.close()
        # Should not be returned (older than 7 days)
        seen = memory.get_seen_urls("tech", days=7)
        assert "https://x.com/old" not in seen

    def test_recent_entry_included(self, isolated_db):
        memory.mark_seen(["https://x.com/new"], "tech")
        seen = memory.get_seen_urls("tech", days=7)
        assert "https://x.com/new" in seen

    def test_custom_days_window(self, isolated_db):
        memory.mark_seen(["https://x.com/new"], "tech")
        # 1-day window should still include just-marked items
        seen = memory.get_seen_urls("tech", days=1)
        assert "https://x.com/new" in seen


# ── Language Preferences ──────────────────────────────────────────────────────

class TestLanguagePreferences:
    def test_language_preference(self, tmp_path):
        test_lang_file = tmp_path / "test_lang.txt"
        with patch.object(memory, "LANG_FILE", test_lang_file):
            assert memory.get_language() == "en"
            memory.save_language("ja")
            assert memory.get_language() == "ja"
            memory.save_language("vi")
            assert memory.get_language() == "vi"
            memory.save_language("fr")  # unsupported
            assert memory.get_language() == "en"

    def test_get_language_instruction(self):
        assert "Japanese" in memory.get_language_instruction("ja")
        assert "Vietnamese" in memory.get_language_instruction("vi")
        assert memory.get_language_instruction("en") == ""

