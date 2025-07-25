"""
Feedback Agent
Handles user feedback collection and learning from user interactions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import numpy as np
from collections import defaultdict

from ..config.settings import settings
from ..models.database import UserContentInteraction, User, ContentItem, UserSummary
from ..models.schemas import UserContentInteractionCreate, InteractionType
from ..core.database import get_db


class FeedbackAgent:
    """
    Agent responsible for collecting user feedback and improving recommendations
    """
    
    def __init__(self):
        self.interaction_weights = {
            InteractionType.VIEW: 1.0,
            InteractionType.LIKE: 2.0,
            InteractionType.DISLIKE: -2.0,
            InteractionType.BOOKMARK: 3.0,
            InteractionType.SHARE: 2.5
        }
    
    def record_interaction(self, interaction_data: UserContentInteractionCreate) -> bool:
        """
        Record a user interaction with content
        
        Args:
            interaction_data: Interaction data to record
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Recording interaction: {interaction_data.interaction_type} for user {interaction_data.user_id}")
            
            db = next(get_db())
            try:
                # Create interaction record
                interaction = UserContentInteraction(
                    user_id=interaction_data.user_id,
                    content_item_id=interaction_data.content_item_id,
                    interaction_type=interaction_data.interaction_type,
                    interaction_value=interaction_data.interaction_value,
                    interaction_metadata=interaction_data.interaction_metadata
                )
                
                db.add(interaction)
                db.commit()
                
                logger.info(f"Recorded interaction {interaction.id}")
                
                # Trigger learning process for significant interactions
                if interaction_data.interaction_type in [InteractionType.LIKE, InteractionType.DISLIKE, InteractionType.BOOKMARK]:
                    self._update_user_preferences_from_interaction(interaction_data)
                
                return True
                
            except Exception as e:
                logger.error(f"Database error recording interaction: {e}")
                db.rollback()
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
            return False
    
    def record_summary_feedback(self, user_id: int, summary_id: int, 
                              rating: Optional[int] = None, feedback: Optional[str] = None) -> bool:
        """
        Record feedback on a generated summary
        
        Args:
            user_id: ID of the user
            summary_id: ID of the summary
            rating: Rating from 1-5
            feedback: Text feedback
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Recording summary feedback for user {user_id}, summary {summary_id}")
            
            db = next(get_db())
            try:
                # Get the summary
                summary = db.query(UserSummary).filter(
                    UserSummary.id == summary_id,
                    UserSummary.user_id == user_id
                ).first()
                
                if not summary:
                    logger.error(f"Summary {summary_id} not found for user {user_id}")
                    return False
                
                # Update summary with feedback
                if rating is not None:
                    summary.user_rating = rating
                if feedback is not None:
                    summary.user_feedback = feedback
                
                db.commit()
                
                logger.info(f"Updated summary {summary_id} with feedback")
                
                # Learn from the feedback
                if rating is not None:
                    self._learn_from_summary_rating(user_id, summary, rating)
                
                return True
                
            except Exception as e:
                logger.error(f"Database error recording summary feedback: {e}")
                db.rollback()
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to record summary feedback: {e}")
            return False
    
    def _update_user_preferences_from_interaction(self, interaction_data: UserContentInteractionCreate):
        """Update user preferences based on content interaction"""
        try:
            db = next(get_db())
            try:
                # Get the content item
                content_item = db.query(ContentItem).filter(
                    ContentItem.id == interaction_data.content_item_id
                ).first()
                
                if not content_item:
                    return
                
                # Get content metadata for learning
                from ..models.database import Website
                website = db.query(Website).filter(Website.id == content_item.website_id).first()
                
                if not website:
                    return
                
                # Get user preferences
                from ..models.database import UserPreference
                preferences = db.query(UserPreference).filter(
                    UserPreference.user_id == interaction_data.user_id
                ).first()
                
                if not preferences:
                    return
                
                # Update preferences based on interaction
                if interaction_data.interaction_type == InteractionType.LIKE:
                    # Add category to preferred if not already there
                    if website.category and website.category not in (preferences.preferred_categories or []):
                        current_categories = preferences.preferred_categories or []
                        current_categories.append(website.category)
                        preferences.preferred_categories = current_categories
                
                elif interaction_data.interaction_type == InteractionType.DISLIKE:
                    # Remove category from preferred if present
                    if website.category and website.category in (preferences.preferred_categories or []):
                        current_categories = preferences.preferred_categories or []
                        current_categories.remove(website.category)
                        preferences.preferred_categories = current_categories
                
                db.commit()
                logger.info(f"Updated preferences for user {interaction_data.user_id} based on interaction")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to update preferences from interaction: {e}")
    
    def _learn_from_summary_rating(self, user_id: int, summary: UserSummary, rating: int):
        """Learn from summary rating to improve future summaries"""
        try:
            logger.info(f"Learning from summary rating {rating} for user {user_id}")
            
            # For low ratings (1-2), analyze what went wrong
            if rating <= 2:
                self._analyze_negative_feedback(user_id, summary)
            
            # For high ratings (4-5), reinforce successful patterns
            elif rating >= 4:
                self._reinforce_positive_patterns(user_id, summary)
            
        except Exception as e:
            logger.error(f"Failed to learn from summary rating: {e}")
    
    def _analyze_negative_feedback(self, user_id: int, summary: UserSummary):
        """Analyze negative feedback to identify improvement areas"""
        try:
            # This is a simplified learning approach
            # In a production system, you might use more sophisticated ML approaches
            
            db = next(get_db())
            try:
                from ..models.database import UserPreference
                preferences = db.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                ).first()
                
                if preferences:
                    # Analyze summary characteristics that led to negative feedback
                    # This could be expanded with more sophisticated analysis
                    
                    # If summary was too long/short, adjust preferences
                    if summary.word_count:
                        if summary.word_count > 800 and preferences.content_length != "short":
                            # User might prefer shorter content
                            logger.info(f"Adjusting content length preference for user {user_id} to shorter")
                        elif summary.word_count < 200 and preferences.content_length != "long":
                            # User might prefer longer content
                            logger.info(f"Adjusting content length preference for user {user_id} to longer")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to analyze negative feedback: {e}")
    
    def _reinforce_positive_patterns(self, user_id: int, summary: UserSummary):
        """Reinforce patterns that led to positive feedback"""
        try:
            # Identify what made this summary successful
            # This could involve analyzing:
            # - Content categories included
            # - Summary format used
            # - Length and depth
            # - Topics covered
            
            logger.info(f"Reinforcing positive patterns for user {user_id}")
            
            # This is a placeholder for more sophisticated pattern reinforcement
            # In practice, you might update user preference weights or create
            # preference embeddings
            
        except Exception as e:
            logger.error(f"Failed to reinforce positive patterns: {e}")
    
    def get_user_interaction_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics about user interactions
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
            
        Returns:
            Dict with interaction analytics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            db = next(get_db())
            try:
                # Get interactions in the time period
                interactions = db.query(UserContentInteraction).filter(
                    UserContentInteraction.user_id == user_id,
                    UserContentInteraction.created_at >= cutoff_date
                ).all()
                
                if not interactions:
                    return {
                        'total_interactions': 0,
                        'interaction_breakdown': {},
                        'engagement_score': 0.0,
                        'top_categories': [],
                        'recommendation': "Start interacting with content to get personalized recommendations"
                    }
                
                # Analyze interactions
                interaction_counts = defaultdict(int)
                category_engagement = defaultdict(float)
                total_score = 0
                
                for interaction in interactions:
                    interaction_counts[interaction.interaction_type.value] += 1
                    weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                    total_score += weight
                    
                    # Get content category for category analysis
                    if hasattr(interaction, 'content_item') and hasattr(interaction.content_item, 'website'):
                        category = interaction.content_item.website.category
                        if category:
                            category_engagement[category] += weight
                
                # Calculate engagement score (normalized)
                engagement_score = max(0, min(10, total_score / len(interactions)))
                
                # Get top categories
                top_categories = sorted(
                    category_engagement.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
                
                return {
                    'total_interactions': len(interactions),
                    'interaction_breakdown': dict(interaction_counts),
                    'engagement_score': round(engagement_score, 2),
                    'top_categories': [{'category': cat, 'score': round(score, 2)} for cat, score in top_categories],
                    'recommendation': self._generate_engagement_recommendation(engagement_score, interaction_counts)
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get user interaction analytics: {e}")
            return {'error': 'Failed to generate analytics'}
    
    def _generate_engagement_recommendation(self, engagement_score: float, 
                                         interaction_counts: Dict[str, int]) -> str:
        """Generate recommendation based on engagement patterns"""
        
        if engagement_score < 3:
            return "Try liking or bookmarking articles you find interesting to improve recommendations"
        elif engagement_score < 6:
            return "Great engagement! Continue rating content to get better personalized summaries"
        elif engagement_score < 8:
            return "Excellent engagement! Your feedback is helping create highly personalized content"
        else:
            return "Outstanding engagement! You're getting the most out of AutoCurate's personalization"
    
    def get_content_performance_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics about content performance across all users
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with content performance analytics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            db = next(get_db())
            try:
                # Get all interactions in the time period
                interactions = db.query(UserContentInteraction).filter(
                    UserContentInteraction.created_at >= cutoff_date
                ).all()
                
                if not interactions:
                    return {'message': 'No interaction data available'}
                
                # Analyze content performance
                content_scores = defaultdict(float)
                category_performance = defaultdict(list)
                
                for interaction in interactions:
                    weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                    content_scores[interaction.content_item_id] += weight
                    
                    # Get content category
                    if hasattr(interaction, 'content_item') and hasattr(interaction.content_item, 'website'):
                        category = interaction.content_item.website.category
                        if category:
                            category_performance[category].append(weight)
                
                # Calculate category averages
                category_avg_scores = {}
                for category, scores in category_performance.items():
                    category_avg_scores[category] = sum(scores) / len(scores)
                
                # Get top performing content
                top_content_ids = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Get content details for top performers
                top_content = []
                for content_id, score in top_content_ids:
                    content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
                    if content_item:
                        top_content.append({
                            'id': content_id,
                            'title': content_item.title,
                            'url': content_item.url,
                            'score': round(score, 2),
                            'category': getattr(content_item.website, 'category', 'Unknown') if hasattr(content_item, 'website') else 'Unknown'
                        })
                
                return {
                    'total_interactions': len(interactions),
                    'unique_content_items': len(content_scores),
                    'category_performance': {cat: round(score, 2) for cat, score in category_avg_scores.items()},
                    'top_performing_content': top_content,
                    'average_engagement_per_item': round(sum(content_scores.values()) / len(content_scores), 2) if content_scores else 0
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get content performance analytics: {e}")
            return {'error': 'Failed to generate analytics'}


def update_user_learning_models():
    """Update user learning models based on accumulated feedback"""
    logger.info("Starting user learning model update")
    
    try:
        # This is a placeholder for more sophisticated learning algorithms
        # In a production system, you might:
        # 1. Update user embedding vectors
        # 2. Retrain personalization models
        # 3. Update content recommendation weights
        # 4. Adjust summary generation parameters
        
        db = next(get_db())
        try:
            # Get users with recent interactions
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            active_users = db.query(User).join(UserContentInteraction).filter(
                UserContentInteraction.created_at >= cutoff_date
            ).distinct().all()
            
            logger.info(f"Updating learning models for {len(active_users)} active users")
            
            # Process each user's learning updates
            for user in active_users:
                try:
                    # This would be where you update user-specific models
                    # For now, we'll just log the process
                    logger.debug(f"Processing learning updates for user {user.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to update learning model for user {user.id}: {e}")
            
        finally:
            db.close()
        
        logger.info("User learning model update completed")
        
    except Exception as e:
        logger.error(f"Failed to update user learning models: {e}")
