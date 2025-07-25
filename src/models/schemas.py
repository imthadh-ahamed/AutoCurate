"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ContentDepth(str, Enum):
    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class ContentFormat(str, Enum):
    BULLETS = "bullets"
    NARRATIVE = "narrative"
    TABULAR = "tabular"


class DeliveryFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class InteractionType(str, Enum):
    VIEW = "view"
    LIKE = "like"
    DISLIKE = "dislike"
    BOOKMARK = "bookmark"
    SHARE = "share"


# Website Models
class WebsiteBase(BaseModel):
    url: HttpUrl
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    scraping_enabled: bool = True
    scraping_frequency_hours: int = Field(default=24, ge=1)
    selector_config: Optional[Dict[str, Any]] = None


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    scraping_enabled: Optional[bool] = None
    scraping_frequency_hours: Optional[int] = Field(None, ge=1)
    selector_config: Optional[Dict[str, Any]] = None


class Website(WebsiteBase):
    id: int
    last_scraped: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Content Models
class ContentItemBase(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    language: Optional[str] = "en"


class ContentItemCreate(ContentItemBase):
    website_id: int


class ContentItem(ContentItemBase):
    id: int
    website_id: int
    cleaned_content: Optional[str] = None
    summary: Optional[str] = None
    scraped_at: datetime
    content_hash: Optional[str] = None
    word_count: Optional[int] = None
    is_processed: bool = False
    processing_status: str = "pending"
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# User Models
class UserBase(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    username: Optional[str] = None
    full_name: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# User Preference Models
class UserPreferenceBase(BaseModel):
    topics_of_interest: Optional[List[str]] = []
    preferred_categories: Optional[List[str]] = []
    content_depth: ContentDepth = ContentDepth.SUMMARY
    content_format: ContentFormat = ContentFormat.BULLETS
    content_length: str = Field(default="medium", pattern=r'^(short|medium|long)$')
    delivery_frequency: DeliveryFrequency = DeliveryFrequency.DAILY
    preferred_time: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    timezone: str = "UTC"
    language_preference: str = "en"
    include_summaries: bool = True
    include_key_points: bool = True
    include_trends: bool = False
    max_items_per_digest: int = Field(default=10, ge=1, le=50)
    feedback_enabled: bool = True
    personalization_enabled: bool = True


class UserPreferenceCreate(UserPreferenceBase):
    user_id: int


class UserPreferenceUpdate(UserPreferenceBase):
    pass


class UserPreference(UserPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Summary Models
class UserSummaryBase(BaseModel):
    title: Optional[str] = None
    summary_content: str
    summary_type: str = "daily_digest"
    content_items_included: Optional[List[int]] = []
    generation_prompt: Optional[str] = None
    llm_model_used: Optional[str] = None
    word_count: Optional[int] = None
    read_time_minutes: Optional[int] = None


class UserSummaryCreate(UserSummaryBase):
    user_id: int


class UserSummary(UserSummaryBase):
    id: int
    user_id: int
    is_read: bool = False
    read_at: Optional[datetime] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Interaction Models
class UserContentInteractionBase(BaseModel):
    interaction_type: InteractionType
    interaction_value: Optional[float] = None
    interaction_metadata: Optional[Dict[str, Any]] = None


class UserContentInteractionCreate(UserContentInteractionBase):
    user_id: int
    content_item_id: int


class UserContentInteraction(UserContentInteractionBase):
    id: int
    user_id: int
    content_item_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Survey Response Model
class SurveyResponse(BaseModel):
    """Complete survey response from the frontend"""
    user_id: int
    topics_of_interest: List[str]
    preferred_categories: List[str]
    content_preferences: Dict[str, str]  # depth, format, length
    delivery_preferences: Dict[str, Union[str, int]]  # frequency, time, timezone, max_items
    advanced_preferences: Dict[str, bool]  # summaries, key_points, trends, feedback, personalization
    
    @validator('content_preferences')
    def validate_content_preferences(cls, v):
        required_keys = {'depth', 'format', 'length'}
        if not all(key in v for key in required_keys):
            raise ValueError(f"Missing required content preference keys: {required_keys - set(v.keys())}")
        return v


# API Response Models
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class PaginatedResponse(BaseModel):
    """Paginated response for list endpoints"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# Scraping Job Models
class ScrapingJobBase(BaseModel):
    website_id: Optional[int] = None
    job_type: str = "manual"


class ScrapingJobCreate(ScrapingJobBase):
    pass


class ScrapingJob(ScrapingJobBase):
    id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items_scraped: int = 0
    items_processed: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics Models
class ContentAnalytics(BaseModel):
    """Analytics data for content performance"""
    total_items: int
    items_by_category: Dict[str, int]
    items_by_date: Dict[str, int]
    top_sources: List[Dict[str, Union[str, int]]]
    avg_word_count: float
    processing_stats: Dict[str, int]


class UserAnalytics(BaseModel):
    """Analytics data for user engagement"""
    total_users: int
    active_users: int
    summaries_generated: int
    avg_rating: float
    interaction_stats: Dict[str, int]
    preference_distribution: Dict[str, Any]
