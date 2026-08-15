import pytest
from backend.app.services.normalizer import canonicalize_url, normalize_title, generate_content_hash

def test_canonicalize_url_removes_tracking():
    raw = "https://openai.com/index/introducing-deep-research/?utm_source=twitter&utm_medium=social&ref=techcrunch&fbclid=12345"
    expected = "https://openai.com/index/introducing-deep-research"
    assert canonicalize_url(raw) == expected

def test_canonicalize_url_preserves_query_params_and_normalizes_case():
    raw = "HTTPS://Blog.Google/Technology/AI/Gemini-Update/?b=2&a=1&utm_campaign=launch"
    res = canonicalize_url(raw)
    assert res == "https://blog.google/Technology/AI/Gemini-Update?a=1&b=2"

def test_normalize_title_strips_brand_suffixes():
    raw = "Claude 3.7 Sonnet Released - Anthropic"
    assert normalize_title(raw) == "Claude 3.7 Sonnet Released"
    
    raw2 = "Introducing o3 Reasoning Model | OpenAI"
    assert normalize_title(raw2) == "Introducing o3 Reasoning Model"

def test_generate_content_hash_is_deterministic():
    url = "https://anthropic.com/news/claude-3-7"
    title = "Claude 3.7 Sonnet"
    content = "Anthropic today announces Claude 3.7."
    
    hash1 = generate_content_hash(url, title, content)
    hash2 = generate_content_hash(url, title, content)
    assert hash1 == hash2
    assert len(hash1) == 64
