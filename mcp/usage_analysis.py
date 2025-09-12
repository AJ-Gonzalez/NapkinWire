import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

def find_claude_logs() -> Optional[Path]:
    """Find Claude Desktop log directory in standard Windows locations"""
    potential_paths = [
        Path(os.environ.get('APPDATA', '')) / 'Claude' / 'logs',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Claude' / 'logs'
    ]
    
    for path in potential_paths:
        if path.exists() and path.is_dir():
            logger.info(f"Found Claude logs at: {path}")
            return path
    
    logger.warning("No Claude log directory found")
    return None

def get_recent_log_files(log_dir: Path, hours: int = 24) -> List[Path]:
    """Get log files modified within the last N hours"""
    cutoff = datetime.now() - timedelta(hours=hours)
    log_files = []
    
    try:
        for file in log_dir.glob('*.log*'):
            if file.is_file() and datetime.fromtimestamp(file.stat().st_mtime) > cutoff:
                log_files.append(file)
        
        return sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True)
    except Exception as e:
        logger.error(f"Error reading log files: {e}")
        return []

def parse_timestamp_with_timezone(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string and return timezone-aware datetime object"""
    if not timestamp_str:
        return None
    
    # Handle UTC timestamps with 'Z' suffix
    if timestamp_str.endswith('Z'):
        formats_utc = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        for fmt in formats_utc:
            try:
                return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    
    # Handle timestamps without timezone info - assume local time, convert to UTC
    formats_local = [
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S'
    ]
    for fmt in formats_local:
        try:
            dt_local = datetime.strptime(timestamp_str, fmt)
            # Convert local time to UTC (approximate - this assumes system timezone)
            dt_utc = dt_local.replace(tzinfo=timezone.utc)
            return dt_utc
        except ValueError:
            continue
    
    return None

def parse_log_entry(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single log line and extract relevant information"""
    try:
        # Try parsing as JSON first
        if line.strip().startswith('{'):
            data = json.loads(line.strip())
            timestamp_str = data.get('timestamp')
            parsed_timestamp = parse_timestamp_with_timezone(timestamp_str) if timestamp_str else None
            return {
                'timestamp': parsed_timestamp,
                'level': data.get('level'),
                'message': data.get('message', ''),
                'raw': data
            }
    except json.JSONDecodeError:
        pass
    
    # Try parsing common log patterns
    timestamp_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\.\d]*Z?)'
    match = re.search(timestamp_pattern, line)
    
    if match:
        timestamp_str = match.group(1)
        parsed_timestamp = parse_timestamp_with_timezone(timestamp_str)
        return {
            'timestamp': parsed_timestamp,
            'level': None,
            'message': line,
            'raw': line
        }
    
    return None

def extract_model_info(entry: Dict[str, Any]) -> Optional[str]:
    """Extract model information from log entry"""
    message = entry.get('message', '').lower()
    raw = str(entry.get('raw', '')).lower()
    
    # Look for model mentions
    if 'opus' in message or 'opus' in raw:
        return 'opus'
    elif 'sonnet' in message or 'sonnet' in raw:
        return 'sonnet'
    
    return None

def detect_rate_limit(entry: Dict[str, Any]) -> bool:
    """Detect if log entry indicates rate limiting"""
    message = entry.get('message', '').lower()
    indicators = ['rate limit', 'too many requests', 'quota exceeded', '429']
    
    return any(indicator in message for indicator in indicators)

def calculate_usage_window(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate current usage window based on log entries"""
    if not entries:
        return {
            'window_started': None,
            'time_elapsed': 0,
            'estimated_remaining': 18000,  # 5 hours in seconds
            'messages_this_window': 0
        }
    
    # Use timezone-aware current time
    now = datetime.now(timezone.utc)
    window_start = None
    message_count = 0
    
    # Look for recent rate limit events
    for entry in reversed(entries):
        if detect_rate_limit(entry):
            timestamp = entry.get('timestamp')
            if timestamp and isinstance(timestamp, datetime):
                window_start = timestamp
                break
    
    # If no rate limit found, use earliest message in last 5 hours
    if not window_start:
        five_hours_ago = now - timedelta(hours=5)
        for entry in entries:
            timestamp = entry.get('timestamp')
            if timestamp and isinstance(timestamp, datetime):
                if timestamp >= five_hours_ago:
                    if not window_start or timestamp < window_start:
                        window_start = timestamp
    
    # Default to 5 hours ago if still no window start
    if not window_start:
        window_start = now - timedelta(hours=5)
    
    # Count messages in current window
    for entry in entries:
        timestamp = entry.get('timestamp')
        if timestamp and isinstance(timestamp, datetime):
            if timestamp >= window_start:
                message_count += 1
    
    elapsed_seconds = int((now - window_start).total_seconds())
    remaining_seconds = max(0, 18000 - elapsed_seconds)  # 5 hours = 18000 seconds
    
    return {
        'window_started': window_start.isoformat(),
        'time_elapsed': elapsed_seconds,
        'estimated_remaining': remaining_seconds,
        'messages_this_window': message_count
    }

def analyze_claude_logs() -> Dict[str, Any]:
    """
    Analyze Claude Desktop logs and return usage patterns
    
    Returns:
        Dict with window_started, time_elapsed, estimated_remaining, messages_this_window
    """
    try:
        # Find log directory
        log_dir = find_claude_logs()
        if not log_dir:
            return {
                'error': 'Claude log directory not found',
                'window_started': None,
                'time_elapsed': 0,
                'estimated_remaining': 18000,
                'messages_this_window': 0
            }
        
        # Get recent log files
        log_files = get_recent_log_files(log_dir, hours=6)  # Look at last 6 hours
        if not log_files:
            return {
                'window_started': None,
                'time_elapsed': 0,
                'estimated_remaining': 18000,
                'messages_this_window': 0
            }
        
        # Parse log entries
        all_entries = []
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        entry = parse_log_entry(line)
                        if entry:
                            all_entries.append(entry)
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
                continue
        
        # Calculate usage window
        result = calculate_usage_window(all_entries)
        
        # Add model usage stats if available
        model_counts = {'opus': 0, 'sonnet': 0, 'unknown': 0}
        for entry in all_entries:
            model = extract_model_info(entry)
            if model:
                model_counts[model] += 1
            else:
                model_counts['unknown'] += 1
        
        result['model_usage'] = model_counts
        
        logger.info(f"Analysis complete: {result['messages_this_window']} messages in current window")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing Claude logs: {e}")
        return {
            'error': str(e),
            'window_started': None,
            'time_elapsed': 0,
            'estimated_remaining': 18000,
            'messages_this_window': 0
        }