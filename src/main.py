"""
AutoCurate FastAPI Application
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime

from .config.settings import settings
from .core.database import get_db, init_database
from .models import schemas
from .models.database import Website, ContentItem, User, UserPreference, UserSummary, UserContentInteraction
from .agents.website_ingest_agent import WebsiteIngestAgent
from .agents.vector_storage_agent import VectorStorageAgent
from .agents.user_preference_agent import UserPreferenceAgent
from .agents.summary_agent import SummaryAgent
from .agents.feedback_agent import FeedbackAgent

# Initialize FastAPI app
app = FastAPI(
    title="AutoCurate API",
    description="AI-Powered Personalized Knowledge Feed from Web Sources",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize agents (will be done at startup)
agents = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    print("Starting AutoCurate API...")
    
    # Initialize database
    init_database()
    
    # Initialize agents
    print("Initializing agents...")
    agents['vector_storage'] = VectorStorageAgent()
    await agents['vector_storage'].initialize()
    
    agents['user_preference'] = UserPreferenceAgent()
    agents['summary'] = SummaryAgent()
    await agents['summary'].initialize()
    
    agents['feedback'] = FeedbackAgent()
    
    print("AutoCurate API started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down AutoCurate API...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Website Management Endpoints
@app.post("/api/websites", response_model=schemas.Website)
async def create_website(website: schemas.WebsiteCreate, db: Session = Depends(get_db)):
    """Create a new website to scrape"""
    try:
        db_website = Website(**website.dict())
        db.add(db_website)
        db.commit()
        db.refresh(db_website)
        return db_website
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create website: {str(e)}")


@app.get("/api/websites", response_model=List[schemas.Website])
async def get_websites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of websites"""
    websites = db.query(Website).filter(Website.is_active == True).offset(skip).limit(limit).all()
    return websites


@app.get("/api/websites/{website_id}", response_model=schemas.Website)
async def get_website(website_id: int, db: Session = Depends(get_db)):
    """Get a specific website"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website


@app.put("/api/websites/{website_id}", response_model=schemas.Website)
async def update_website(website_id: int, website_update: schemas.WebsiteUpdate, db: Session = Depends(get_db)):
    """Update a website"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    update_data = website_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(website, field, value)
    
    db.commit()
    db.refresh(website)
    return website


@app.delete("/api/websites/{website_id}")
async def delete_website(website_id: int, db: Session = Depends(get_db)):
    """Delete a website"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    website.is_active = False
    db.commit()
    return {"message": "Website deleted successfully"}


# Content Management Endpoints
@app.get("/api/content", response_model=List[schemas.ContentItem])
async def get_content(
    skip: int = 0, 
    limit: int = 20, 
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get content items"""
    query = db.query(ContentItem).filter(ContentItem.is_processed == True)
    
    if category:
        query = query.join(Website).filter(Website.category == category)
    
    content_items = query.order_by(ContentItem.scraped_at.desc()).offset(skip).limit(limit).all()
    return content_items


@app.get("/api/content/{content_id}", response_model=schemas.ContentItem)
async def get_content_item(content_id: int, db: Session = Depends(get_db)):
    """Get a specific content item"""
    content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not content_item:
        raise HTTPException(status_code=404, detail="Content item not found")
    return content_item


