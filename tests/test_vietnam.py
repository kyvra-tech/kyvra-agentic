from __future__ import annotations

import pytest
from agents.registry import load_module
from modules.vietnam.sources import VietnamModule
from modules.vietnam.config import KEYWORDS, SOURCE_AUTHORITY


def test_vietnam_module_registration():
    """Verify that the vietnam module is successfully registered and instantiates the correct class."""
    module = load_module("vietnam")
    assert isinstance(module, VietnamModule)
    assert module.name == "vietnam"


def test_vietnam_module_keywords_and_sources():
    """Verify keywords and sources are configured correctly for lifestyle and nightlife."""
    module = load_module("vietnam")
    keywords = module.get_keywords()
    
    assert "gái xinh" in keywords
    assert "bar" in keywords
    assert "quẩy" in keywords
    assert "lounge" in keywords
    
    sources = module.get_sources()
    assert len(sources) > 0
    
    source_names = {src.name for src in sources}
    assert "Kenh14 Star" in source_names
    assert "Kenh14 Doi Song" in source_names
    assert "Ngoisao Hau Truong" in source_names
    assert "Ngoisao Lam Dep" in source_names
    assert "Google News - Bar San" in source_names
    assert "Google News - Gai Xinh" in source_names
    
    # Verify Kenh14 Star URL is correct
    k14_source = next(src for src in sources if src.name == "Kenh14 Star")
    assert k14_source.url == "https://kenh14.vn/star.rss"


def test_vietnam_module_prompts():
    """Verify prompt builders execute without errors and return expected strings with new instructions."""
    module = load_module("vietnam")
    
    # Test chat system prompt
    chat_prompt = module.get_chat_system_prompt()
    assert "Kyvra Vietnam" in chat_prompt
    assert "lifestyle" in chat_prompt
    assert "no sexy" in chat_prompt
    
    # Test report prompt
    dummy_items = [
        {
            "title": "KOL xinh đẹp chia sẻ bí quyết làm đẹp",
            "url": "https://example.com/beauty-tips",
            "confidence_score": 90,
            "published_at": "2026-06-25T12:00:00Z",
            "summary": "Nữ blogger nổi tiếng chia sẻ quy trình chăm sóc da tối giản phù hợp cho mùa hè.",
            "source": "Kenh14 Star",
            "is_spike": True
        }
    ]
    report_prompt = module.get_report_prompt(dummy_items)
    assert "🇻🇳 **KYVRA VIETNAM LIFESTYLE REPORT" in report_prompt
    assert "no sexy" in report_prompt
    
    # Test thread prompt
    thread_prompt = module.get_thread_prompt(dummy_items[0], voice="Trẻ trung, năng động")
    assert "Trẻ trung, năng động" in thread_prompt
    assert "short X thread" in thread_prompt
    
    # Test brief prompt
    brief_prompt = module.get_brief_prompt(dummy_items)
    assert "Vietnam Vibe Check" in brief_prompt
    
    # Test newsletter prompt
    newsletter_prompt = module.get_newsletter_prompt(dummy_items[0])
    assert "Nguồn:" in newsletter_prompt
    
    # Test script prompt
    script_prompt = module.get_script_prompt(dummy_items[0])
    assert "TikTok/Reels" in script_prompt
    
    # Test tweet hook prompt
    tweet_prompt = module.get_tweet_hook_prompt(dummy_items[0], lang="vi")
    assert "Write 1 compelling tweet hook" in tweet_prompt
