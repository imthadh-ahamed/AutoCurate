"""
Summary generation tasks for Celery.
Handles personalized content summarization and periodic updates.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from celery import Task
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..core.database import get_db
from ..agents.summary_agent import SummaryAgent
from ..agents.user_preference_agent import UserPreferenceAgent
from ..models.database import User, UserSummary, ContentItem
from ..config.settings import get_settings

settings = get_settings()


class AsyncTask(Task):
    """Base class for async Celery tasks."""
    
    def __call__(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._run(*args, **kwargs))
        finally:
            loop.close()
    
    async def _run(self, *args, **kwargs):
        raise NotImplementedError


@celery_app.task(base=AsyncTask, bind=True, max_retries=3)
async def generate_user_summary(self, user_id: int, force_regenerate: bool = False) -> Dict[str, Any]:
    """
    Generate personalized summary for a specific user.
    
    Args:
        user_id: ID of the user
        force_regenerate: Whether to force regeneration even if recent summary exists
        
    Returns:
        Dict containing summary generation results
    """
    try:
        db = next(get_db())
        
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": f"User {user_id} not found"}
        
        # Check if recent summary exists (unless force regenerate)
        if not force_regenerate:
            recent_summary = db.query(UserSummary).filter(
                UserSummary.user_id == user_id,
                UserSummary.created_at > datetime.utcnow() - timedelta(hours=6)
            ).first()
            
            if recent_summary:
                return {
                    "status": "skipped",
                    "message": "Recent summary exists",
                    "summary_id": recent_summary.id
                }
        
        # Initialize agents
        summary_agent = SummaryAgent()
        preference_agent = UserPreferenceAgent()
        
        # Get user preferences
        preferences = await preference_agent.get_user_preferences(user_id)
        
        # Generate summary
        summary_result = await summary_agent.generate_personalized_summary(
            user_id=user_id,
            preferences=preferences
        )
        
        if summary_result["status"] == "success":
            return {
                "status": "success",
                "summary_id": summary_result["summary_id"],
                "content_count": summary_result["content_count"],
                "user_id": user_id
            }
        else:
            return {
                "status": "error",
                "message": summary_result.get("message", "Unknown error"),
                "user_id": user_id
            }
            
    except Exception as exc:
        self.retry(countdown=60 * (self.request.retries + 1), exc=exc)
        return {
            "status": "error",
            "message": str(exc),
            "user_id": user_id
        }


@celery_app.task(base=AsyncTask, bind=True)
async def generate_summaries_for_all_users(self) -> Dict[str, Any]:
    """
    Generate summaries for all active users.
    
    Returns:
        Dict containing batch generation results
    """
    try:
        db = next(get_db())
        
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        results = {
            "total_users": len(active_users),
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        for user in active_users:
            try:
                result = await generate_user_summary._run(user.id)
                
                if result["status"] == "success":
                    results["successful"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": user.id,
                        "error": result.get("message", "Unknown error")
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user.id,
                    "error": str(e)
                })
        
        return results
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "total_users": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }


@celery_app.task(base=AsyncTask, bind=True)
async def update_trending_topics(self) -> Dict[str, Any]:
    """
    Analyze content to identify trending topics and update summary contexts.
    
    Returns:
        Dict containing trending topics analysis results
    """
    try:
        db = next(get_db())
        
        # Get recent content (last 24 hours)
        recent_content = db.query(ContentItem).filter(
            ContentItem.scraped_at > datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        if not recent_content:
            return {
                "status": "success",
                "message": "No recent content to analyze",
                "trending_topics": []
            }
        
        summary_agent = SummaryAgent()
        
        # Extract topics from recent content
        content_texts = [item.content for item in recent_content if item.content]
        trending_topics = await summary_agent.extract_trending_topics(content_texts)
        
        # Store trending topics in cache or database for future use
        # This could be implemented as a separate table or cache mechanism
        
        return {
            "status": "success",
            "trending_topics": trending_topics,
            "content_analyzed": len(content_texts),
            "analysis_time": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "trending_topics": []
        }


@celery_app.task(base=AsyncTask, bind=True, max_retries=2)
async def cleanup_old_summaries(self, days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old summaries to maintain database performance.
    
    Args:
        days_to_keep: Number of days of summaries to keep
        
    Returns:
        Dict containing cleanup results
    """
    try:
        db = next(get_db())
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count old summaries
        old_summaries = db.query(UserSummary).filter(
            UserSummary.created_at < cutoff_date
        )
        
        count_to_delete = old_summaries.count()
        
        if count_to_delete == 0:
            return {
                "status": "success",
                "message": "No old summaries to clean up",
                "deleted_count": 0
            }
        
        # Delete old summaries
        deleted_count = old_summaries.delete()
        db.commit()
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep
        }
        
    except Exception as exc:
        db.rollback()
        self.retry(countdown=300, exc=exc)
        return {
            "status": "error",
            "message": str(exc),
            "deleted_count": 0
        }


@celery_app.task(base=AsyncTask, bind=True)
async def generate_summary_analytics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate analytics about summary performance and user engagement.
    
    Args:
        user_id: Optional specific user ID to analyze
        
    Returns:
        Dict containing analytics results
    """
    try:
        db = next(get_db())
        
        # Base query
        summary_query = db.query(UserSummary)
        
        if user_id:
            summary_query = summary_query.filter(UserSummary.user_id == user_id)
        
        # Get summaries from last 30 days
        recent_summaries = summary_query.filter(
            UserSummary.created_at > datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if not recent_summaries:
            return {
                "status": "success",
                "message": "No recent summaries found",
                "analytics": {}
            }
        
        # Calculate analytics
        total_summaries = len(recent_summaries)
        avg_content_items = sum(s.content_count for s in recent_summaries) / total_summaries
        
        # User engagement metrics (if interactions are tracked)
        engagement_scores = [s.engagement_score for s in recent_summaries if s.engagement_score]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        
        # Summary length analysis
        summary_lengths = [len(s.summary_text) for s in recent_summaries if s.summary_text]
        avg_length = sum(summary_lengths) / len(summary_lengths) if summary_lengths else 0
        
        analytics = {
            "period_days": 30,
            "total_summaries": total_summaries,
            "avg_content_items_per_summary": round(avg_content_items, 2),
            "avg_engagement_score": round(avg_engagement, 2),
            "avg_summary_length": round(avg_length, 2),
            "unique_users": len(set(s.user_id for s in recent_summaries)),
            "analysis_date": datetime.utcnow().isoformat()
        }
        
        if user_id:
            analytics["user_id"] = user_id
        
        return {
            "status": "success",
            "analytics": analytics
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "analytics": {}
        }


# Periodic tasks
@celery_app.task(base=AsyncTask, name="daily_summary_generation")
async def daily_summary_generation():
    """Daily task to generate summaries for all users."""
    return await generate_summaries_for_all_users._run()


@celery_app.task(base=AsyncTask, name="hourly_trending_update")
async def hourly_trending_update():
    """Hourly task to update trending topics."""
    return await update_trending_topics._run()


@celery_app.task(base=AsyncTask, name="weekly_summary_cleanup")
async def weekly_summary_cleanup():
    """Weekly task to clean up old summaries."""
    return await cleanup_old_summaries._run(days_to_keep=30)
