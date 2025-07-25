"""
AutoCurate Database Models
SQLAlchemy models for the AutoCurate system
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()


class Website(Base):
    """Website sources to scrape"""
    __tablename__ = "websites"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    category = Column(String(100), index=True)
    name = Column(String(200))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    scraping_enabled = Column(Boolean, default=True)
    last_scraped = Column(DateTime)
    scraping_frequency_hours = Column(Integer, default=24)
    selector_config = Column(JSON)  # Custom selectors for this website
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    content_items = relationship("ContentItem", back_populates="website")


class ContentItem(Base):
    """Scraped and processed content items"""
    __tablename__ = "content_items"
    
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    cleaned_content = Column(Text)
    summary = Column(Text)
    author = Column(String(200))
    published_date = Column(DateTime)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    content_hash = Column(String(64), index=True)  # For detecting duplicates
    word_count = Column(Integer)
    language = Column(String(10))
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Metadata extracted during processing
    content_metadata = Column(JSON)
    
    # Relationships
    website = relationship("Website", back_populates="content_items")
    chunks = relationship("ContentChunk", back_populates="content_item")
    user_interactions = relationship("UserContentInteraction", back_populates="content_item")


class ContentChunk(Base):
    """Text chunks for vector storage"""
    __tablename__ = "content_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within the content item
    vector_id = Column(String(100))  # ID in vector database
    embedding_model = Column(String(100))
    chunk_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="chunks")


class User(Base):
    """User accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    summaries = relationship("UserSummary", back_populates="user")
    interactions = relationship("UserContentInteraction", back_populates="user")


class UserPreference(Base):
    """User preferences collected via survey"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Interest categories
    topics_of_interest = Column(JSON)  # List of topics/categories
    preferred_categories = Column(JSON)  # Preferred website categories
    
    # Content preferences
    content_depth = Column(String(20), default="summary")  # summary, detailed, comprehensive
    content_format = Column(String(20), default="bullets")  # bullets, narrative, tabular
    content_length = Column(String(20), default="medium")  # short, medium, long
    
    # Delivery preferences
    delivery_frequency = Column(String(20), default="daily")  # daily, weekly, monthly
    preferred_time = Column(String(10))  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Advanced preferences
    language_preference = Column(String(10), default="en")
    include_summaries = Column(Boolean, default=True)
    include_key_points = Column(Boolean, default=True)
    include_trends = Column(Boolean, default=False)
    max_items_per_digest = Column(Integer, default=10)
    
    # Learning preferences
    feedback_enabled = Column(Boolean, default=True)
    personalization_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class UserSummary(Base):
    """Generated personalized summaries for users"""
    __tablename__ = "user_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300))
    summary_content = Column(Text)
    summary_type = Column(String(50))  # daily_digest, weekly_roundup, custom
    content_items_included = Column(JSON)  # List of content item IDs used
    generation_prompt = Column(Text)
    llm_model_used = Column(String(100))
    
    # Metrics
    word_count = Column(Integer)
    read_time_minutes = Column(Integer)
    
    # User interaction
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    user_rating = Column(Integer)  # 1-5 stars
    user_feedback = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="summaries")


class UserContentInteraction(Base):
    """Track user interactions with content for learning"""
    __tablename__ = "user_content_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    
    interaction_type = Column(String(50))  # view, like, dislike, bookmark, share
    interaction_value = Column(Float)  # Numeric value if applicable (rating, time spent, etc.)
    interaction_metadata = Column(JSON)  # Additional interaction data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    content_item = relationship("ContentItem", back_populates="user_interactions")


class ScrapingJob(Base):
    """Track scraping job status and results"""
    __tablename__ = "scraping_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    job_type = Column(String(50))  # scheduled, manual, batch
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    
    # Job details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    items_scraped = Column(Integer, default=0)
    items_processed = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemMetrics(Base):
    """System performance and usage metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    metric_tags = Column(JSON)  # Additional metadata/tags
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
