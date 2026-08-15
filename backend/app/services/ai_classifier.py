import os
import json
import re
import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from backend.app.config import settings

logger = logging.getLogger(__name__)

class StoryClassificationResult(BaseModel):
    is_ai_related: bool = Field(description="Whether the article is directly related to AI/ML or AI compute")
    category: str = Field(description="Primary category: AI Agents, LLMs, Multimodal, Hardware, Research, Infrastructure, Developer Tools, Open Source, or General AI")
    sub_category: Optional[str] = Field(default=None, description="Specific subfield, e.g., 'Developer Tools', 'Reasoning Models', 'Inference Acceleration'")
    companies: List[str] = Field(default_factory=list, description="Key companies/labs mentioned (e.g. OpenAI, Anthropic, Google DeepMind, Meta, Mistral, NVIDIA)")
    technologies: List[str] = Field(default_factory=list, description="Key architectures, models or tech (e.g. Claude 3.7, GPT-4.5, Agents SDK, MoE, LoRA)")
    topics: List[str] = Field(default_factory=list, description="Core themes (e.g. AI Agents, Developer Tools, Reasoning, Open Weights)")
    importance_score: float = Field(description="Significance score (0.0 - 10.0 or 0 - 100)")
    novelty_score: float = Field(description="Novelty score (0.0 - 10.0 or 0 - 100)")
    technical_score: float = Field(description="Technical depth score (0.0 - 10.0 or 0 - 100)")
    is_breaking: bool = Field(default=False, description="True if major breaking release or landmark breakthrough")

    @field_validator("importance_score", "novelty_score", "technical_score", mode="after")
    @classmethod
    def normalize_score(cls, v: float) -> float:
        """Normalizes score to standard 0-100 float scale if given on a 0-10 scale."""
        if v <= 10.0 and v > 0.0:
            return round(v * 10.0, 1)
        return round(min(100.0, max(0.0, v)), 1)

COMPANY_KEYWORDS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "claude": "Anthropic",
    "deepmind": "Google DeepMind",
    "google ai": "Google",
    "gemini": "Google",
    "meta ai": "Meta",
    "llama": "Meta",
    "mistral": "Mistral AI",
    "nvidia": "NVIDIA",
    "hugging face": "Hugging Face",
    "huggingface": "Hugging Face",
    "microsoft": "Microsoft",
    "cohere": "Cohere",
    "xai": "xAI",
    "grok": "xAI",
    "apple": "Apple",
    "deepseek": "DeepSeek"
}

TECH_KEYWORDS = {
    "transformer": "Transformers",
    "diffusion": "Diffusion",
    "moe": "Mixture of Experts (MoE)",
    "lora": "LoRA / PEFT",
    "rag": "RAG",
    "mcp": "Model Context Protocol (MCP)",
    "agents sdk": "Agents SDK",
    "reasoning": "Reasoning Models",
    "vision": "Computer Vision",
    "whisper": "Whisper",
    "gpu": "GPU Infrastructure",
    "cuda": "CUDA",
    "agent": "AI Agents",
    "multimodal": "Multimodal AI"
}

BREAKING_PATTERNS = [
    r"\b(announcing|introducing|releases?|unveils?|launches?|open[- ]sources?)\b",
    r"\b(sota|state[- ]of[- ]the[- ]art|breakthrough|frontier model)\b",
    r"\b(gpt-5|gpt-4\.5|claude[- ]3\.7|gemini[- ]2\.5|llama[- ]4|deepseek[- ]r1|o3|o1)\b"
]

