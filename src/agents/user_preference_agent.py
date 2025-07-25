"""
User Preference Agent
Handles user preference collection, interpretation, and management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from ..config.settings import settings
from ..models.database import User, UserPreference
from ..models.schemas import SurveyResponse, UserPreferenceCreate, UserPreferenceUpdate
from ..core.database import get_db


class UserPreferenceAgent:
    """
    Agent responsible for collecting and managing user preferences
    """
    
    def __init__(self):
        self.preference_categories = {
            'AI Research & Tech Blogs': ['artificial intelligence', 'machine learning', 'deep learning', 'neural networks', 'ai research'],
            'Tech News': ['technology', 'startups', 'programming', 'software development', 'tech industry'],
            'Science': ['science', 'research', 'biology', 'physics', 'chemistry', 'space'],
            'Business': ['business', 'finance', 'economics', 'markets', 'entrepreneurship'],
            'Health': ['health', 'medicine', 'fitness', 'nutrition', 'wellness'],
            'Environment': ['environment', 'climate', 'sustainability', 'green technology', 'conservation']
        }
    
    def create_dynamic_survey(self, user_id: int) -> Dict[str, Any]:
        """
        Generate a dynamic survey based on available content categories
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict containing survey structure
        """
        try:
            # Get available categories from websites
            db = next(get_db())
            try:
                from ..models.database import Website
                categories = db.query(Website.category).distinct().filter(
                    Website.category.isnot(None),
                    Website.is_active == True
                ).all()
                
                available_categories = [cat[0] for cat in categories if cat[0]]
                
            finally:
                db.close()
            
            survey_structure = {
                'user_id': user_id,
                'sections': [
                    {
                        'id': 'interests',
                        'title': 'What are your main interests?',
                        'type': 'multi_select',
                        'options': self._generate_interest_options(),
                        'required': True,
                        'min_selections': 1,
                        'max_selections': 10
                    },
                    {
                        'id': 'categories',
                        'title': 'Which content categories would you like to follow?',
                        'type': 'multi_select',
                        'options': [{'value': cat, 'label': cat} for cat in available_categories],
                        'required': True,
                        'min_selections': 1,
                        'max_selections': len(available_categories)
                    },
                    {
                        'id': 'content_depth',
                        'title': 'How detailed should your summaries be?',
                        'type': 'single_select',
                        'options': [
                            {'value': 'summary', 'label': 'Brief summaries (2-3 sentences)', 'description': 'Quick overview of key points'},
                            {'value': 'detailed', 'label': 'Detailed summaries (1-2 paragraphs)', 'description': 'More comprehensive coverage'},
                            {'value': 'comprehensive', 'label': 'Comprehensive analysis (3+ paragraphs)', 'description': 'In-depth analysis and context'}
                        ],
                        'required': True,
                        'default': 'summary'
                    },
                    {
                        'id': 'content_format',
                        'title': 'How would you prefer to receive information?',
                        'type': 'single_select',
                        'options': [
                            {'value': 'bullets', 'label': 'Bullet points', 'description': 'Easy to scan key points'},
                            {'value': 'narrative', 'label': 'Narrative format', 'description': 'Story-like flowing text'},
                            {'value': 'tabular', 'label': 'Tables and structured data', 'description': 'Organized in tables when possible'}
                        ],
                        'required': True,
                        'default': 'bullets'
                    },
                    {
                        'id': 'content_length',
                        'title': 'Preferred content length?',
                        'type': 'single_select',
                        'options': [
                            {'value': 'short', 'label': 'Short (1-2 minutes read)', 'description': '100-200 words'},
                            {'value': 'medium', 'label': 'Medium (3-5 minutes read)', 'description': '300-500 words'},
                            {'value': 'long', 'label': 'Long (5+ minutes read)', 'description': '500+ words'}
                        ],
                        'required': True,
                        'default': 'medium'
                    },
                    {
                        'id': 'delivery_frequency',
                        'title': 'How often would you like to receive updates?',
                        'type': 'single_select',
                        'options': [
                            {'value': 'daily', 'label': 'Daily digest', 'description': 'Every day at your preferred time'},
                            {'value': 'weekly', 'label': 'Weekly roundup', 'description': 'Once a week summary'},
                            {'value': 'monthly', 'label': 'Monthly overview', 'description': 'Monthly comprehensive report'}
                        ],
                        'required': True,
                        'default': 'daily'
                    },
                    {
                        'id': 'preferred_time',
                        'title': 'What time would you prefer to receive your digest?',
                        'type': 'time_select',
                        'required': False,
                        'default': '09:00',
                        'description': 'Time in 24-hour format (HH:MM)'
                    },
                    {
                        'id': 'timezone',
                        'title': 'Your timezone',
                        'type': 'timezone_select',
                        'required': True,
                        'default': 'UTC'
                    },
                    {
                        'id': 'max_items',
                        'title': 'Maximum number of items per digest?',
                        'type': 'number_slider',
                        'min': 5,
                        'max': 50,
                        'default': 10,
                        'step': 5,
                        'required': True
                    },
                    {
                        'id': 'advanced_features',
                        'title': 'Additional features',
                        'type': 'checkbox_group',
                        'options': [
                            {'value': 'include_summaries', 'label': 'Include article summaries', 'default': True},
                            {'value': 'include_key_points', 'label': 'Extract key points', 'default': True},
                            {'value': 'include_trends', 'label': 'Highlight trending topics', 'default': False},
                            {'value': 'feedback_enabled', 'label': 'Enable feedback for improvement', 'default': True},
                            {'value': 'personalization_enabled', 'label': 'Enable AI personalization', 'default': True}
                        ],
                        'required': False
                    }
                ]
            }
            
            return survey_structure
            
        except Exception as e:
            logger.error(f"Failed to create dynamic survey: {e}")
            return self._get_fallback_survey(user_id)
    
    def _generate_interest_options(self) -> List[Dict[str, str]]:
        """Generate interest options from categories"""
        options = []
        
        for category, keywords in self.preference_categories.items():
            # Add category as main option
            options.append({
                'value': category.lower().replace(' & ', '_').replace(' ', '_'),
                'label': category,
                'category': category
            })
            
            # Add specific keywords as sub-options
            for keyword in keywords:
                options.append({
                    'value': keyword.replace(' ', '_'),
                    'label': keyword.title(),
                    'category': category
                })
        
        return sorted(options, key=lambda x: x['label'])
    
    def _get_fallback_survey(self, user_id: int) -> Dict[str, Any]:
        """Fallback survey structure if dynamic generation fails"""
        return {
            'user_id': user_id,
            'sections': [
                {
                    'id': 'basic_interests',
                    'title': 'What topics interest you most?',
                    'type': 'multi_select',
                    'options': [
                        {'value': 'technology', 'label': 'Technology'},
                        {'value': 'science', 'label': 'Science'},
                        {'value': 'business', 'label': 'Business'},
                        {'value': 'health', 'label': 'Health'},
                        {'value': 'environment', 'label': 'Environment'}
                    ],
                    'required': True
                }
            ]
        }
    
    def process_survey_response(self, survey_response: SurveyResponse) -> bool:
        """
        Process and save survey response as user preferences
        
        Args:
            survey_response: Completed survey response
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing survey response for user {survey_response.user_id}")
            
            db = next(get_db())
            try:
                # Check if user exists
                user = db.query(User).filter(User.id == survey_response.user_id).first()
                if not user:
                    logger.error(f"User {survey_response.user_id} not found")
                    return False
                
                # Check if preferences already exist
                existing_preferences = db.query(UserPreference).filter(
                    UserPreference.user_id == survey_response.user_id
                ).first()
                
                # Extract preference data from survey response
                preference_data = self._extract_preferences_from_survey(survey_response)
                
                if existing_preferences:
                    # Update existing preferences
                    for key, value in preference_data.items():
                        setattr(existing_preferences, key, value)
                    existing_preferences.updated_at = datetime.utcnow()
                    
                    logger.info(f"Updated preferences for user {survey_response.user_id}")
                
                else:
                    # Create new preferences
                    preference_data['user_id'] = survey_response.user_id
                    new_preferences = UserPreference(**preference_data)
                    db.add(new_preferences)
                    
                    logger.info(f"Created new preferences for user {survey_response.user_id}")
                
                db.commit()
                return True
                
            except Exception as e:
                logger.error(f"Database error processing survey: {e}")
                db.rollback()
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to process survey response: {e}")
            return False
    
    def _extract_preferences_from_survey(self, survey_response: SurveyResponse) -> Dict[str, Any]:
        """Extract preference fields from survey response"""
        preference_data = {
            'topics_of_interest': survey_response.topics_of_interest,
            'preferred_categories': survey_response.preferred_categories,
            'content_depth': survey_response.content_preferences.get('depth', 'summary'),
            'content_format': survey_response.content_preferences.get('format', 'bullets'),
            'content_length': survey_response.content_preferences.get('length', 'medium'),
            'delivery_frequency': survey_response.delivery_preferences.get('frequency', 'daily'),
            'preferred_time': survey_response.delivery_preferences.get('time'),
            'timezone': survey_response.delivery_preferences.get('timezone', 'UTC'),
            'max_items_per_digest': survey_response.delivery_preferences.get('max_items', 10),
            'include_summaries': survey_response.advanced_preferences.get('summaries', True),
            'include_key_points': survey_response.advanced_preferences.get('key_points', True),
            'include_trends': survey_response.advanced_preferences.get('trends', False),
            'feedback_enabled': survey_response.advanced_preferences.get('feedback', True),
            'personalization_enabled': survey_response.advanced_preferences.get('personalization', True)
        }
        
        return preference_data
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user preferences by user ID
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict with user preferences or None if not found
        """
        try:
            db = next(get_db())
            try:
                preferences = db.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                ).first()
                
                if preferences:
                    return {
                        'user_id': preferences.user_id,
                        'topics_of_interest': preferences.topics_of_interest or [],
                        'preferred_categories': preferences.preferred_categories or [],
                        'content_depth': preferences.content_depth,
                        'content_format': preferences.content_format,
                        'content_length': preferences.content_length,
                        'delivery_frequency': preferences.delivery_frequency,
                        'preferred_time': preferences.preferred_time,
                        'timezone': preferences.timezone,
                        'max_items_per_digest': preferences.max_items_per_digest,
                        'include_summaries': preferences.include_summaries,
                        'include_key_points': preferences.include_key_points,
                        'include_trends': preferences.include_trends,
                        'feedback_enabled': preferences.feedback_enabled,
                        'personalization_enabled': preferences.personalization_enabled,
                        'created_at': preferences.created_at,
                        'updated_at': preferences.updated_at
                    }
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    def update_user_preferences(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update specific user preference fields
        
        Args:
            user_id: ID of the user
            updates: Dict of fields to update
            
        Returns:
            bool: Success status
        """
        try:
            db = next(get_db())
            try:
                preferences = db.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                ).first()
                
                if not preferences:
                    logger.error(f"Preferences not found for user {user_id}")
                    return False
                
                # Update provided fields
                for key, value in updates.items():
                    if hasattr(preferences, key):
                        setattr(preferences, key, value)
                
                preferences.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Updated preferences for user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Database error updating preferences: {e}")
                db.rollback()
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False
    
    def generate_content_filters(self, user_id: int) -> Dict[str, Any]:
        """
        Generate content filters based on user preferences
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict with filters for content retrieval
        """
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return {}
        
        filters = {}
        
        # Category filters
        if preferences['preferred_categories']:
            filters['category'] = preferences['preferred_categories']
        
        # Topic filters (will be used for vector search)
        if preferences['topics_of_interest']:
            filters['topics'] = preferences['topics_of_interest']
        
        # Content length preferences (for filtering by word count)
        if preferences['content_length'] == 'short':
            filters['max_word_count'] = 300
        elif preferences['content_length'] == 'medium':
            filters['max_word_count'] = 800
        else:  # long
            filters['max_word_count'] = None
        
        # Language filter
        if preferences.get('language_preference'):
            filters['language'] = preferences['language_preference']
        
        return filters
    
    def get_personalization_context(self, user_id: int) -> Dict[str, Any]:
        """
        Get context for personalized content generation
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict with personalization context
        """
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return {}
        
        context = {
            'content_depth': preferences['content_depth'],
            'content_format': preferences['content_format'],
            'content_length': preferences['content_length'],
            'topics_of_interest': preferences['topics_of_interest'],
            'include_summaries': preferences['include_summaries'],
            'include_key_points': preferences['include_key_points'],
            'include_trends': preferences['include_trends'],
            'max_items': preferences['max_items_per_digest']
        }
        
        return context
