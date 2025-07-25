"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os

from ..config.settings import settings
print(f"[AutoCurate] Using database URL: {settings.database.url}")
from ..models.database import Base


# Create database engine
if "sqlite" in settings.database.url:
    engine = create_engine(
        settings.database.url,
        echo=settings.database.echo,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.database.url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        echo=settings.database.echo
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database with tables and sample data"""
    print("Creating database tables...")
    create_tables()
    
    # Add sample data if database is empty
    db = SessionLocal()
    try:
        from ..models.database import Website
        
        # Check if we have any websites
        website_count = db.query(Website).count()
        
        if website_count == 0:
            print("Adding sample websites...")
            sample_websites = [
                {
                    "url": "https://openai.com/blog",
                    "category": "AI Research & Tech Blogs",
                    "name": "OpenAI Blog",
                    "description": "Latest updates from OpenAI",
                    "scraping_frequency_hours": 24
                },
                {
                    "url": "https://ai.googleblog.com/",
                    "category": "AI Research & Tech Blogs", 
                    "name": "Google AI Blog",
                    "description": "Research and insights from Google AI",
                    "scraping_frequency_hours": 24
                },
                {
                    "url": "https://huggingface.co/blog",
                    "category": "AI Research & Tech Blogs",
                    "name": "Hugging Face Blog", 
                    "description": "Open source AI community updates",
                    "scraping_frequency_hours": 24
                },
                {
                    "url": "https://techcrunch.com/category/artificial-intelligence/",
                    "category": "Tech News",
                    "name": "TechCrunch AI",
                    "description": "AI news and startup coverage",
                    "scraping_frequency_hours": 12
                },
                {
                    "url": "https://www.theverge.com/ai-artificial-intelligence",
                    "category": "Tech News", 
                    "name": "The Verge AI",
                    "description": "Consumer AI technology news",
                    "scraping_frequency_hours": 12
                }
            ]
            
            for website_data in sample_websites:
                website = Website(**website_data)
                db.add(website)
            
            db.commit()
            print(f"Added {len(sample_websites)} sample websites")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Database initialization completed!")


if __name__ == "__main__":
    init_database()
