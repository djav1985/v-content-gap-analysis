"""Configuration management for the SEO Gap Analysis Agent."""
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field, field_validator, ValidationError
from pydantic_settings import BaseSettings

from app.utils.logger import get_logger

logger = get_logger(__name__)


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
    chunk_size: int = Field(default=1500, gt=0, le=8000)
    max_chunks_per_page: int = Field(default=10, gt=0, le=50)
    max_pages_per_site: int = Field(default=50, gt=0, le=500)
    similarity_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    max_concurrent_requests: int = Field(default=10, gt=0, le=100)
    request_timeout: int = Field(default=30, gt=0, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0"
    
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    
    # OpenAI API key from environment
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    
    @field_validator('site')
    @classmethod
    def validate_site_url(cls, v: str) -> str:
        """Validate site URL format."""
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('Site URL must start with http:// or https://')
        return v

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
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid or empty
        ValidationError: If config data is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        error_msg = f"Configuration file not found: {config_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        if not config_data:
            error_msg = "Configuration file is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate and create Settings object
        settings = Settings(**config_data)
        logger.info(f"Successfully loaded configuration from {config_path}")
        return settings
        
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse YAML configuration: {e}"
        logger.error(error_msg)
        raise ValueError(f"Invalid YAML in configuration file: {e}") from e
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error loading configuration: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e


def load_competitors(competitors_path: str = "config/competitors.yaml") -> List[str]:
    """
    Load competitor sitemaps from YAML file.
    
    Args:
        competitors_path: Path to competitors file
        
    Returns:
        List of competitor sitemap URLs
        
    Raises:
        FileNotFoundError: If competitors file doesn't exist
        ValueError: If competitor file is invalid or empty
        ValidationError: If competitor data is invalid
    """
    competitors_file = Path(competitors_path)
    
    if not competitors_file.exists():
        error_msg = f"Competitors file not found: {competitors_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(competitors_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            error_msg = "Competitors file is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        competitors = data.get("competitors", [])
        
        if not competitors:
            error_msg = "No competitors found in configuration"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate competitor URLs
        from app.utils.models import CompetitorListModel
        validated = CompetitorListModel(competitors=competitors)
        
        logger.info(f"Successfully loaded {len(validated.competitors)} competitors")
        return validated.competitors
        
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse YAML competitors file: {e}"
        logger.error(error_msg)
        raise ValueError(f"Invalid YAML in competitors file: {e}") from e
    except ValidationError as e:
        logger.error(f"Competitor validation failed: {e}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error loading competitors: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e
