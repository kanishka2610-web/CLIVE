import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
import feedparser
from bs4 import BeautifulSoup
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.source import Source
from backend.app.models.story import Story
from backend.app.services.normalizer import canonicalize_url, normalize_title, generate_content_hash, parse_published_date
from backend.app.services.deduplicator import Deduplicator
from backend.app.services.ai_classifier import ai_classifier
from backend.app.services.summarizer import ai_summarizer

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": settings.USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException, httpx.ConnectError)),
    reraise=True
)
def fetch_url_content(url: str, timeout: float = settings.HTTP_TIMEOUT_SECONDS) -> str:
    """Fetches raw URL text content with exponential backoff retries."""
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text

def extract_clean_text(raw_html: str) -> str:
    """Extracts clean article text from HTML using trafilatura with BeautifulSoup fallback."""
    if not raw_html:
        return ""
    try:
        extracted = trafilatura.extract(
            raw_html,
            include_comments=False,
            include_tables=False,
            no_fallback=False
        )
        if extracted and len(extracted.strip()) > 80:
            return extracted.strip()
    except Exception:
        pass
        
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)[:3000]
    except Exception:
        return ""

class RawEntry:
    def __init__(self, title: str, url: str, content: str, published_at: datetime, author: Optional[str] = None):
        self.title = title
        self.url = url
        self.content = content
        self.published_at = published_at
        self.author = author

class BaseCollector(ABC):
    @abstractmethod
    def collect(self, source: Source) -> List[RawEntry]:
        pass

class RSSCollector(BaseCollector):
    def collect(self, source: Source) -> List[RawEntry]:
        content = fetch_url_content(source.url)
        feed = feedparser.parse(content)
        entries = []
        for entry in feed.entries[:settings.MAX_ITEMS_PER_FEED]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            body = entry.get("summary", "") or entry.get("description", "")
            if "content" in entry and entry.content:
                body = entry.content[0].value
            pub_date = entry.get("published_parsed") or entry.get("updated_parsed") or entry.get("published")
            published_dt = parse_published_date(pub_date)
            author = entry.get("author", source.name)
            if title and link:
                entries.append(RawEntry(title=title, url=link, content=body, published_at=published_dt, author=author))
        return entries

class AtomCollector(BaseCollector):
    def collect(self, source: Source) -> List[RawEntry]:
        content = fetch_url_content(source.url)
        feed = feedparser.parse(content)
        entries = []
        for entry in feed.entries[:settings.MAX_ITEMS_PER_FEED]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            body = entry.get("summary", "") or entry.get("description", "")
            if "content" in entry and entry.content:
                body = entry.content[0].value
            pub_date = entry.get("updated_parsed") or entry.get("published_parsed") or entry.get("updated")
            published_dt = parse_published_date(pub_date)
            author = entry.get("author", source.name)
            if title and link:
                entries.append(RawEntry(title=title, url=link, content=body, published_at=published_dt, author=author))
        return entries

class HTMLCollector(BaseCollector):
    def collect(self, source: Source) -> List[RawEntry]:
        content = fetch_url_content(source.url)
        soup = BeautifulSoup(content, "html.parser")
        entries = []
        article_tags = soup.find_all(["article", "div", "li"], limit=15)
        for art in article_tags:
            a_tag = art.find("a", href=True)
            if a_tag and a_tag.get_text(strip=True):
                link = a_tag["href"]
                if not link.startswith("http"):
                    from urllib.parse import urljoin
                    link = urljoin(source.url, link)
                title = a_tag.get_text(strip=True)
                if len(title) > 15:
                    entries.append(RawEntry(
                        title=title,
                        url=link,
                        content=art.get_text(strip=True),
                        published_at=datetime.now(timezone.utc),
                        author=source.name
                    ))
        return entries

