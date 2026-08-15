import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "CLIVE"
    APP_VERSION: str = "1.0.0"
    TAGLINE: str = "Your signal in the AI noise."
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_radar.db"
    
    # AI - Server-side Gemini configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_CLASSIFIER_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_SUMMARY_MODEL: str = "gemini-3.6-flash"
    GEMINI_TIMEOUT_SECONDS: float = 15.0
    
    # Threshold for summary generation
    MIN_IMPORTANCE_FOR_SUMMARY: float = 6.5
    IMPORTANCE_SUMMARY_THRESHOLD: float = 65.0
    
    # Feed Ingestion Interval
    COLLECT_INTERVAL_MINUTES: int = 10
    SCAN_INTERVAL_MINUTES: int = 10
    HTTP_TIMEOUT_SECONDS: float = 12.0
    MAX_ITEMS_PER_FEED: int = 25
    USER_AGENT: str = "CLIVE-AI-Intelligence/1.0 (+https://github.com/founderlabs/clive)"
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Ranking Weights (40% Importance + 30% Personal Relevance + 20% Recency + 10% Novelty)
    WEIGHT_IMPORTANCE: float = 0.40
    WEIGHT_RELEVANCE: float = 0.30
    WEIGHT_RECENCY: float = 0.20
    WEIGHT_NOVELTY: float = 0.10
    BREAKING_BOOST: float = 15.0

    # Configurable Preference Weight Deltas
    WEIGHT_DELTA_LIKE: float = 0.25
    WEIGHT_DELTA_DISLIKE: float = -0.12
    WEIGHT_DELTA_SAVE: float = 0.40
    WEIGHT_DELTA_SOURCE_OPEN: float = 0.15
    WEIGHT_DELTA_OPEN: float = 0.10
    WEIGHT_DELTA_SHARE: float = 0.30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    def model_post_init(self, __context):
        # Synchronize COLLECT_INTERVAL_MINUTES with SCAN_INTERVAL_MINUTES
        if self.COLLECT_INTERVAL_MINUTES:
            self.SCAN_INTERVAL_MINUTES = self.COLLECT_INTERVAL_MINUTES
        # Synchronize MIN_IMPORTANCE_FOR_SUMMARY to standard 0-100 scale
        if self.MIN_IMPORTANCE_FOR_SUMMARY <= 10.0 and self.MIN_IMPORTANCE_FOR_SUMMARY > 0:
            self.IMPORTANCE_SUMMARY_THRESHOLD = self.MIN_IMPORTANCE_FOR_SUMMARY * 10.0
        else:
            self.IMPORTANCE_SUMMARY_THRESHOLD = self.MIN_IMPORTANCE_FOR_SUMMARY

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
