import re
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from datetime import datetime, timezone
import dateparser

# List of tracking query parameter prefixes and exact keys to remove
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_reader", "utm_creative", "utm_place",
    "ref", "ref_src", "ref_url", "source",
    "fbclid", "gclid", "dclid", "gclsrc", "msclkid",
    "mc_cid", "mc_eid", "igshid", "_ga", "_gl", "_hsenc", "_hsmi",
    "sc_src", "sc_llid", "sc_customer", "ncid", "pk_campaign", "pk_kwd"
}

# Common blog/news title suffixes to clean
SUFFIX_PATTERNS = [
    r"\s*[-|–—]\s*(OpenAI|Anthropic|Google DeepMind|DeepMind|Meta AI|Hugging Face|Mistral AI|Microsoft Research|GitHub|TechCrunch|The Verge|ArXiv|Simon Willison's Weblog|Simon Willison|NVIDIA).*$",
    r"\s*[-|–—]\s*Blog\s*$",
    r"\s*[-|–—]\s*News\s*$",
    r"\s*\|\s*AI\s*$",
]

def canonicalize_url(raw_url: str) -> str:
    """
    Canonicalizes a URL by normalizing the scheme/netloc, removing tracking parameters,
    and stripping non-essential trailing slashes and fragments.
    """
    if not raw_url or not isinstance(raw_url, str):
        return ""
    
    raw_url = raw_url.strip()
    try:
        parsed = urlparse(raw_url)
        # Standardize scheme and hostname to lowercase
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        netloc = parsed.netloc.lower()
        
        # Remove standard default ports if present
        if ":80" in netloc and scheme == "http":
            netloc = netloc.replace(":80", "")
        elif ":443" in netloc and scheme == "https":
            netloc = netloc.replace(":443", "")
            
        # Filter query parameters
        query_items = parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_query = [
            (k, v) for k, v in query_items
            if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
        ]
        # Sort query params for consistent canonical order
        cleaned_query.sort(key=lambda x: x[0])
        new_query_str = urlencode(cleaned_query)
        
        # Normalize path
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]
        if not path:
            path = "/"
            
        canonical = urlunparse((
            scheme,
            netloc,
            path,
            "",  # params
            new_query_str,
            ""   # drop fragment/anchor
        ))
        return canonical
    except Exception:
        return raw_url.strip()

def normalize_title(title: str) -> str:
    """
    Cleans and standardizes title string for duplicate comparison and display.
    """
    if not title:
        return ""
    
    cleaned = title.strip()
    # Strip HTML entities if any
    cleaned = re.sub(r"&[a-z]+;|&#\d+;", " ", cleaned)
    
    # Strip brand suffixes
    for pat in SUFFIX_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
        
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def generate_content_hash(canonical_url: str, normalized_title: str, content: str = "") -> str:
    """
    Generates a deterministic SHA-256 hash representing the story signature.
    """
    base_str = f"{canonical_url.strip().lower()}||{normalized_title.strip().lower()}"
    if content:
        clean_snip = re.sub(r"\s+", " ", content.strip()[:500].lower())
        base_str += f"||{clean_snip}"
    return hashlib.sha256(base_str.encode("utf-8")).hexdigest()

def parse_published_date(raw_date: any) -> datetime:
    """
    Robustly parses various published date formats to timezone-aware UTC datetime.
    """
    if isinstance(raw_date, datetime):
        if raw_date.tzinfo is None:
            return raw_date.replace(tzinfo=timezone.utc)
        return raw_date.astimezone(timezone.utc)
    
    if not raw_date:
        return datetime.now(timezone.utc)
        
    if isinstance(raw_date, (int, float)):
        try:
            return datetime.fromtimestamp(raw_date, tz=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    if isinstance(raw_date, str):
        try:
            parsed = dateparser.parse(raw_date)
            if parsed:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
        except Exception:
            pass
            
    return datetime.now(timezone.utc)
