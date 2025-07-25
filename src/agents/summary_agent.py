"""
Summary Agent
Handles personalized content summarization using LLM
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import openai
from loguru import logger

from ..config.settings import settings
from ..models.database import ContentItem, UserSummary, User, UserPreference
from ..models.schemas import UserSummaryCreate
from ..core.database import get_db
from ..agents.vector_storage_agent import VectorStorageAgent
from ..agents.user_preference_agent import UserPreferenceAgent
from ..utils.text_processor import TextProcessor


class SummaryAgent:
    """
    Agent responsible for generating personalized summaries using RAG
    """
    
    def __init__(self):
        self.vector_agent = VectorStorageAgent()
        self.preference_agent = UserPreferenceAgent()
        self.text_processor = TextProcessor()
        self.llm_client = None
        
    async def initialize(self):
        """Initialize the summary agent"""
        await self.vector_agent.initialize()
        
        # Setup OpenAI client
        openai.api_key = settings.llm.openai_api_key
        self.llm_client = openai
        
        logger.info("Summary Agent initialized")
    
    async def generate_personalized_summary(self, user_id: int, 
                                          summary_type: str = "daily_digest") -> Optional[Dict[str, Any]]:
        """
        Generate a personalized summary for a user
        
        Args:
            user_id: ID of the user
            summary_type: Type of summary to generate
            
        Returns:
            Dict with summary data or None if failed
        """
        try:
            logger.info(f"Generating {summary_type} for user {user_id}")
            
            # Get user preferences
            preferences = self.preference_agent.get_user_preferences(user_id)
            if not preferences:
                logger.error(f"No preferences found for user {user_id}")
                return None
            
            # Get personalization context
            context = self.preference_agent.get_personalization_context(user_id)
            
            # Retrieve relevant content based on preferences
            relevant_content = await self._retrieve_relevant_content(user_id, context)
            
            if not relevant_content:
                logger.warning(f"No relevant content found for user {user_id}")
                return None
            
            # Generate summary using LLM
            summary_data = await self._generate_llm_summary(
                relevant_content, context, summary_type
            )
            
            if not summary_data:
                logger.error(f"Failed to generate LLM summary for user {user_id}")
                return None
            
            # Save summary to database
            summary_record = await self._save_summary(user_id, summary_data, relevant_content)
            
            if summary_record:
                logger.info(f"Successfully generated summary {summary_record.id} for user {user_id}")
                return {
                    'id': summary_record.id,
                    'title': summary_record.title,
                    'content': summary_record.summary_content,
                    'summary_type': summary_record.summary_type,
                    'word_count': summary_record.word_count,
                    'read_time_minutes': summary_record.read_time_minutes,
                    'created_at': summary_record.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate personalized summary: {e}")
            return None
    
    async def _retrieve_relevant_content(self, user_id: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content based on user preferences and recent activity
        
        Args:
            user_id: ID of the user
            context: Personalization context
            
        Returns:
            List of relevant content items with metadata
        """
        try:
            # Get content filters from preferences
            filters = self.preference_agent.generate_content_filters(user_id)
            
            # Get time window for content based on delivery frequency
            preferences = self.preference_agent.get_user_preferences(user_id)
            time_window = self._get_time_window(preferences['delivery_frequency'])
            
            # Query database for recent content
            db = next(get_db())
            try:
                query = db.query(ContentItem).filter(
                    ContentItem.is_processed == True,
                    ContentItem.scraped_at >= time_window
                )
                
                # Apply category filters if specified
                if filters.get('category'):
                    from ..models.database import Website
                    query = query.join(Website).filter(
                        Website.category.in_(filters['category'])
                    )
                
                # Apply word count filters
                if filters.get('max_word_count'):
                    query = query.filter(
                        ContentItem.word_count <= filters['max_word_count']
                    )
                
                # Apply language filter
                if filters.get('language'):
                    query = query.filter(
                        ContentItem.language == filters['language']
                    )
                
                # Order by recency and limit results
                recent_content = query.order_by(
                    ContentItem.scraped_at.desc()
                ).limit(50).all()  # Get more than needed for vector filtering
                
            finally:
                db.close()
            
            if not recent_content:
                return []
            
            # Use vector search to find most relevant content based on topics
            if context.get('topics_of_interest'):
                relevant_items = await self._vector_filter_content(
                    recent_content, context['topics_of_interest'], context['max_items']
                )
            else:
                # Fallback to recent content
                relevant_items = recent_content[:context['max_items']]
            
            # Convert to dict format with metadata
            content_data = []
            for item in relevant_items:
                content_data.append({
                    'id': item.id,
                    'title': item.title,
                    'content': item.cleaned_content or item.content,
                    'url': item.url,
                    'author': item.author,
                    'published_date': item.published_date,
                    'scraped_at': item.scraped_at,
                    'word_count': item.word_count,
                    'category': getattr(item.website, 'category', 'Unknown') if hasattr(item, 'website') else 'Unknown'
                })
            
            return content_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant content: {e}")
            return []
    
    async def _vector_filter_content(self, content_items: List[ContentItem], 
                                   topics: List[str], max_items: int) -> List[ContentItem]:
        """
        Use vector similarity to filter content based on user topics
        
        Args:
            content_items: List of content items to filter
            topics: User's topics of interest
            max_items: Maximum number of items to return
            
        Returns:
            Filtered list of content items
        """
        try:
            # Create search query from topics
            search_query = " ".join(topics)
            
            # Get content item IDs
            content_ids = [item.id for item in content_items]
            
            # Search for similar content using vector database
            search_results = await self.vector_agent.search_similar_content(
                query=search_query,
                limit=max_items * 2,  # Get more to account for filtering
                filters={'content_item_id': content_ids}
            )
            
            # Map results back to content items
            relevant_item_ids = set()
            for result in search_results[:max_items]:
                if 'content_item_id' in result['metadata']:
                    relevant_item_ids.add(result['metadata']['content_item_id'])
            
            # Filter original items based on vector search results
            filtered_items = [
                item for item in content_items 
                if item.id in relevant_item_ids
            ]
            
            # If vector search didn't return enough items, add recent ones
            if len(filtered_items) < max_items:
                additional_items = [
                    item for item in content_items 
                    if item.id not in relevant_item_ids
                ][:max_items - len(filtered_items)]
                filtered_items.extend(additional_items)
            
            return filtered_items[:max_items]
            
        except Exception as e:
            logger.error(f"Vector filtering failed: {e}")
            # Fallback to recent content
            return content_items[:max_items]
    
    def _get_time_window(self, delivery_frequency: str) -> datetime:
        """Get the time window for content based on delivery frequency"""
        now = datetime.utcnow()
        
        if delivery_frequency == "daily":
            return now - timedelta(days=1)
        elif delivery_frequency == "weekly":
            return now - timedelta(weeks=1)
        elif delivery_frequency == "monthly":
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=1)  # Default to daily
    
    async def _generate_llm_summary(self, content_items: List[Dict[str, Any]], 
                                   context: Dict[str, Any], summary_type: str) -> Optional[Dict[str, Any]]:
        """
        Generate summary using LLM based on content and user context
        
        Args:
            content_items: List of content items to summarize
            context: User personalization context
            summary_type: Type of summary to generate
            
        Returns:
            Dict with generated summary data
        """
        try:
            # Build the prompt
            prompt = self._build_summary_prompt(content_items, context, summary_type)
            
            # Call LLM
            response = await self.llm_client.ChatCompletion.acreate(
                model=settings.llm.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt(context, summary_type)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=settings.llm.max_tokens,
                temperature=settings.llm.temperature
            )
            
            summary_content = response.choices[0].message.content.strip()
            
            if not summary_content:
                logger.error("Empty response from LLM")
                return None
            
            # Generate title
            title = await self._generate_summary_title(summary_content, summary_type)
            
            # Calculate metrics
            word_count = self.text_processor.count_words(summary_content)
            read_time = self.text_processor.estimate_reading_time(summary_content)
            
            return {
                'title': title,
                'content': summary_content,
                'summary_type': summary_type,
                'word_count': word_count,
                'read_time_minutes': read_time,
                'generation_prompt': prompt,
                'llm_model_used': settings.llm.openai_model
            }
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return None
    
    def _build_summary_prompt(self, content_items: List[Dict[str, Any]], 
                            context: Dict[str, Any], summary_type: str) -> str:
        """Build the prompt for LLM summary generation"""
        
        # Format content items
        content_text = ""
        for i, item in enumerate(content_items, 1):
            content_text += f"\n--- Article {i} ---\n"
            content_text += f"Title: {item['title']}\n"
            content_text += f"Source: {item['url']}\n"
            if item['author']:
                content_text += f"Author: {item['author']}\n"
            content_text += f"Category: {item['category']}\n"
            content_text += f"Content: {item['content'][:1000]}...\n"  # Limit content length
        
        # Build main prompt
        prompt = f"""Please create a personalized {summary_type} based on the following articles:

{content_text}

User Preferences:
- Content Depth: {context.get('content_depth', 'summary')}
- Content Format: {context.get('content_format', 'bullets')}
- Content Length: {context.get('content_length', 'medium')}
- Topics of Interest: {', '.join(context.get('topics_of_interest', []))}
- Include Summaries: {context.get('include_summaries', True)}
- Include Key Points: {context.get('include_key_points', True)}
- Include Trends: {context.get('include_trends', False)}

Please format the response according to the user's preferences and focus on their topics of interest."""
        
        return prompt
    
    def _get_system_prompt(self, context: Dict[str, Any], summary_type: str) -> str:
        """Get the system prompt for LLM"""
        
        format_instructions = {
            'bullets': "Format your response using bullet points and clear headings.",
            'narrative': "Write in a flowing narrative style with connected paragraphs.",
            'tabular': "When possible, use structured formats like tables or lists."
        }
        
        depth_instructions = {
            'summary': "Provide brief, concise summaries focusing on key points.",
            'detailed': "Include more context and explanation in your summaries.",
            'comprehensive': "Provide thorough analysis with background context and implications."
        }
        
        system_prompt = f"""You are an AI assistant that creates personalized content summaries. 

Your task is to create a {summary_type} that is tailored to the user's specific interests and preferences.

Formatting Guidelines:
- {format_instructions.get(context.get('content_format', 'bullets'), format_instructions['bullets'])}
- {depth_instructions.get(context.get('content_depth', 'summary'), depth_instructions['summary'])}

Key Requirements:
1. Focus on the user's topics of interest
2. Maintain the requested content depth and format
3. Include only relevant and high-quality information
4. Make the content engaging and easy to read
5. If trends are requested, highlight emerging patterns across articles
6. Always cite sources when referencing specific articles

Be concise but informative, and ensure the summary adds value by connecting information across sources."""
        
        return system_prompt
    
    async def _generate_summary_title(self, summary_content: str, summary_type: str) -> str:
        """Generate a title for the summary"""
        try:
            # Extract key topics from content for title
            key_phrases = self.text_processor.extract_key_phrases(summary_content, max_phrases=3)
            
            if key_phrases:
                # Use key phrases to create title
                main_topic = key_phrases[0].title()
                date_str = datetime.utcnow().strftime("%B %d, %Y")
                
                if summary_type == "daily_digest":
                    return f"Daily Digest: {main_topic} - {date_str}"
                elif summary_type == "weekly_roundup":
                    return f"Weekly Roundup: {main_topic} - {date_str}"
                else:
                    return f"{main_topic} Summary - {date_str}"
            else:
                # Fallback titles
                date_str = datetime.utcnow().strftime("%B %d, %Y")
                return f"{summary_type.replace('_', ' ').title()} - {date_str}"
                
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return f"Your {summary_type.replace('_', ' ').title()}"
    
    async def _save_summary(self, user_id: int, summary_data: Dict[str, Any], 
                          content_items: List[Dict[str, Any]]) -> Optional[UserSummary]:
        """Save the generated summary to database"""
        try:
            db = next(get_db())
            try:
                # Extract content item IDs
                content_item_ids = [item['id'] for item in content_items]
                
                # Create summary record
                summary_record = UserSummary(
                    user_id=user_id,
                    title=summary_data['title'],
                    summary_content=summary_data['content'],
                    summary_type=summary_data['summary_type'],
                    content_items_included=content_item_ids,
                    generation_prompt=summary_data.get('generation_prompt'),
                    llm_model_used=summary_data.get('llm_model_used'),
                    word_count=summary_data['word_count'],
                    read_time_minutes=summary_data['read_time_minutes']
                )
                
                db.add(summary_record)
                db.commit()
                db.refresh(summary_record)
                
                return summary_record
                
            except Exception as e:
                logger.error(f"Database error saving summary: {e}")
                db.rollback()
                return None
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            return None


