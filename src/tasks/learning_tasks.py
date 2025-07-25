"""
Learning and preference update tasks for Celery.
Handles user feedback processing and preference learning.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from celery import Task
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..core.database import get_db
from ..agents.feedback_agent import FeedbackAgent
from ..agents.user_preference_agent import UserPreferenceAgent
from ..models.database import User, UserContentInteraction, UserPreference, ContentItem
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
async def process_user_feedback(self, user_id: int, content_id: int, 
                               interaction_type: str, rating: Optional[int] = None) -> Dict[str, Any]:
    """
    Process user feedback and update preferences accordingly.
    
    Args:
        user_id: ID of the user providing feedback
        content_id: ID of the content being rated
        interaction_type: Type of interaction (like, dislike, save, share, etc.)
        rating: Optional numeric rating (1-5)
        
    Returns:
        Dict containing processing results
    """
    try:
        db = next(get_db())
        
        # Verify user and content exist
        user = db.query(User).filter(User.id == user_id).first()
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        
        if not user:
            return {"status": "error", "message": f"User {user_id} not found"}
        
        if not content:
            return {"status": "error", "message": f"Content {content_id} not found"}
        
        # Initialize agents
        feedback_agent = FeedbackAgent()
        preference_agent = UserPreferenceAgent()
        
        # Process the feedback
        feedback_result = await feedback_agent.process_feedback(
            user_id=user_id,
            content_id=content_id,
            interaction_type=interaction_type,
            rating=rating
        )
        
        if feedback_result["status"] == "success":
            # Update user preferences based on feedback
            preference_update = await preference_agent.update_preferences_from_interaction(
                user_id=user_id,
                content=content,
                interaction_type=interaction_type,
                rating=rating
            )
            
            return {
                "status": "success",
                "feedback_processed": True,
                "preferences_updated": preference_update.get("updated", False),
                "interaction_id": feedback_result.get("interaction_id"),
                "user_id": user_id,
                "content_id": content_id
            }
        else:
            return {
                "status": "error",
                "message": feedback_result.get("message", "Failed to process feedback"),
                "user_id": user_id,
                "content_id": content_id
            }
            
    except Exception as exc:
        self.retry(countdown=60 * (self.request.retries + 1), exc=exc)
        return {
            "status": "error",
            "message": str(exc),
            "user_id": user_id,
            "content_id": content_id
        }


@celery_app.task(base=AsyncTask, bind=True)
async def analyze_user_behavior_patterns(self, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Analyze user behavior patterns to improve personalization.
    
    Args:
        user_id: Optional specific user ID to analyze, if None analyzes all users
        
    Returns:
        Dict containing analysis results
    """
    try:
        db = next(get_db())
        
        # Base query for interactions
        interaction_query = db.query(UserContentInteraction)
        
        if user_id:
            interaction_query = interaction_query.filter(UserContentInteraction.user_id == user_id)
        
        # Get recent interactions (last 30 days)
        recent_interactions = interaction_query.filter(
            UserContentInteraction.created_at > datetime.now() - timedelta(days=30)
        ).all()
        
        if not recent_interactions:
            return {
                "status": "success",
                "message": "No recent interactions found",
                "patterns": {}
            }
        
        feedback_agent = FeedbackAgent()
        
        # Analyze patterns
        patterns = await feedback_agent.analyze_behavior_patterns(recent_interactions)
        
        # Update user preferences based on patterns
        if user_id and patterns:
            preference_agent = UserPreferenceAgent()
            await preference_agent.update_preferences_from_patterns(user_id, patterns)
        
        return {
            "status": "success",
            "patterns": patterns,
            "interactions_analyzed": len(recent_interactions),
            "user_id": user_id,
            "analysis_date": datetime.now().isoformat()
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "patterns": {},
            "user_id": user_id
        }


@celery_app.task(base=AsyncTask, bind=True)
async def update_content_recommendations(self, user_id: int) -> Dict[str, Any]:
    """
    Update content recommendations based on latest user preferences.
    
    Args:
        user_id: ID of the user to update recommendations for
        
    Returns:
        Dict containing recommendation update results
    """
    try:
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": f"User {user_id} not found"}
        
        preference_agent = UserPreferenceAgent()
        
        # Get updated preferences
        preferences = await preference_agent.get_user_preferences(user_id)
        
        # Generate new content recommendations
        recommendations = await preference_agent.generate_content_recommendations(
            user_id=user_id,
            preferences=preferences
        )
        
        return {
            "status": "success",
            "recommendations_count": len(recommendations),
            "user_id": user_id,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "user_id": user_id
        }


