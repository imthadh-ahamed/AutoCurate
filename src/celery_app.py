"""
Celery configuration for background tasks
"""

from celery import Celery
from celery.schedules import crontab
import asyncio
import os

from .config.settings import settings

# Create Celery app
celery_app = Celery(
    "autocurate",
    broker=settings.scheduling.redis_url,
    backend=settings.scheduling.redis_url,
    include=[
        'src.tasks.scraping_tasks',
        'src.tasks.processing_tasks', 
        'src.tasks.summary_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Scraping tasks
    'scrape-websites-hourly': {
        'task': 'src.tasks.scraping_tasks.run_scheduled_scraping',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    
    # Content processing tasks
    'process-content-every-30min': {
        'task': 'src.tasks.processing_tasks.process_pending_content',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    
    # Summary generation tasks
    'generate-daily-summaries': {
        'task': 'src.tasks.summary_tasks.generate_daily_summaries',
        'schedule': crontab(hour=9, minute=0),  # 9 AM UTC daily
    },
    
    'generate-weekly-summaries': {
        'task': 'src.tasks.summary_tasks.generate_weekly_summaries', 
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday 9 AM UTC
    },
    
    'generate-monthly-summaries': {
        'task': 'src.tasks.summary_tasks.generate_monthly_summaries',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),  # 1st of month 9 AM UTC
    },
    
    # Learning and cleanup tasks
    'update-learning-models': {
        'task': 'src.tasks.learning_tasks.update_user_learning_models',
        'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
    
    'cleanup-old-data': {
        'task': 'src.tasks.maintenance_tasks.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM UTC
    },
}


def run_async_task(task_func, *args, **kwargs):
    """Helper to run async functions in Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(task_func(*args, **kwargs))
    finally:
        loop.close()


if __name__ == '__main__':
    celery_app.start()