class FeedCollectorService:
    def __init__(self, db: Session):
        self.db = db
        self.deduplicator = Deduplicator(db)
        self.collectors: Dict[str, BaseCollector] = {
            "rss": RSSCollector(),
            "atom": AtomCollector(),
            "html": HTMLCollector()
        }

    def scan_source(self, source: Source) -> Dict[str, Any]:
        """
        Scans a single source safely, tracking success/failure statistics.
        """
        results = {
            "source_id": source.id,
            "source_name": source.name,
            "items_found": 0,
            "items_saved": 0,
            "items_duplicate": 0,
            "status": "success",
            "errors": []
        }
        
        try:
            logger.info(f"Scanning source [{source.name}] ({source.url})...")
            collector = self.collectors.get(source.feed_type.lower(), self.collectors["rss"])
            raw_entries = collector.collect(source)
            results["items_found"] = len(raw_entries)
            
            for item in raw_entries:
                canonical_url = canonicalize_url(item.url)
                norm_title = normalize_title(item.title)
                
                # Pre-check canonical URL in database
                existing_canonical = self.db.query(Story.id).filter(Story.canonical_url == canonical_url).first()
                if existing_canonical:
                    results["items_duplicate"] += 1
                    continue

                # Check for duplicate via deduplicator
                is_dup, existing_story, reason = self.deduplicator.check_duplicate(
                    raw_url=canonical_url,
                    title=norm_title,
                    content=item.content,
                    published_at=item.published_at,
                    source_category=source.category
                )
                
                if is_dup:
                    results["items_duplicate"] += 1
                    continue
                
                extracted_body = extract_clean_text(item.content)
                if not extracted_body or len(extracted_body) < 100:
                    try:
                        page_html = fetch_url_content(canonical_url, timeout=5.0)
                        deep_text = extract_clean_text(page_html)
                        if deep_text and len(deep_text) > len(extracted_body):
                            extracted_body = deep_text
                    except Exception:
                        pass
                
                # AI classification & understanding
                classification = ai_classifier.classify_story(
                    title=norm_title,
                    content=extracted_body or item.content,
                    source_name=source.name
                )
                
                if not classification.is_ai_related:
                    continue

                # Executive summary (gated by importance threshold)
                summary_data = ai_summarizer.summarize_story(
                    title=norm_title,
                    content=extracted_body or item.content,
                    importance_score=classification.importance_score,
                    category=classification.category,
                    companies=classification.companies
                )
                
                hash_sig = generate_content_hash(canonical_url, norm_title, extracted_body)
                
                story = Story(
                    source_id=source.id,
                    canonical_url=canonical_url,
                    original_url=item.url,
                    title=item.title,
                    normalized_title=norm_title,
                    hash_signature=hash_sig,
                    author=item.author or source.name,
                    raw_content=item.content[:5000],
                    extracted_content=(extracted_body or item.content)[:8000],
                    published_at=item.published_at,
                    is_ai_related=classification.is_ai_related,
                    category=classification.category,
                    sub_category=classification.sub_category,
                    companies=classification.companies,
                    technologies=classification.technologies,
                    topics=classification.topics,
                    importance_score=classification.importance_score,
                    novelty_score=classification.novelty_score,
                    technical_score=classification.technical_score,
                    is_breaking=classification.is_breaking,
                    headline=summary_data.headline or norm_title,
                    summary=summary_data.summary,
                    why_it_matters=summary_data.why_it_matters,
                    status="processed"
                )
                
                try:
                    self.db.add(story)
                    self.db.commit()
                    results["items_saved"] += 1
                except Exception as save_ex:
                    self.db.rollback()
                    results["items_duplicate"] += 1
                    logger.info(f"Skipping duplicate item [{canonical_url}]: {save_ex}")

            # Update source health stats
            source.last_scanned_at = datetime.now(timezone.utc)
            source.last_success_at = datetime.now(timezone.utc)
            source.failure_count = 0
            source.last_error = None
            self.db.commit()

        except Exception as ex:
            self.db.rollback()
            error_msg = f"Failed to scan source: {str(ex)}"
            logger.error(error_msg)
            results["status"] = "failed"
            results["errors"].append(error_msg)
            try:
                source.last_scanned_at = datetime.now(timezone.utc)
                source.failure_count = (source.failure_count or 0) + 1
                source.last_error = str(ex)[:400]
                self.db.commit()
            except Exception:
                self.db.rollback()


        return results

    def scan_all_active_sources(self) -> Dict[str, Any]:
        """Scans all active sources sequentially with complete error isolation."""
        sources = self.db.query(Source).filter(Source.is_active == True).all()
        summary = {
            "total_sources": len(sources),
            "total_items_saved": 0,
            "total_duplicates": 0,
            "successful_sources": 0,
            "failed_sources": 0,
            "details": []
        }
        
        for src in sources:
            res = self.scan_source(src)
            if res["status"] == "success":
                summary["successful_sources"] += 1
            else:
                summary["failed_sources"] += 1
            summary["total_items_saved"] += res["items_saved"]
            summary["total_duplicates"] += res["items_duplicate"]
            summary["details"].append(res)
            
        return summary
