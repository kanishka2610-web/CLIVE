import os
import json
import re
import logging
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from backend.app.config import settings

logger = logging.getLogger(__name__)

class StorySummaryResult(BaseModel):
    headline: str = Field(description="Headline: approximately 15 words maximum. Sharp, executive, hype-free.")
    summary: str = Field(description="Summary: 1–3 concise sentences explaining the development and core mechanism.")
    why_it_matters: List[str] = Field(description="Why it matters: one strong sentence highlighting strategic and technical impact.")

    @field_validator("headline", mode="after")
    @classmethod
    def enforce_headline_length(cls, v: str) -> str:
        words = v.strip().split()
        if len(words) > 16:
            return " ".join(words[:15])
        return v.strip()

    @field_validator("why_it_matters", mode="before")
    @classmethod
    def ensure_why_it_matters_list(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [v.strip()]
        if isinstance(v, list):
            # Keep the primary strong sentence or at most 2
            return [s.strip() for s in v if s and isinstance(s, str)][:2]
        return ["Directly impacts AI architecture, developer velocity, and production deployment economics."]

def fallback_heuristic_summarizer(title: str, content: str, category: str = "", companies: Optional[List[str]] = None) -> StorySummaryResult:
    """
    Deterministic rule-based summary generation when Gemini is not available.
    Adheres strictly to the 15-word headline, 1-3 sentence summary, and 1-sentence 'Why it matters'.
    """
    clean_title = re.sub(r"\s+", " ", title).strip()
    words = clean_title.split()
    headline = " ".join(words[:15])

    clean_content = re.sub(r"<[^>]+>", " ", content).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_content) if len(s.strip()) > 20]
    
    # Filter filler phrases
    filler_patterns = [
        r"^(this article discusses|in this post we|today we are excited to|in today'?s rapidly evolving landscape)",
    ]
    filtered_sentences = []
    for sent in sentences:
        is_filler = any(re.search(pat, sent, re.IGNORECASE) for pat in filler_patterns)
        if not is_filler:
            filtered_sentences.append(sent)

    if filtered_sentences:
        summary = " ".join(filtered_sentences[:2])
    else:
        summary = f"{clean_title} introduces new capabilities in {category or 'AI engineering'}."

    comp_str = ", ".join(companies[:2]) if companies else "frontier labs"
    why_it_matters = [
        f"Advances production capability in {category or 'AI engineering'}, directly shifting architecture and cost trade-offs for teams using {comp_str}."
    ]

    return StorySummaryResult(
        headline=headline,
        summary=summary[:320],
        why_it_matters=why_it_matters
    )

class AISummarizerService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.model_name = model_name or os.getenv("GEMINI_SUMMARY_MODEL") or settings.GEMINI_SUMMARY_MODEL
        self._client = None
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI Client in Summarizer: {e}")

    def summarize_story(
        self,
        title: str,
        content: str,
        importance_score: float,
        category: str = "",
        companies: Optional[List[str]] = None
    ) -> StorySummaryResult:
        """
        Generates structured executive headline, summary, and why-it-matters sentence.
        Follows prompt specification:
        - Headline: approximately 15 words maximum.
        - Summary: 1–3 concise sentences.
        - Why it matters: one strong sentence.
        - Avoid filler such as 'this article discusses' or 'in today's rapidly evolving landscape'.
        """
        if importance_score < settings.IMPORTANCE_SUMMARY_THRESHOLD:
            words = title.strip().split()
            short_headline = " ".join(words[:15])
            return StorySummaryResult(
                headline=short_headline,
                summary=content[:180].strip() if content else title,
                why_it_matters=[]
            )

        if not self._client or not self.api_key:
            return fallback_heuristic_summarizer(title, content, category, companies)

        system_instruction = (
            "You are an elite AI technology intelligence analyst. "
            "Write a concise, high-signal executive brief for this development. "
            "Follow these constraints strictly: "
            "1. Headline: approximately 15 words maximum. Sharp and executive. "
            "2. Summary: 1–3 concise sentences explaining the announcement and mechanism. "
            "3. Why it matters: exactly one strong sentence highlighting the strategic, technical, or economic impact. "
            "4. NEVER use filler phrases such as 'this article discusses', 'in this post', or 'in today\\'s rapidly evolving landscape'. "
            "Return only the requested structured JSON adhering to the schema."
        )

        prompt = f"""
Category: {category}
Companies: {', '.join(companies or [])}
Title: {title}
Content:
{content[:2500]}
"""

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": StorySummaryResult,
                    "temperature": 0.2,
                }
            )
            
            if response and response.text:
                data = json.loads(response.text)
                return StorySummaryResult(**data)
        except Exception as ex:
            logger.error(f"Gemini summarizer call failed: {ex}. Falling back to heuristics.")
            
        return fallback_heuristic_summarizer(title, content, category, companies)

ai_summarizer = AISummarizerService()
