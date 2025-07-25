"""
Celery tasks for content scraping
"""

from celery import current_app
import asyncio
from loguru import logger

from ..celery_app import celery_app, run_async_task
from ..agents.website_ingest_agent import run_scheduled_scraping, WebsiteIngestAgent
from ..models.database import Website
from ..core.database import get_db


@celery_app.task(bind=True, max_retries=3)
def run_scheduled_scraping_task(self):
    """
    Celery task to run scheduled scraping for all websites
    """
    try:
        logger.info("Starting scheduled scraping task")
        result = run_async_task(run_scheduled_scraping)
        logger.info("Scheduled scraping task completed successfully")
        return {"status": "success", "message": "Scraping completed"}
    
    except Exception as e:
        logger.error(f"Scheduled scraping task failed: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying scraping task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=300, exc=e)  # Retry after 5 minutes
        
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=2)
def scrape_single_website_task(self, website_id: int):
    """
    Celery task to scrape a single website
    
    Args:
        website_id: ID of the website to scrape
    """
    try:
        logger.info(f"Starting scraping task for website {website_id}")
        
        # Get website from database
        db = next(get_db())
        try:
            website = db.query(Website).filter(Website.id == website_id).first()
            if not website:
                return {"status": "failed", "error": f"Website {website_id} not found"}
        finally:
            db.close()
        
        # Run scraping
        async def scrape_website():
            async with WebsiteIngestAgent() as agent:
                return await agent.scrape_website(website)
        
        result = run_async_task(scrape_website)
        
        logger.info(f"Website {website_id} scraping completed: {result}")
        return {"status": "success", "website_id": website_id, "results": result}
    
    except Exception as e:
        logger.error(f"Website {website_id} scraping failed: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying website {website_id} scraping (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=180, exc=e)  # Retry after 3 minutes
        
        return {"status": "failed", "website_id": website_id, "error": str(e)}


@celery_app.task
def scrape_websites_by_category_task(category: str):
    """
    Celery task to scrape all websites in a specific category
    
    Args:
        category: Category of websites to scrape
    """
    try:
        logger.info(f"Starting category scraping task for: {category}")
        
        # Get websites in category
        db = next(get_db())
        try:
            websites = db.query(Website).filter(
                Website.category == category,
                Website.is_active == True,
                Website.scraping_enabled == True
            ).all()
        finally:
            db.close()
        
        if not websites:
            return {"status": "success", "message": f"No active websites found for category: {category}"}
        
        # Scrape each website
        results = []
        for website in websites:
            try:
                # Queue individual scraping tasks
                task_result = scrape_single_website_task.delay(website.id)
                results.append({
                    "website_id": website.id,
                    "task_id": task_result.id,
                    "status": "queued"
                })
            except Exception as e:
                logger.error(f"Failed to queue scraping for website {website.id}: {e}")
                results.append({
                    "website_id": website.id,
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(f"Category scraping task completed for {category}. Queued {len(results)} websites")
        return {
            "status": "success", 
            "category": category,
            "websites_queued": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Category scraping task failed for {category}: {e}")
        return {"status": "failed", "category": category, "error": str(e)}


# Task aliases for backward compatibility
run_scheduled_scraping = run_scheduled_scraping_task