# User Management Endpoints
@app.post("/api/users", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")


@app.get("/api/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# User Preference Endpoints
@app.get("/api/users/{user_id}/survey")
async def get_user_survey(user_id: int, db: Session = Depends(get_db)):
    """Get dynamic survey for user preferences"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    survey = agents['user_preference'].create_dynamic_survey(user_id)
    return survey


@app.post("/api/users/{user_id}/survey")
async def submit_survey_response(user_id: int, survey_response: schemas.SurveyResponse, db: Session = Depends(get_db)):
    """Submit survey response and create/update user preferences"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = agents['user_preference'].process_survey_response(survey_response)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process survey response")
    
    return {"message": "Survey response processed successfully"}


@app.get("/api/users/{user_id}/preferences", response_model=schemas.UserPreference)
async def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    """Get user preferences"""
    preferences = agents['user_preference'].get_user_preferences(user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    return preferences


@app.put("/api/users/{user_id}/preferences")
async def update_user_preferences(user_id: int, updates: Dict[str, Any], db: Session = Depends(get_db)):
    """Update user preferences"""
    success = agents['user_preference'].update_user_preferences(user_id, updates)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update preferences")
    
    return {"message": "Preferences updated successfully"}


@app.post("/api/users/preferences")
async def save_user_preferences(preferences: dict):
    """Save user preferences (stub)"""
    # You can add DB logic here to store preferences
    return {"message": "Preferences received", "preferences": preferences}


# Summary Endpoints
@app.post("/api/users/{user_id}/summaries")
async def generate_summary(
    user_id: int, 
    summary_type: str = "daily_digest",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Generate a personalized summary for a user"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate summary in background
    background_tasks.add_task(
        generate_summary_task, user_id, summary_type
    )
    
    return {"message": f"Summary generation started for user {user_id}"}


async def generate_summary_task(user_id: int, summary_type: str):
    """Background task to generate summary"""
    try:
        summary = await agents['summary'].generate_personalized_summary(user_id, summary_type)
        if summary:
            print(f"Generated summary {summary['id']} for user {user_id}")
        else:
            print(f"Failed to generate summary for user {user_id}")
    except Exception as e:
        print(f"Error in summary generation task: {e}")


@app.get("/api/users/{user_id}/summaries", response_model=List[schemas.UserSummary])
async def get_user_summaries(
    user_id: int, 
    skip: int = 0, 
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get user's summaries"""
    summaries = db.query(UserSummary).filter(
        UserSummary.user_id == user_id
    ).order_by(UserSummary.created_at.desc()).offset(skip).limit(limit).all()
    
    return summaries


@app.get("/api/users/{user_id}/summaries/{summary_id}", response_model=schemas.UserSummary)
async def get_user_summary(user_id: int, summary_id: int, db: Session = Depends(get_db)):
    """Get a specific user summary"""
    summary = db.query(UserSummary).filter(
        UserSummary.id == summary_id,
        UserSummary.user_id == user_id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Mark as read
    if not summary.is_read:
        summary.is_read = True
        summary.read_at = datetime.utcnow()
        db.commit()
    
    return summary


# Feedback Endpoints
@app.post("/api/users/{user_id}/interactions")
async def record_interaction(
    user_id: int, 
    interaction: schemas.UserContentInteractionCreate,
    db: Session = Depends(get_db)
):
    """Record user interaction with content"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify content exists
    content = db.query(ContentItem).filter(ContentItem.id == interaction.content_item_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    success = agents['feedback'].record_interaction(interaction)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record interaction")
    
    return {"message": "Interaction recorded successfully"}


@app.post("/api/users/{user_id}/summaries/{summary_id}/feedback")
async def submit_summary_feedback(
    user_id: int, 
    summary_id: int,
    rating: Optional[int] = None,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Submit feedback on a summary"""
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    success = agents['feedback'].record_summary_feedback(user_id, summary_id, rating, feedback)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record feedback")
    
    return {"message": "Feedback recorded successfully"}


# Analytics Endpoints
@app.get("/api/users/{user_id}/analytics")
async def get_user_analytics(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get user interaction analytics"""
    analytics = agents['feedback'].get_user_interaction_analytics(user_id, days)
    return analytics


@app.get("/api/analytics/content")
async def get_content_analytics(days: int = 30, db: Session = Depends(get_db)):
    """Get content performance analytics"""
    analytics = agents['feedback'].get_content_performance_analytics(days)
    return analytics


# Search Endpoints
@app.get("/api/search")
async def search_content(q: str, limit: int = 10, db: Session = Depends(get_db)):
    """Search content using vector similarity"""
    try:
        results = await agents['vector_storage'].search_similar_content(q, limit)
        
        # Get full content details for results
        content_items = []
        for result in results:
            if 'content_item_id' in result['metadata']:
                content_item = db.query(ContentItem).filter(
                    ContentItem.id == result['metadata']['content_item_id']
                ).first()
                
                if content_item:
                    content_items.append({
                        'id': content_item.id,
                        'title': content_item.title,
                        'url': content_item.url,
                        'summary': content_item.summary,
                        'author': content_item.author,
                        'published_date': content_item.published_date,
                        'similarity_score': result['score'],
                        'category': getattr(content_item.website, 'category', 'Unknown') if hasattr(content_item, 'website') else 'Unknown'
                    })
        
        return {"query": q, "results": content_items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Admin/Management Endpoints
@app.post("/api/admin/scrape")
async def trigger_scraping(
    website_id: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Trigger content scraping"""
    if website_id:
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        background_tasks.add_task(scrape_single_website, website_id)
        return {"message": f"Scraping started for website {website_id}"}
    else:
        background_tasks.add_task(scrape_all_websites)
        return {"message": "Scraping started for all websites"}


async def scrape_single_website(website_id: int):
    """Background task to scrape a single website"""
    try:
        db = next(get_db())
        website = db.query(Website).filter(Website.id == website_id).first()
        db.close()
        
        if website:
            async with WebsiteIngestAgent() as agent:
                results = await agent.scrape_website(website)
                print(f"Scraping results for website {website_id}: {results}")
    except Exception as e:
        print(f"Error scraping website {website_id}: {e}")


async def scrape_all_websites():
    """Background task to scrape all active websites"""
    try:
        from .agents.website_ingest_agent import run_scheduled_scraping
        await run_scheduled_scraping()
    except Exception as e:
        print(f"Error in scheduled scraping: {e}")


@app.post("/api/admin/process-content")
async def trigger_content_processing(background_tasks: BackgroundTasks = BackgroundTasks()):
    """Trigger content processing for embeddings"""
    background_tasks.add_task(process_content_task)
    return {"message": "Content processing started"}


async def process_content_task():
    """Background task to process content"""
    try:
        from .agents.vector_storage_agent import process_pending_content
        await process_pending_content()
    except Exception as e:
        print(f"Error processing content: {e}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower()
    )
