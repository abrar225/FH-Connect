import asyncio
from datetime import datetime
from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import db

logger = get_logger("alerts")


class AlertLevel:
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


async def check_intent_queue_alerts() -> tuple[str, str]:
    """Check intent queue for pending/failed messages and alert if thresholds exceeded."""
    if not settings.REDIS_URL:
        return AlertLevel.NONE, ""

    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.REDIS_URL)
        try:
            pending = await r.xlen(settings.INTENT_STREAM_NAME)
            failed = await r.xlen(f"{settings.INTENT_STREAM_NAME}:dlq")
            
            level = AlertLevel.NONE
            message = ""
            
            if pending >= settings.INTENT_QUEUE_ALERT_PENDING:
                level = AlertLevel.CRITICAL
                message = f"Intent queue backlog critical: {pending} pending messages (threshold: {settings.INTENT_QUEUE_ALERT_PENDING})"
            elif pending >= settings.INTENT_QUEUE_ALERT_PENDING * 0.8:
                level = AlertLevel.WARNING
                message = f"Intent queue backlog building: {pending} pending messages"
            
            if failed >= settings.INTENT_QUEUE_ALERT_FAILED:
                level = AlertLevel.CRITICAL
                message = f"Intent queue failures critical: {failed} failed messages (threshold: {settings.INTENT_QUEUE_ALERT_FAILED})"
            
            if message:
                logger.warning(message)
            
            return level, message
        finally:
            await r.aclose()
    except Exception as e:
        logger.error(f"Failed to check intent queue alerts: {e}")
        return AlertLevel.NONE, ""


async def check_report_queue_alerts() -> tuple[str, str]:
    """Check report queue for pending/failed messages and alert if thresholds exceeded."""
    if not settings.REDIS_URL:
        return AlertLevel.NONE, ""

    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.REDIS_URL)
        try:
            pending = await r.xlen(settings.REPORT_STREAM_NAME)
            failed = await r.xlen(f"{settings.REPORT_STREAM_NAME}:dlq")
            
            level = AlertLevel.NONE
            message = ""
            
            if pending >= settings.REPORT_QUEUE_ALERT_PENDING:
                level = AlertLevel.CRITICAL
                message = f"Report queue backlog critical: {pending} pending messages (threshold: {settings.REPORT_QUEUE_ALERT_PENDING})"
            elif pending >= settings.REPORT_QUEUE_ALERT_PENDING * 0.8:
                level = AlertLevel.WARNING
                message = f"Report queue backlog building: {pending} pending messages"
            
            if failed >= settings.REPORT_QUEUE_ALERT_FAILED:
                level = AlertLevel.CRITICAL
                message = f"Report queue failures critical: {failed} failed messages (threshold: {settings.REPORT_QUEUE_ALERT_FAILED})"
            
            if message:
                logger.warning(message)
            
            return level, message
        finally:
            await r.aclose()
    except Exception as e:
        logger.error(f"Failed to check report queue alerts: {e}")
        return AlertLevel.NONE, ""


async def check_database_health() -> tuple[str, str]:
    """Check database connection and alert if unhealthy."""
    if not db.pool:
        return AlertLevel.CRITICAL, "Database not connected"

    try:
        result = await db.pool.fetchval("SELECT 1")
        if result != 1:
            return AlertLevel.CRITICAL, "Database health check failed"
        return AlertLevel.NONE, ""
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return AlertLevel.CRITICAL, f"Database error: {str(e)}"


async def run_health_checks():
    """Run all health checks and log alerts."""
    checks = [
        ("Intent Queue", check_intent_queue_alerts),
        ("Report Queue", check_report_queue_alerts),
        ("Database", check_database_health),
    ]
    
    critical_alerts = []
    
    for name, check_func in checks:
        level, message = await check_func()
        if level == AlertLevel.CRITICAL:
            critical_alerts.append(f"[{name}] {message}")
        elif level == AlertLevel.WARNING:
            logger.warning(f"[{name}] {message}")
    
    if critical_alerts:
        logger.critical(f"Critical alerts detected: {'; '.join(critical_alerts)}")
    
    return critical_alerts


async def start_alert_monitor(interval_seconds: int = 60):
    """Start the alert monitoring loop."""
    logger.info(f"Starting alert monitor (interval: {interval_seconds}s)")
    
    while True:
        try:
            await run_health_checks()
        except Exception as e:
            logger.error(f"Alert monitor error: {e}")
        
        await asyncio.sleep(interval_seconds)