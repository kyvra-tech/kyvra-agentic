from __future__ import annotations

import pytest
from agents.registry import load_module
from modules.web3.sources import Web3Module
from modules.web3.config import KEYWORDS, SOURCE_AUTHORITY


def test_web3_module_registration():
    """Verify that the web3 module is successfully registered and instantiates the correct class."""
    module = load_module("web3")
    assert isinstance(module, Web3Module)
    assert module.name == "web3"


def test_web3_module_keywords_and_sources():
    """Verify keywords are correctly populated and sources are formatted correctly."""
    module = load_module("web3")
    keywords = module.get_keywords()
    
    assert "smart contract" in keywords
    assert "zkp" in keywords
    assert "layer 2" in keywords
    
    sources = module.get_sources()
    assert len(sources) > 0
    
    # Assert specific sources exist
    source_names = {src.name for src in sources}
    assert "Ethereum Foundation" in source_names
    assert "Bankless" in source_names
    assert "a16z Crypto" in source_names
    assert "NewsAPI - Web3" in source_names
    
    # Validate bypass filter for curated feeds
    ef_source = next(src for src in sources if src.name == "Ethereum Foundation")
    assert ef_source.bypass_keyword_filter is True
    assert ef_source.source_type == "rss"


def test_web3_module_prompts():
    """Verify prompt builders execute without errors and return expected strings."""
    module = load_module("web3")
    
    # Test chat system prompt
    chat_prompt = module.get_chat_system_prompt()
    assert "Kyvra Web3" in chat_prompt
    assert "BULLISH / BEARISH / NEUTRAL" in chat_prompt
    
    # Test report prompt
    dummy_items = [
        {
            "title": "EIP-4844 Released",
            "url": "https://ethereum.org/eip-4844",
            "confidence_score": 95,
            "published_at": "2026-03-15T12:00:00Z",
            "summary": "Proto-danksharding introduces blob-carrying transactions to scale L2s.",
            "source": "Ethereum Foundation",
            "is_spike": True
        }
    ]
    report_prompt = module.get_report_prompt(dummy_items)
    assert "DAILY WEB3 TECHNICAL REPORT" in report_prompt
    assert "EIP-4844 Released" in report_prompt
    
    # Test thread prompt
    thread_prompt = module.get_thread_prompt(dummy_items[0], voice="Casual, punchy")
    assert "Twitter/X thread" in thread_prompt
    assert "Casual, punchy" in thread_prompt
    
    # Test brief prompt
    brief_prompt = module.get_brief_prompt(dummy_items)
    assert "Web3 dev pulse" in brief_prompt
    
    # Test newsletter prompt
    newsletter_prompt = module.get_newsletter_prompt(dummy_items[0])
    assert "developer-centric newsletter" in newsletter_prompt
    
    # Test script prompt
    script_prompt = module.get_script_prompt(dummy_items[0])
    assert "voiceover script" in script_prompt
    
    # Test tweet hook prompt
    tweet_prompt_en = module.get_tweet_hook_prompt(dummy_items[0], lang="en")
    assert "Write 1 compelling tweet hook" in tweet_prompt_en
    assert "English" in tweet_prompt_en
    
    tweet_prompt_vi = module.get_tweet_hook_prompt(dummy_items[0], lang="vi")
    assert "Vietnamese" in tweet_prompt_vi