async def generate_summaries_for_all_users():
    """Generate summaries for all active users based on their delivery schedule"""
    logger.info("Starting summary generation job for all users")
    
    db = next(get_db())
    try:
        # Get users who need summaries based on their delivery frequency
        current_hour = datetime.utcnow().hour
        
        # Get users with daily delivery preference
        daily_users = db.query(User).join(UserPreference).filter(
            User.is_active == True,
            UserPreference.delivery_frequency == "daily"
        ).all()
        
        # Get users with weekly delivery (Mondays only)
        weekly_users = []
        if datetime.utcnow().weekday() == 0:  # Monday
            weekly_users = db.query(User).join(UserPreference).filter(
                User.is_active == True,
                UserPreference.delivery_frequency == "weekly"
            ).all()
        
        # Get users with monthly delivery (1st of month only)
        monthly_users = []
        if datetime.utcnow().day == 1:  # First day of month
            monthly_users = db.query(User).join(UserPreference).filter(
                User.is_active == True,
                UserPreference.delivery_frequency == "monthly"
            ).all()
        
        all_users = daily_users + weekly_users + monthly_users
        
    finally:
        db.close()
    
    if not all_users:
        logger.info("No users need summaries at this time")
        return
    
    logger.info(f"Generating summaries for {len(all_users)} users")
    
    # Initialize summary agent
    agent = SummaryAgent()
    await agent.initialize()
    
    # Generate summaries for each user
    for user in all_users:
        try:
            # Determine summary type based on delivery frequency
            preferences = agent.preference_agent.get_user_preferences(user.id)
            if preferences:
                frequency = preferences['delivery_frequency']
                if frequency == "daily":
                    summary_type = "daily_digest"
                elif frequency == "weekly":
                    summary_type = "weekly_roundup"
                else:
                    summary_type = "monthly_overview"
                
                # Generate summary
                summary = await agent.generate_personalized_summary(user.id, summary_type)
                
                if summary:
                    logger.info(f"Generated summary for user {user.id}")
                else:
                    logger.warning(f"Failed to generate summary for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error generating summary for user {user.id}: {e}")
    
    logger.info("Summary generation job completed")