def fallback_heuristic_classifier(title: str, content: str, source_name: str = "") -> StoryClassificationResult:
    full_text = f"{title} {content}".lower()
    
    ai_terms = ["ai", "model", "llm", "neural", "deep learning", "machine learning", "dataset", 
                "inference", "weights", "benchmark", "agent", "prompt", "token", "embedding", "gpu", "rag"]
    is_ai = any(term in full_text for term in ai_terms) or any(k in full_text for k in COMPANY_KEYWORDS)
    
    companies = [v for k, v in COMPANY_KEYWORDS.items() if k in full_text]
    if not companies and source_name:
        companies = [v for k, v in COMPANY_KEYWORDS.items() if k in source_name.lower()]
        
    technologies = [v for k, v in TECH_KEYWORDS.items() if k in full_text]
    
    topics = []
    if "agent" in full_text or "agents sdk" in full_text:
        topics.append("AI Agents")
    if "developer" in full_text or "sdk" in full_text or "api" in full_text:
        topics.append("Developer Tools")
    if "open-source" in full_text or "open weights" in full_text:
        topics.append("Open Source")
    if "benchmark" in full_text:
        topics.append("Benchmarks")
    if not topics:
        topics = ["AI Research & Development"]

    category = "General AI"
    if "AI Agents" in topics or any("Agent" in t for t in technologies):
        category = "AI Agents"
    elif "Developer Tools" in topics or "Model Context Protocol (MCP)" in technologies:
        category = "Developer Tools"
    elif any(t in ["Computer Vision", "Multimodal AI", "Diffusion"] for t in technologies):
        category = "Multimodal"
    elif any(t in ["GPU Infrastructure", "CUDA"] for t in technologies) or "NVIDIA" in companies:
        category = "Hardware"
    elif "arxiv" in full_text or "research" in full_text:
        category = "Research"
    elif any(t in ["Transformers", "Reasoning Models"] for t in technologies):
        category = "LLMs"

    importance = 6.0
    novelty = 5.5
    technical = 5.5
    
    if any(c in ["OpenAI", "Anthropic", "Google DeepMind", "Meta", "Mistral AI", "DeepSeek"] for c in companies):
        importance += 2.0
        novelty += 1.5
    if "arxiv" in full_text or "architecture" in full_text:
        technical += 2.5
        
    is_breaking = False
    for pat in BREAKING_PATTERNS:
        if re.search(pat, full_text):
            is_breaking = True
            importance += 1.2
            novelty += 1.5
            break

    return StoryClassificationResult(
        is_ai_related=is_ai,
        category=category,
        sub_category=topics[0] if topics else "General AI",
        companies=companies[:4],
        technologies=technologies[:4],
        topics=topics[:4],
        importance_score=min(10.0, max(2.5, importance)),
        novelty_score=min(10.0, max(2.0, novelty)),
        technical_score=min(10.0, max(2.0, technical)),
        is_breaking=is_breaking
    )

class AIClassifierService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.model_name = model_name or os.getenv("GEMINI_CLASSIFIER_MODEL") or settings.GEMINI_CLASSIFIER_MODEL
        self._client = None
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI Client: {e}")

    def classify_story(self, title: str, content: str, source_name: str = "") -> StoryClassificationResult:
        """
        Classifies story with Gemini SDK using structured JSON output.
        Follows official prompt instructions:
        'You are an AI technology intelligence analyst.
        Prioritize meaningful new models, AI products, APIs, agents, research, open-source releases,
        infrastructure, developer tooling, robotics, acquisitions, regulation, security and meaningful pricing/API changes.
        Down-rank opinion pieces, generic tutorials, SEO content, marketing filler, repeated news and speculation without evidence.
        Return only the requested structured output.'
        """
        if not self._client or not self.api_key:
            return fallback_heuristic_classifier(title, content, source_name)

        system_instruction = (
            "You are an AI technology intelligence analyst. "
            "Prioritize meaningful new models, AI products, APIs, agents, research, open-source releases, "
            "infrastructure, developer tooling, robotics, acquisitions, regulation, security and meaningful pricing/API changes. "
            "Down-rank opinion pieces, generic tutorials, SEO content, marketing filler, repeated news and speculation without evidence. "
            "Return only the requested structured output adhering strictly to the schema."
        )

        prompt = f"""
Source: {source_name}
Title: {title}
Content snippet:
{content[:2500]}
"""

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": StoryClassificationResult,
                    "temperature": 0.2,
                }
            )
            
            if response and response.text:
                data = json.loads(response.text)
                return StoryClassificationResult(**data)
        except Exception as ex:
            logger.error(f"Gemini classifier call failed: {ex}. Falling back to heuristics.")
            
        return fallback_heuristic_classifier(title, content, source_name)

ai_classifier = AIClassifierService()
