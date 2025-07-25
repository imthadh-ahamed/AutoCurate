"""
Run AutoCurate Application
Main entry point with different run modes
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def run_api():
    """Run the FastAPI application"""
    import uvicorn
    from src.config.settings import settings
    
    print("🚀 Starting AutoCurate API Server...")
    print(f"📡 Server will be available at: http://{settings.app.host}:{settings.app.port}")
    print(f"📚 API Documentation: http://{settings.app.host}:{settings.app.port}/docs")
    
    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower()
    )


def run_worker():
    """Run Celery worker"""
    print("🔧 Starting AutoCurate Celery Worker...")
    os.system("celery -A src.celery_app worker --loglevel=info")


def run_scheduler():
    """Run Celery beat scheduler"""
    print("⏰ Starting AutoCurate Task Scheduler...")
    os.system("celery -A src.celery_app beat --loglevel=info")


def run_flower():
    """Run Flower monitoring tool"""
    print("🌸 Starting Flower Task Monitor...")
    print("📊 Flower UI will be available at: http://localhost:5555")
    os.system("celery -A src.celery_app flower")


def init_database():
    """Initialize the database"""
    from src.core.database import init_database as init_db
    print("🗄️  Initializing AutoCurate Database...")
    init_db()
    print("✅ Database initialization completed!")


async def run_scraping():
    """Run one-time scraping job"""
    from src.agents.website_ingest_agent import run_scheduled_scraping
    
    print("🕷️  Running website scraping job...")
    await run_scheduled_scraping()
    print("✅ Scraping completed!")


async def run_processing():
    """Run one-time content processing job"""
    from src.agents.vector_storage_agent import process_pending_content
    
    print("⚙️  Running content processing job...")
    await process_pending_content()
    print("✅ Content processing completed!")


async def generate_test_summary():
    """Generate a test summary for user ID 1"""
    from src.agents.summary_agent import SummaryAgent
    
    print("📝 Generating test summary...")
    
    agent = SummaryAgent()
    await agent.initialize()
    
    summary = await agent.generate_personalized_summary(1, "daily_digest")
    
    if summary:
        print("✅ Test summary generated successfully!")
        print(f"📋 Title: {summary['title']}")
        print(f"📊 Word Count: {summary['word_count']}")
        print(f"⏱️  Read Time: {summary['read_time_minutes']} minutes")
    else:
        print("❌ Failed to generate test summary")


def show_status():
    """Show application status"""
    import requests
    from src.config.settings import settings
    
    print("📊 AutoCurate Application Status")
    print("=" * 40)
    
    # Check API status
    try:
        response = requests.get(f"http://{settings.app.host}:{settings.app.port}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server: Running")
        else:
            print("❌ API Server: Error")
    except:
        print("❌ API Server: Not running")
    
    # Check database
    try:
        from src.core.database import SessionLocal
        from src.models.database import Website
        
        db = SessionLocal()
        website_count = db.query(Website).count()
        db.close()
        
        print(f"✅ Database: Connected ({website_count} websites)")
    except Exception as e:
        print(f"❌ Database: Error - {e}")
    
    # Check Redis (if available)
    try:
        import redis
        r = redis.from_url(settings.scheduling.redis_url)
        r.ping()
        print("✅ Redis: Connected")
    except:
        print("❌ Redis: Not available")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AutoCurate - AI-Powered Knowledge Feed")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # API server
    subparsers.add_parser('api', help='Run the FastAPI server')
    
    # Background workers
    subparsers.add_parser('worker', help='Run Celery worker for background tasks')
    subparsers.add_parser('scheduler', help='Run Celery beat scheduler')
    subparsers.add_parser('flower', help='Run Flower task monitor')
    
    # Database
    subparsers.add_parser('init-db', help='Initialize the database')
    
    # One-time jobs
    subparsers.add_parser('scrape', help='Run website scraping job')
    subparsers.add_parser('process', help='Run content processing job')
    subparsers.add_parser('test-summary', help='Generate a test summary')
    
    # Utilities
    subparsers.add_parser('status', help='Show application status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🧠 AutoCurate - AI-Powered Knowledge Feed")
    print("=" * 50)
    
    if args.command == 'api':
        run_api()
    elif args.command == 'worker':
        run_worker()
    elif args.command == 'scheduler':
        run_scheduler()
    elif args.command == 'flower':
        run_flower()
    elif args.command == 'init-db':
        init_database()
    elif args.command == 'scrape':
        asyncio.run(run_scraping())
    elif args.command == 'process':
        asyncio.run(run_processing())
    elif args.command == 'test-summary':
        asyncio.run(generate_test_summary())
    elif args.command == 'status':
        show_status()
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
