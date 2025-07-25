"""
Celery tasks for content processing
"""

from celery import current_app
import asyncio
from loguru import logger

from ..celery_app import celery_app, run_async_task
from ..agents.vector_storage_agent import process_pending_content, VectorStorageAgent
from ..models.database import ContentItem
from ..core.database import get_db


@celery_app.task(bind=True, max_retries=2)
def process_pending_content_task(self):
    """
    Celery task to process pending content items for embedding generation
    """
    try:
        logger.info("Starting content processing task")
        run_async_task(process_pending_content)
        logger.info("Content processing task completed successfully")
        return {"status": "success", "message": "Content processing completed"}
    
    except Exception as e:
        logger.error(f"Content processing task failed: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying content processing task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=600, exc=e)  # Retry after 10 minutes
        
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=1)
def process_single_content_item_task(self, content_item_id: int):
    """
    Celery task to process a single content item
    
    Args:
        content_item_id: ID of the content item to process
    """
    try:
        logger.info(f"Starting processing task for content item {content_item_id}")
        
        # Get content item from database
        db = next(get_db())
        try:
            content_item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
            if not content_item:
                return {"status": "failed", "error": f"Content item {content_item_id} not found"}
        finally:
            db.close()
        
        # Process the content item
        async def process_item():
            agent = VectorStorageAgent()
            await agent.initialize()
            return await agent.process_content_item(content_item)
        
        success = run_async_task(process_item)
        
        if success:
            logger.info(f"Content item {content_item_id} processed successfully")
            return {"status": "success", "content_item_id": content_item_id}
        else:
            logger.error(f"Content item {content_item_id} processing failed")
            return {"status": "failed", "content_item_id": content_item_id, "error": "Processing failed"}
    
    except Exception as e:
        logger.error(f"Content item {content_item_id} processing failed: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying content item {content_item_id} processing (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=300, exc=e)  # Retry after 5 minutes
        
        return {"status": "failed", "content_item_id": content_item_id, "error": str(e)}


@celery_app.task
def process_content_by_category_task(category: str):
    """
    Celery task to process all unprocessed content items from a specific category
    
    Args:
        category: Category of content to process
    """
    try:
        logger.info(f"Starting category content processing task for: {category}")
        
        # Get unprocessed content items in category
        db = next(get_db())
        try:
            from ..models.database import Website
            content_items = db.query(ContentItem).join(Website).filter(
                Website.category == category,
                ContentItem.is_processed == False,
                ContentItem.processing_status == "pending"
            ).limit(50).all()  # Process in batches
        finally:
            db.close()
        
        if not content_items:
            return {"status": "success", "message": f"No pending content found for category: {category}"}
        
        # Process each content item
        results = []
        for content_item in content_items:
            try:
                # Queue individual processing tasks
                task_result = process_single_content_item_task.delay(content_item.id)
                results.append({
                    "content_item_id": content_item.id,
                    "task_id": task_result.id,
                    "status": "queued"
                })
            except Exception as e:
                logger.error(f"Failed to queue processing for content item {content_item.id}: {e}")
                results.append({
                    "content_item_id": content_item.id,
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(f"Category processing task completed for {category}. Queued {len(results)} items")
        return {
            "status": "success", 
            "category": category,
            "items_queued": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Category processing task failed for {category}: {e}")
        return {"status": "failed", "category": category, "error": str(e)}


@celery_app.task
def cleanup_failed_processing_task():
    """
    Celery task to reset failed content processing jobs for retry
    """
    try:
        logger.info("Starting cleanup of failed processing jobs")
        
        db = next(get_db())
        try:
            # Reset content items that have been stuck in "processing" status for too long
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            stuck_items = db.query(ContentItem).filter(
                ContentItem.processing_status == "processing",
                ContentItem.scraped_at < cutoff_time
            ).all()
            
            reset_count = 0
            for item in stuck_items:
                item.processing_status = "pending"
                reset_count += 1
            
            # Reset failed items that are older than 24 hours for another attempt
            failed_cutoff = datetime.utcnow() - timedelta(hours=24)
            failed_items = db.query(ContentItem).filter(
                ContentItem.processing_status == "failed",
                ContentItem.scraped_at < failed_cutoff
            ).all()
            
            for item in failed_items:
                item.processing_status = "pending"
                reset_count += 1
            
            db.commit()
            
            logger.info(f"Cleanup completed. Reset {reset_count} content items for retry")
            return {"status": "success", "items_reset": reset_count}
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"status": "failed", "error": str(e)}


# Task aliases for backward compatibility
process_pending_content = process_pending_content_task
