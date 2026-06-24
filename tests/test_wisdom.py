from __future__ import annotations

import pytest
from agents.registry import load_module
from modules.wisdom.sources import WisdomModule
from modules.wisdom.config import KEYWORDS, SOURCE_AUTHORITY


def test_wisdom_module_registration():
    """Verify that the wisdom module is successfully registered and instantiates the correct class."""
    module = load_module("wisdom")
    assert isinstance(module, WisdomModule)
    assert module.name == "wisdom"


def test_wisdom_module_keywords_and_sources():
    """Verify keywords and sources are configured correctly."""
    module = load_module("wisdom")
    keywords = module.get_keywords()
    
    assert "never give up" in keywords
    assert "chilling" in keywords
    assert "mindfulness" in keywords
    
    sources = module.get_sources()
    assert len(sources) > 0
    
    source_names = {src.name for src in sources}
    assert "James Clear" in source_names
    assert "Daily Stoic" in source_names
    assert "Zen Habits" in source_names
    assert "NewsAPI - Motivation" in source_names
    
    # Verify Zen Habits URL is correct
    zh_source = next(src for src in sources if src.name == "Zen Habits")
    assert zh_source.url == "https://zenhabits.net/index.xml"


def test_wisdom_module_prompts():
    """Verify prompt builders execute without errors and return expected strings."""
    module = load_module("wisdom")
    
    # Test chat system prompt
    chat_prompt = module.get_chat_system_prompt()
    assert "Kyvra Wisdom" in chat_prompt
    assert "never give up" in chat_prompt
    assert "just chilling" in chat_prompt
    
    # Test report prompt
    dummy_items = [
        {
            "title": "The Power of Tiny Habits",
            "url": "https://jamesclear.com/tiny-habits",
            "confidence_score": 92,
            "published_at": "2026-03-15T12:00:00Z",
            "summary": "How doing 1% better every day compounding over time yields massive changes.",
            "source": "James Clear",
            "is_spike": True
        }
    ]
    report_prompt = module.get_report_prompt(dummy_items)
    assert "🌱 **KYVRA DAILY WISDOM & MOTIVATION" in report_prompt
    assert "Tiny Habits" in report_prompt
    
    # Test thread prompt
    thread_prompt = module.get_thread_prompt(dummy_items[0], voice="Empathetic, warm")
    assert "Empathetic, warm" in thread_prompt
    
    # Test brief prompt
    brief_prompt = module.get_brief_prompt(dummy_items)
    assert "Daily Vibe Check" in brief_prompt
    
    # Test newsletter prompt
    newsletter_prompt = module.get_newsletter_prompt(dummy_items[0])
    assert "Vibe Check (Drive vs. Calm)" in newsletter_prompt
    
    # Test script prompt
    script_prompt = module.get_script_prompt(dummy_items[0])
    assert "voiceover script" in script_prompt
    
    # Test tweet hook prompt
    tweet_prompt = module.get_tweet_hook_prompt(dummy_items[0], lang="en")
    assert "Write 1 compelling tweet hook" in tweet_prompt
