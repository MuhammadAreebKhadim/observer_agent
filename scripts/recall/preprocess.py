from typing import Tuple, Optional, Dict
import re
from datetime import datetime, timedelta

def preprocess_user_query(user_input: str) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Inspect the user’s query and decide if it maps directly to one of our tools.
    Returns (tool_name, tool_args) or (None, None) if no shortcut applies.
    """
    lowered = user_input.strip().lower()
    now = datetime.now()

    # Shortcut: "logs for today"
    if any(phrase in lowered for phrase in ["logs for today", "logs today", "show me today's logs"]):
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return "search_logs_timewindow", {"since": start_of_today}

    # Check for "yesterday"
    if any(keyword in lowered for keyword in ['yesterday', 'last day', 'previous day', 'day before']):
        yesterday_date = (now.date() - timedelta(days=1)).isoformat()
        return 'search_logs', {'query': yesterday_date}

    # Specific hours patterns
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
            since = now - timedelta(hours=hours)
            return 'search_logs_timewindow', {'since': since}

    # Specific days patterns
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
            since = now - timedelta(days=days)
            return 'search_logs_timewindow', {'since': since}

    # General "recent" queries default to last 24h
    if any(kw in lowered for kw in ['recent', 'lately', 'last few', 'past']) and \
       any(word in lowered for word in ['activity', 'what', 'show', 'active']):
        since = now - timedelta(days=1)
        return 'search_logs_timewindow', {'since': since}

    # Specific date in YYYY-MM-DD
    date_match = re.search(r'(20\d{2}-\d{2}-\d{2})', lowered)
    if date_match:
        return 'search_logs', {'query': date_match.group(1)}

    # Relative "within X days" or "this week"
    relative_patterns = [
        (r'(?:before|within)\s+(?:one|1)\s+day', 1),
        (r'(?:before|within)\s+(?:two|2)\s+days?', 2),
        (r'(?:before|within)\s+(?:three|3)\s+days?', 3),
        (r'this\s+week', 7),
        (r'past\s+week', 7)
    ]
    for pattern, days in relative_patterns:
        if re.search(pattern, lowered):
            since = now - timedelta(days=days)
            return 'search_logs_timewindow', {'since': since}

    # No shortcut
    return None, None
