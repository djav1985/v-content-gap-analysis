"""Configuration management for the SEO Gap Analysis Agent."""
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelsConfig(BaseModel):
    """Model configuration."""
    embeddings: str = "text-embedding-3-large"
    llm: str = "gpt-4o-mini"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "data/pages.db"


class OutputConfig(BaseModel):
    """Output configuration."""
    json_report: str = "reports/gap_report.json"
    markdown_report: str = "reports/gap_report.md"


class ThresholdsConfig(BaseModel):
    """Analysis thresholds configuration."""
    thin_content_ratio: float = 3.0
    min_similarity: float = 0.45
    cluster_min_samples: int = 2


class Settings(BaseSettings):
    """Main application settings."""
    site: str
    chunk_size: int = 1500
    max_chunks_per_page: int = 10
    similarity_threshold: float = 0.45
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0"
    
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    
    # OpenAI API key from environment
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: str = "config/settings.yaml") -> Settings:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Settings object
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    return Settings(**config_data)


def load_competitors(competitors_path: str = "config/competitors.yaml") -> list[str]:
    """
    Load competitor sitemaps from YAML file.
    
    Args:
        competitors_path: Path to competitors file
        
    Returns:
        List of competitor sitemap URLs
    """
    competitors_file = Path(competitors_path)
    
    if not competitors_file.exists():
        raise FileNotFoundError(f"Competitors file not found: {competitors_path}")
    
    with open(competitors_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("competitors", [])
