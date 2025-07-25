"""
Maintenance and system health tasks for Celery.
Handles database cleanup, health checks, and system monitoring.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import psutil

from celery import Task
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from ..celery_app import celery_app
from ..core.database import get_db, engine
from ..models.database import Website, ContentItem, User, UserSummary, UserContentInteraction
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


@celery_app.task(base=AsyncTask, bind=True)
async def health_check(self) -> Dict[str, Any]:
    """
    Perform comprehensive system health check.
    
    Returns:
        Dict containing health status of various components
    """
    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {}
        }
        
        # Database health check
        try:
            db = next(get_db())
            
            # Test database connection
            result = db.execute(text("SELECT 1")).fetchone()
            if result:
                health_status["components"]["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
            else:
                health_status["components"]["database"] = {
                    "status": "unhealthy",
                    "message": "Database query failed"
                }
                health_status["overall_status"] = "unhealthy"
                
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}"
            }
            health_status["overall_status"] = "unhealthy"
        
        # System resources check
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                system_status = "warning"
                health_status["overall_status"] = "warning"
            
            health_status["components"]["system"] = {
                "status": system_status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
            
        except Exception as e:
            health_status["components"]["system"] = {
                "status": "unhealthy",
                "message": f"System monitoring error: {str(e)}"
            }
            health_status["overall_status"] = "unhealthy"
        
        # Celery workers check
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                health_status["components"]["celery"] = {
                    "status": "healthy",
                    "active_workers": len(active_workers),
                    "workers": list(active_workers.keys())
                }
            else:
                health_status["components"]["celery"] = {
                    "status": "warning",
                    "message": "No active workers found"
                }
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
                    
        except Exception as e:
            health_status["components"]["celery"] = {
                "status": "unhealthy",
                "message": f"Celery monitoring error: {str(e)}"
            }
            health_status["overall_status"] = "unhealthy"
        
        return health_status
        
    except Exception as exc:
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unhealthy",
            "error": str(exc),
            "components": {}
        }


@celery_app.task(base=AsyncTask, bind=True, max_retries=2)
async def database_maintenance(self) -> Dict[str, Any]:
    """
    Perform database maintenance tasks including optimization and cleanup.
    
    Returns:
        Dict containing maintenance results
    """
    try:
        db = next(get_db())
        maintenance_results = {
            "timestamp": datetime.now().isoformat(),
            "tasks_completed": [],
            "errors": []
        }
        
        # Analyze table statistics
        try:
            # Update table statistics (PostgreSQL specific)
            db.execute(text("ANALYZE"))
            maintenance_results["tasks_completed"].append("Table statistics updated")
        except Exception as e:
            maintenance_results["errors"].append(f"Statistics update failed: {str(e)}")
        
        # Clean up orphaned records
        try:
            # Remove content items without associated websites
            orphaned_content = db.query(ContentItem).filter(
                ~ContentItem.website_id.in_(
                    db.query(Website.id)
                )
            )
            
            orphaned_count = orphaned_content.count()
            if orphaned_count > 0:
                orphaned_content.delete(synchronize_session=False)
                db.commit()
                maintenance_results["tasks_completed"].append(f"Removed {orphaned_count} orphaned content items")
            
        except Exception as e:
            db.rollback()
            maintenance_results["errors"].append(f"Orphaned records cleanup failed: {str(e)}")
        
        # Vacuum database (PostgreSQL specific)
        try:
            # Close current session for VACUUM
            db.close()
            
            # Create new connection for VACUUM (must be in autocommit mode)
            with engine.connect() as conn:
                conn.execute(text("VACUUM"))
            
            maintenance_results["tasks_completed"].append("Database vacuum completed")
            
        except Exception as e:
            maintenance_results["errors"].append(f"Database vacuum failed: {str(e)}")
        
        return {
            "status": "completed",
            "results": maintenance_results
        }
        
    except Exception as exc:
        self.retry(countdown=3600, exc=exc)  # Retry after 1 hour
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(base=AsyncTask, bind=True)
async def system_monitoring(self) -> Dict[str, Any]:
    """
    Monitor system performance and generate alerts if needed.
    
    Returns:
        Dict containing monitoring results and potential alerts
    """
    try:
        monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "alerts": []
        }
        
        # Database metrics
        try:
            db = next(get_db())
            
            # Count records in main tables
            website_count = db.query(func.count(Website.id)).scalar()
            content_count = db.query(func.count(ContentItem.id)).scalar()
            user_count = db.query(func.count(User.id)).scalar()
            summary_count = db.query(func.count(UserSummary.id)).scalar()
            interaction_count = db.query(func.count(UserContentInteraction.id)).scalar()
            
            monitoring_data["metrics"]["database"] = {
                "websites": website_count,
                "content_items": content_count,
                "users": user_count,
                "summaries": summary_count,
                "interactions": interaction_count
            }
            
            # Check for rapid growth that might indicate issues
            recent_content = db.query(func.count(ContentItem.id)).filter(
                ContentItem.scraped_at > datetime.now() - timedelta(hours=24)
            ).scalar()
            
            if recent_content > 10000:  # Threshold for alert
                monitoring_data["alerts"].append({
                    "type": "high_content_volume",
                    "message": f"High content volume in last 24h: {recent_content} items",
                    "severity": "warning"
                })
            
        except Exception as e:
            monitoring_data["alerts"].append({
                "type": "database_error",
                "message": f"Database monitoring failed: {str(e)}",
                "severity": "error"
            })
        
        # System resource monitoring
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            monitoring_data["metrics"]["system"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }
            
            # Generate alerts for high resource usage
            if cpu_percent > 85:
                monitoring_data["alerts"].append({
                    "type": "high_cpu_usage",
                    "message": f"CPU usage is {cpu_percent}%",
                    "severity": "warning"
                })
            
            if memory.percent > 85:
                monitoring_data["alerts"].append({
                    "type": "high_memory_usage",
                    "message": f"Memory usage is {memory.percent}%",
                    "severity": "warning"
                })
            
            if disk.percent > 85:
                monitoring_data["alerts"].append({
                    "type": "high_disk_usage",
                    "message": f"Disk usage is {disk.percent}%",
                    "severity": "warning"
                })
            
        except Exception as e:
            monitoring_data["alerts"].append({
                "type": "system_monitoring_error",
                "message": f"System monitoring failed: {str(e)}",
                "severity": "error"
            })
        
        # Celery queue monitoring
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            
            total_active = sum(len(tasks) for tasks in (active_tasks or {}).values())
            total_scheduled = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
            
            monitoring_data["metrics"]["celery"] = {
                "active_tasks": total_active,
                "scheduled_tasks": total_scheduled,
                "active_workers": len(active_tasks or {})
            }
            
            if total_active > 100:  # Threshold for queue backlog
                monitoring_data["alerts"].append({
                    "type": "high_task_backlog",
                    "message": f"High number of active tasks: {total_active}",
                    "severity": "warning"
                })
            
        except Exception as e:
            monitoring_data["alerts"].append({
                "type": "celery_monitoring_error",
                "message": f"Celery monitoring failed: {str(e)}",
                "severity": "error"
            })
        
        return {
            "status": "completed",
            "data": monitoring_data
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(base=AsyncTask, bind=True, max_retries=2)
async def cleanup_temp_files(self, max_age_days: int = 7) -> Dict[str, Any]:
    """
    Clean up temporary files and logs older than specified days.
    
    Args:
        max_age_days: Maximum age of files to keep
        
    Returns:
        Dict containing cleanup results
    """
    try:
        cleanup_results = {
            "timestamp": datetime.now().isoformat(),
            "directories_cleaned": [],
            "files_removed": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        # Define directories to clean
        temp_directories = [
            "/tmp",
            "./logs",
            "./temp",
            "./cache"
        ]
        
        for directory in temp_directories:
            if not os.path.exists(directory):
                continue
                
            try:
                files_removed = 0
                space_freed = 0
                
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_stat = os.stat(file_path)
                            file_time = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            if file_time < cutoff_time:
                                file_size = file_stat.st_size
                                os.remove(file_path)
                                files_removed += 1
                                space_freed += file_size
                                
                        except Exception as e:
                            cleanup_results["errors"].append(f"Failed to remove {file_path}: {str(e)}")
                
                if files_removed > 0:
                    cleanup_results["directories_cleaned"].append({
                        "directory": directory,
                        "files_removed": files_removed,
                        "space_freed_mb": round(space_freed / (1024*1024), 2)
                    })
                    
                    cleanup_results["files_removed"] += files_removed
                    cleanup_results["space_freed_mb"] += round(space_freed / (1024*1024), 2)
                
            except Exception as e:
                cleanup_results["errors"].append(f"Failed to clean directory {directory}: {str(e)}")
        
        return {
            "status": "completed",
            "results": cleanup_results
        }
        
    except Exception as exc:
        self.retry(countdown=1800, exc=exc)  # Retry after 30 minutes
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(base=AsyncTask, bind=True)
async def generate_system_report(self) -> Dict[str, Any]:
    """
    Generate comprehensive system status report.
    
    Returns:
        Dict containing detailed system report
    """
    try:
        # Run health check
        health_data = await health_check._run()
        
        # Run monitoring
        monitoring_data = await system_monitoring._run()
        
        # Get additional metrics
        db = next(get_db())
        
        # Database statistics
        db_stats = {
            "total_websites": db.query(func.count(Website.id)).scalar(),
            "active_websites": db.query(func.count(Website.id)).filter(Website.is_active == True).scalar(),
            "total_content": db.query(func.count(ContentItem.id)).scalar(),
            "recent_content_24h": db.query(func.count(ContentItem.id)).filter(
                ContentItem.scraped_at > datetime.now() - timedelta(hours=24)
            ).scalar(),
            "total_users": db.query(func.count(User.id)).scalar(),
            "active_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
            "total_summaries": db.query(func.count(UserSummary.id)).scalar(),
            "summaries_24h": db.query(func.count(UserSummary.id)).filter(
                UserSummary.created_at > datetime.now() - timedelta(hours=24)
            ).scalar()
        }
        
        # Compile comprehensive report
        system_report = {
            "report_timestamp": datetime.now().isoformat(),
            "health_status": health_data,
            "monitoring_data": monitoring_data,
            "database_statistics": db_stats,
            "summary": {
                "overall_health": health_data.get("overall_status", "unknown"),
                "critical_alerts": len([
                    alert for alert in monitoring_data.get("data", {}).get("alerts", [])
                    if alert.get("severity") == "error"
                ]),
                "warning_alerts": len([
                    alert for alert in monitoring_data.get("data", {}).get("alerts", [])
                    if alert.get("severity") == "warning"
                ]),
                "content_growth_24h": db_stats["recent_content_24h"],
                "summary_generation_24h": db_stats["summaries_24h"]
            }
        }
        
        return {
            "status": "completed",
            "report": system_report
        }
        
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }


# Periodic maintenance tasks
@celery_app.task(base=AsyncTask, name="hourly_health_check")
async def hourly_health_check():
    """Hourly system health check."""
    return await health_check._run()


@celery_app.task(base=AsyncTask, name="daily_database_maintenance")
async def daily_database_maintenance():
    """Daily database maintenance tasks."""
    return await database_maintenance._run()


@celery_app.task(base=AsyncTask, name="hourly_system_monitoring")
async def hourly_system_monitoring():
    """Hourly system performance monitoring."""
    return await system_monitoring._run()


@celery_app.task(base=AsyncTask, name="daily_temp_cleanup")
async def daily_temp_cleanup():
    """Daily temporary file cleanup."""
    return await cleanup_temp_files._run(max_age_days=7)


@celery_app.task(base=AsyncTask, name="daily_system_report")
async def daily_system_report():
    """Daily comprehensive system report generation."""
    return await generate_system_report._run()
