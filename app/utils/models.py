"""Pydantic models for data validation."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator


class PageModel(BaseModel):
    """Model for page data validation."""
    url: str
    domain: str
    is_primary: bool
    title: Optional[str] = None
    description: Optional[str] = None
    h1: Optional[str] = None
    content_text: Optional[str] = None
    word_count: Optional[int] = Field(None, ge=0)
    schema_data: Optional[str] = None
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @field_validator('word_count')
    @classmethod
    def validate_word_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate word count is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Word count must be non-negative')
        return v


class ChunkModel(BaseModel):
    """Model for content chunk validation."""
    page_id: int = Field(gt=0)
    chunk_index: int = Field(ge=0)
    content: str = Field(min_length=1)
    token_count: int = Field(gt=0)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v


class EmbeddingModel(BaseModel):
    """Model for embedding validation."""
    chunk_id: int = Field(gt=0)
    embedding: List[float]
    model: str = Field(min_length=1)
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: List[float]) -> List[float]:
        """Validate embedding dimensions."""
        if not v or len(v) == 0:
            raise ValueError('Embedding cannot be empty')
        return v


class GapModel(BaseModel):
    """Model for gap data validation."""
    competitor_url: str
    gap_type: str = Field(pattern=r'^(missing_content|missing_page|thin_content|metadata_gap|schema_gap)$')
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    closest_match_url: Optional[str] = None
    analysis: Optional[str] = None
    priority: Optional[str] = Field(None, pattern=r'^(low|medium|high)$')
    
    @field_validator('competitor_url', 'closest_match_url')
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class CompetitorListModel(BaseModel):
    """Model for competitor URLs list validation."""
    competitors: List[str]
    
    @field_validator('competitors')
    @classmethod
    def validate_competitors(cls, v: List[str]) -> List[str]:
        """Validate competitor URLs."""
        if not v:
            raise ValueError('Competitor list cannot be empty')
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f'Invalid competitor URL: {url}')
        return v


class ReportModel(BaseModel):
    """Model for report data validation."""
    gaps: Dict[str, List[Dict[str, Any]]]
    summary: Dict[str, Any]
    action_plan: List[Dict[str, Any]]
    quick_wins: List[Dict[str, Any]]
    config: Dict[str, Any]
    
    @field_validator('gaps')
    @classmethod
    def validate_gaps(cls, v: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Validate gaps structure."""
        required_keys = {'missing_pages', 'thin_content', 'metadata_gaps', 'schema_gaps'}
        if not all(key in v for key in required_keys):
            raise ValueError(f'Gaps must contain all required keys: {required_keys}')
        return v
