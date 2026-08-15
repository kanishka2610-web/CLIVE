from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from backend.app.models.story import Story
from backend.app.models.source import Source
from backend.app.services.normalizer import canonicalize_url, normalize_title, generate_content_hash

# List of trusted primary domain identifiers (first-party AI labs/orgs)
PRIMARY_DOMAINS = [
    "openai.com", "anthropic.com", "deepmind.google", "blog.google", 
    "ai.meta.com", "huggingface.co", "mistral.ai", "microsoft.com", 
    "github.com", "arxiv.org", "stability.ai", "cohere.com", "x.ai"
]

def is_primary_source(url: str, source_category: str = "") -> bool:
    """Returns True if the URL or source category indicates a primary first-party publication."""
    url_lower = url.lower()
    if any(domain in url_lower for domain in PRIMARY_DOMAINS):
        return True
    if source_category.lower() in ["lab", "research", "first-party", "official"]:
        return True
    return False

class Deduplicator:
    def __init__(self, db: Session):
        self.db = db

    def check_duplicate(
        self,
        raw_url: str,
        title: str,
        content: str = "",
        published_at: Optional[datetime] = None,
        companies: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        source_category: str = "",
        time_window_hours: int = 72
    ) -> Tuple[bool, Optional[Story], str]:
        """
        Multi-tier deduplication check:
        1. Canonicalize URLs and remove tracking parameters.
        2. Normalize titles and compare with RapidFuzz.
        3. Use publication time + company/topic context as supporting signals.
        4. Prefer the primary/original source when several publications cover the same announcement.
        DO NOT merge stories only because titles are fuzzy matches.
        """
        canonical_url = canonicalize_url(raw_url)
        norm_title = normalize_title(title)
        hash_sig = generate_content_hash(canonical_url, norm_title, content)
        
        # 1. Exact Canonical URL match
        exact_url_story = self.db.query(Story).filter(Story.canonical_url == canonical_url).first()
        if exact_url_story:
            return True, exact_url_story, "exact_url_match"

        # 2. Exact Hash Signature match
        exact_hash_story = self.db.query(Story).filter(Story.hash_signature == hash_sig).first()
        if exact_hash_story:
            return True, exact_hash_story, "exact_content_hash_match"

        # 3. Fuzzy Title + Context match within time window
        if not published_at:
            published_at = datetime.now(timezone.utc)
            
        time_floor = published_at - timedelta(hours=time_window_hours)
        time_ceil = published_at + timedelta(hours=time_window_hours)
        
        candidates = self.db.query(Story).filter(
            Story.published_at >= time_floor,
            Story.published_at <= time_ceil
        ).all()
        
        incoming_companies = set(c.lower() for c in (companies or []))
        incoming_topics = set(t.lower() for t in (topics or []))
        is_incoming_primary = is_primary_source(canonical_url, source_category)

        for candidate in candidates:
            cand_norm_title = candidate.normalized_title or normalize_title(candidate.title)
            
            # Fuzzy title ratio
            ratio = fuzz.token_sort_ratio(norm_title.lower(), cand_norm_title.lower())
            
            # Guard: Require high similarity AND contextual overlap (never merge on title alone)
            if ratio >= 85:
                cand_companies = set(c.lower() for c in (candidate.companies or []))
                cand_topics = set(t.lower() for t in (candidate.topics or []))
                
                # If both stories specify known distinct companies without overlap, DO NOT merge
                if incoming_companies and cand_companies and not (incoming_companies & cand_companies):
                    continue

                has_company_overlap = bool(incoming_companies and cand_companies and (incoming_companies & cand_companies))
                has_topic_overlap = bool(incoming_topics and cand_topics and (incoming_topics & cand_topics))
                
                # Ensure timezone-aware datetimes for safe arithmetic
                cand_pub = candidate.published_at
                if cand_pub and cand_pub.tzinfo is None:
                    cand_pub = cand_pub.replace(tzinfo=timezone.utc)
                pub_at = published_at
                if pub_at and pub_at.tzinfo is None:
                    pub_at = pub_at.replace(tzinfo=timezone.utc)

                # Check time difference in hours
                time_diff = abs((pub_at - cand_pub).total_seconds()) / 3600.0 if (cand_pub and pub_at) else 0.0
                
                # Context validation rule
                if ratio >= 92 or (ratio >= 85 and (has_company_overlap or has_topic_overlap or time_diff < 12)):
                    # Check if incoming is higher priority primary source
                    is_candidate_primary = is_primary_source(candidate.canonical_url)
                    if is_incoming_primary and not is_candidate_primary:
                        # Secondary story exists, primary story has arrived:
                        return True, candidate, "duplicate_primary_override"
                    return True, candidate, f"fuzzy_title_match_{ratio:.1f}%"

        return False, None, "unique"
