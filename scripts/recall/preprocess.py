from typing import Tuple, Optional, Dict
import re
from datetime import datetime, timedelta

def preprocess_user_query(text: str) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Inspect the user’s query and decide if it maps directly to one of our tools.
    Returns (tool_name, tool_args) or (None, None) if no shortcut applies.
    """

    t = text.strip().lower()

    # ── Shortcut: “logs for today” ────────────────────────────────
    if "logs for today" in t or "logs today" in t or "show me today's logs" in t:
        # since = midnight of the current day
        today_midnight = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return "search_logs_timewindow", {"since": today_midnight}
        
    lowered = user_input.lower()
    today = datetime.now()
    
    # Time-related keywords for semantic understanding
    today_keywords = ['today', 'this day', 'current day', 'now', 'present']
    yesterday_keywords = ['yesterday', 'last day', 'previous day', 'day before']
    recent_keywords = ['recent', 'lately', 'last few', 'past', 'before']
    
    # Check for "today" related queries
    if any(keyword in lowered for keyword in today_keywords) and ('what' in lowered or 'show' in lowered or 'activity' in lowered or 'do' in lowered or 'did' in lowered):
        start_of_today = datetime.combine(today.date(), datetime.min.time())
        return 'search_logs_timewindow', {'since': start_of_today}
    
    # Check for "yesterday" related queries
    if any(keyword in lowered for keyword in yesterday_keywords):
        yesterday_date = (today.date() - timedelta(days=1)).isoformat()
        return 'search_logs', {'query': yesterday_date}
    
    # Check for specific time periods (hours)
    hour_patterns = [
        r'(?:last|past|previous)\s+(\d+)\s+hours?',
        r'(\d+)\s+hours?\s+(?:ago|back)',
        r'past\s+(\d+)h',
        r'last\s+(\d+)h'
    ]
    
    for pattern in hour_patterns:
        match = re.search(pattern, lowered)
        if match:
            hours = int(match.group(1))
            since = today - timedelta(hours=hours)
            return 'search_logs_timewindow', {'since': since}
    
    # Check for day-based time periods
    day_patterns = [
        r'(?:last|past|previous)\s+(\d+)\s+days?',
        r'(\d+)\s+days?\s+(?:ago|back)',
        r'past\s+(\d+)d',
        r'last\s+(\d+)d'
    ]
    
    for pattern in day_patterns:
        match = re.search(pattern, lowered)
        if match:
            days = int(match.group(1))
            since = today - timedelta(days=days)
            return 'search_logs_timewindow', {'since': since}
    
    # Check for general recent activity queries
    if any(keyword in lowered for keyword in recent_keywords) and ('activity' in lowered or 'what' in lowered or 'show' in lowered or 'active' in lowered):
        # Default to last 24 hours for "recent" queries
        since = today - timedelta(days=1)
        return 'search_logs_timewindow', {'since': since}
    
    # Check for specific dates (YYYY-MM-DD format)
    date_match = re.search(r'(20\d{2}-\d{2}-\d{2})', user_input)
    if date_match:
        return 'search_logs', {'query': date_match.group(1)}
    
    # Check for relative time expressions
    relative_patterns = [
        (r'(?:before|within)\s+(?:one|1)\s+day', 1),
        (r'(?:before|within)\s+(?:two|2)\s+days?', 2),
        (r'(?:before|within)\s+(?:three|3)\s+days?', 3),
        (r'(?:before|within)\s+a\s+day', 1),
        (r'(?:before|within)\s+few\s+days?', 3),
        (r'this\s+week', 7),
        (r'past\s+week', 7)
    ]
    
    for pattern, days in relative_patterns:
        if re.search(pattern, lowered):
            since = today - timedelta(days=days)
            return 'search_logs_timewindow', {'since': since}
    
    return None, None 