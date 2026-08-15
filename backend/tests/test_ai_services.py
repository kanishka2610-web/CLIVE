import pytest
from unittest.mock import MagicMock, patch
from backend.app.services.ai_classifier import AIClassifierService, StoryClassificationResult, fallback_heuristic_classifier
from backend.app.services.summarizer import AISummarizerService, StorySummaryResult, fallback_heuristic_summarizer

def test_fallback_heuristic_classifier():
    title = "Anthropic Announces Claude 3.7 Sonnet with Extended Thinking"
    content = "Anthropic today introduces Claude 3.7 Sonnet, a hybrid reasoning model setting SOTA benchmarks."
    
    result = fallback_heuristic_classifier(title, content, "Anthropic News")
    assert isinstance(result, StoryClassificationResult)
    assert result.is_ai_related is True
    assert "Anthropic" in result.companies
    assert result.importance_score > 60.0
    assert result.is_breaking is True

def test_fallback_heuristic_classifier_non_ai():
    title = "Best Coffee Shops in San Francisco"
    content = "A review of artisanal espresso bars and pastries in downtown SF."
    
    result = fallback_heuristic_classifier(title, content, "Food Blog")
    assert result.is_ai_related is False

def test_classifier_service_with_mocked_gemini():
    classifier = AIClassifierService(api_key="mock_key", model_name="gemini-2.5-flash")
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"is_ai_related": true, "category": "AI Agents", "sub_category": "Developer Tools", "companies": ["OpenAI"], "technologies": ["Agents SDK"], "topics": ["AI Agents", "Developer Tools"], "importance_score": 8.7, "novelty_score": 9.1, "technical_score": 7.8, "is_breaking": true}'
    mock_client.models.generate_content.return_value = mock_response
    classifier._client = mock_client

    res = classifier.classify_story("Agents SDK Released", "OpenAI announces Agents SDK.")
    assert res.is_ai_related is True
    assert res.importance_score == 87.0
    assert res.category == "AI Agents"
    assert "Agents SDK" in res.technologies

def test_classifier_handles_invalid_json_gracefully():
    classifier = AIClassifierService(api_key="mock_key", model_name="gemini-2.5-flash")
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "INVALID NON-JSON OUTPUT"
    mock_client.models.generate_content.return_value = mock_response
    classifier._client = mock_client

    res = classifier.classify_story("OpenAI Launches o3 Reasoning Model", "OpenAI releases o3.")
    assert isinstance(res, StoryClassificationResult)
    assert res.is_ai_related is True
    assert "OpenAI" in res.companies

def test_summarizer_gated_by_importance_threshold():
    summarizer = AISummarizerService(api_key="mock_key")
    
    res_low = summarizer.summarize_story(
        title="Minor library patch v0.1.2",
        content="Fixed typo in documentation.",
        importance_score=35.0
    )
    assert res_low.why_it_matters == []
    assert len(res_low.headline.split()) <= 15

def test_summarizer_service_with_mocked_gemini():
    summarizer = AISummarizerService(api_key="mock_key", model_name="gemini-2.5-flash")
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"headline": "Anthropic Unveils Claude 3.7 Sonnet Hybrid Reasoning Architecture", "summary": "Anthropic released Claude 3.7 Sonnet, introducing hybrid instantaneous and step-by-step thinking tokens.", "why_it_matters": ["Sets new coding benchmarks and gives developers granular control over reasoning budgets."]}'
    mock_client.models.generate_content.return_value = mock_response
    summarizer._client = mock_client

    res = summarizer.summarize_story(
        title="Claude 3.7 Sonnet and Extended Thinking",
        content="Full article body...",
        importance_score=92.0,
        category="LLMs",
        companies=["Anthropic"]
    )
    assert len(res.headline.split()) <= 15
    assert len(res.why_it_matters) == 1
    assert "Sets new coding benchmarks" in res.why_it_matters[0]
