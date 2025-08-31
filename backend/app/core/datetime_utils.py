"""
Datetime utilities for timezone-aware datetime handling
Fixes deprecation warnings for datetime.now(timezone.utc)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

def utc_now_naive() -> datetime:
    """Get current UTC time as naive datetime (for backward compatibility)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def days_ago(days: int) -> datetime:
    """Get datetime for specified days ago from now (UTC)"""
    return utc_now() - timedelta(days=days)

def days_from_now(days: int) -> datetime:
    """Get datetime for specified days from now (UTC)"""
    return utc_now() + timedelta(days=days)

def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to UTC timezone-aware"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume it's already in UTC if naive
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def to_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert timezone-aware datetime to naive (for DB storage)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.replace(tzinfo=None)