@celery_app.task(base=AsyncTask, bind=True, max_retries=2)
async def cleanup_old_interactions(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old user interactions while preserving learning data.
    
    Args:
        days_to_keep: Number of days of interactions to keep
        
    Returns:
        Dict containing cleanup results
    """
    try:
        db = next(get_db())
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Count old interactions (keep more recent ones for learning)
        old_interactions = db.query(UserContentInteraction).filter(
            UserContentInteraction.created_at < cutoff_date,
            UserContentInteraction.interaction_type.in_(['view', 'click'])  # Remove less important interactions first
        )
        
        count_to_delete = old_interactions.count()
        
        if count_to_delete == 0:
            return {
                "status": "success",
                "message": "No old interactions to clean up",
                "deleted_count": 0
            }
        
        # Delete old interactions
        deleted_count = old_interactions.delete()
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
async def retrain_user_preferences(self, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrain user preference models based on accumulated feedback.
    
    Args:
        user_id: Optional specific user ID to retrain, if None retrains all users
        
    Returns:
        Dict containing retraining results
    """
    try:
        db = next(get_db())
        
        # Get users to retrain
        if user_id:
            users = db.query(User).filter(User.id == user_id, User.is_active == True).all()
        else:
            users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            return {
                "status": "success",
                "message": "No users found for retraining",
                "retrained_users": 0
            }
        
        preference_agent = UserPreferenceAgent()
        retrained_count = 0
        errors = []
        
        for user in users:
            try:
                # Get user's interaction history
                interactions = db.query(UserContentInteraction).filter(
                    UserContentInteraction.user_id == user.id,
                    UserContentInteraction.created_at > datetime.now() - timedelta(days=90)
                ).all()
                
                if len(interactions) < 5:  # Need minimum interactions for retraining
                    continue
                
                # Retrain preferences
                retrain_result = await preference_agent.retrain_user_model(
                    user_id=user.id,
                    interactions=interactions
                )
                
                if retrain_result.get("success", False):
                    retrained_count += 1
                else:
                    errors.append({
                        "user_id": user.id,
                        "error": retrain_result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                errors.append({
                    "user_id": user.id,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "total_users": len(users),
            "retrained_users": retrained_count,
            "errors": errors,
            "retrain_date": datetime.now().isoformat()
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "retrained_users": 0
        }


@celery_app.task(base=AsyncTask, bind=True)
async def generate_learning_insights(self) -> Dict[str, Any]:
    """
    Generate insights about the learning system performance.
    
    Returns:
        Dict containing learning insights
    """
    try:
        db = next(get_db())
        
        # Get recent interactions and feedback
        recent_interactions = db.query(UserContentInteraction).filter(
            UserContentInteraction.created_at > datetime.now() - timedelta(days=7)
        ).all()
        
        # Calculate engagement metrics
        total_interactions = len(recent_interactions)
        positive_interactions = len([i for i in recent_interactions 
                                   if i.interaction_type in ['like', 'save', 'share']])
        negative_interactions = len([i for i in recent_interactions 
                                   if i.interaction_type in ['dislike', 'skip']])
        
        # User activity metrics
        active_users = len({i.user_id for i in recent_interactions})
        avg_interactions_per_user = total_interactions / active_users if active_users > 0 else 0
        
        # Content performance
        content_interactions = {}
        for interaction in recent_interactions:
            content_id = interaction.content_id
            if content_id not in content_interactions:
                content_interactions[content_id] = {"positive": 0, "negative": 0, "total": 0}
            
            content_interactions[content_id]["total"] += 1
            if interaction.interaction_type in ['like', 'save', 'share']:
                content_interactions[content_id]["positive"] += 1
            elif interaction.interaction_type in ['dislike', 'skip']:
                content_interactions[content_id]["negative"] += 1
        
        # Calculate engagement rate
        engagement_rate = (positive_interactions / total_interactions * 100) if total_interactions > 0 else 0
        
        insights = {
            "period_days": 7,
            "total_interactions": total_interactions,
            "positive_interactions": positive_interactions,
            "negative_interactions": negative_interactions,
            "engagement_rate": round(engagement_rate, 2),
            "active_users": active_users,
            "avg_interactions_per_user": round(avg_interactions_per_user, 2),
            "top_performing_content": sorted(
                [(cid, data["positive"] / data["total"] * 100) 
                 for cid, data in content_interactions.items() if data["total"] >= 5],
                key=lambda x: x[1], reverse=True
            )[:10],
            "analysis_date": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "insights": insights
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "insights": {}
        }


# Periodic tasks
@celery_app.task(base=AsyncTask, name="hourly_behavior_analysis")
async def hourly_behavior_analysis():
    """Hourly task to analyze user behavior patterns."""
    return await analyze_user_behavior_patterns._run()


@celery_app.task(base=AsyncTask, name="daily_preference_updates")
async def daily_preference_updates():
    """Daily task to update user preferences based on recent activity."""
    db = next(get_db())
    active_users = db.query(User).filter(User.is_active == True).all()
    
    results = []
    for user in active_users:
        result = await update_content_recommendations._run(user.id)
        results.append(result)
    
    return {
        "status": "success",
        "processed_users": len(results),
        "date": datetime.now().isoformat()
    }


@celery_app.task(base=AsyncTask, name="weekly_model_retraining")
async def weekly_model_retraining():
    """Weekly task to retrain user preference models."""
    return await retrain_user_preferences._run()


@celery_app.task(base=AsyncTask, name="weekly_interaction_cleanup")
async def weekly_interaction_cleanup():
    """Weekly task to clean up old interactions."""
    return await cleanup_old_interactions._run(days_to_keep=90)
