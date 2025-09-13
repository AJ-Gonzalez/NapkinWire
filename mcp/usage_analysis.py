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
    
    # Handle UTC timestamps with 'Z' suffix (Claude logs use this format)
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
    
    # Handle timestamps without timezone info - these should be rare in Claude logs
    # For safety, assume they are UTC (Claude logs are typically UTC)
    formats_local = [
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S'
    ]
    for fmt in formats_local:
        try:
            dt_naive = datetime.strptime(timestamp_str, fmt)
            # Assume UTC for Claude logs (safer than assuming local time)
            return dt_naive.replace(tzinfo=timezone.utc)
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

def is_user_message(entry: Dict[str, Any]) -> bool:
    """Detect if log entry represents a user message (not system/internal)"""
    message = entry.get('message', '').lower()
    
    # Look for patterns that indicate user interaction
    user_indicators = [
        'message from client',  # MCP client messages
        'user:',               # Direct user messages
        'human:',              # User input
        '"method":"'           # API method calls (user actions)
    ]
    
    # Exclude system/internal messages
    system_indicators = [
        'message from server',  # Server responses
        'assistant:',          # AI responses
        'system:',             # System messages
        'debug',               # Debug logs
        'error',               # Error logs
        'warning'              # Warning logs
    ]
    
    # Check for user indicators
    has_user_indicator = any(indicator in message for indicator in user_indicators)
    has_system_indicator = any(indicator in message for indicator in system_indicators)
    
    # Must have user indicator and not have system indicator
    return has_user_indicator and not has_system_indicator

def calculate_usage_window(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate current usage window based on log entries
    
    Claude has a 5-hour usage window followed by a 5-hour cooldown.
    This function finds the current active window and counts user messages within it.
    """
    if not entries:
        return {
            'window_started': None,
            'time_elapsed': 0,
            'estimated_remaining': 18000,  # 5 hours in seconds
            'messages_this_window': 0,
            'debug_info': 'No log entries found'
        }
    
    now = datetime.now(timezone.utc)
    WINDOW_DURATION = timedelta(hours=5)  # 5 hour usage window
    COOLDOWN_DURATION = timedelta(hours=5)  # 5 hour cooldown
    
    # Step 1: Filter and sort entries by timestamp
    valid_entries = []
    for entry in entries:
        timestamp = entry.get('timestamp')
        if timestamp and isinstance(timestamp, datetime):
            valid_entries.append((timestamp, entry))
    
    if not valid_entries:
        return {
            'window_started': None,
            'time_elapsed': 0,
            'estimated_remaining': 18000,
            'messages_this_window': 0,
            'debug_info': 'No valid timestamps found'
        }
    
    # Sort by timestamp (oldest first)
    valid_entries.sort(key=lambda x: x[0])
    
    # Step 2: Look for the most recent rate limit to determine window boundaries
    window_start = None
    last_rate_limit = None
    
    # Find most recent rate limit event
    for timestamp, entry in reversed(valid_entries):
        if detect_rate_limit(entry):
            last_rate_limit = timestamp
            break
    
    # Step 3: Check for recent user activity first (overrides old rate limits)
    recent_cutoff = now - timedelta(hours=1)  # Look for activity in last hour
    recent_user_messages = []
    
    # Collect recent user messages
    for timestamp, entry in valid_entries:
        if timestamp >= recent_cutoff and is_user_message(entry):
            recent_user_messages.append(timestamp)
    
    # Step 4: Determine current window start
    if recent_user_messages:
        # We have recent activity - start new window from recent activity
        first_recent = min(recent_user_messages)
        
        # If there's a rate limit that's more recent than 5 hours ago, respect it
        if last_rate_limit and (now - last_rate_limit).total_seconds() < 18000:  # 5 hours
            potential_window_start = last_rate_limit + COOLDOWN_DURATION
            if potential_window_start <= first_recent:
                # Cooldown ended before recent activity, use recent activity
                window_start = first_recent
                logger.info(f"Window start based on recent activity after cooldown: {window_start}")
            else:
                # Still in cooldown period
                return {
                    'window_started': None,
                    'time_elapsed': 0,
                    'estimated_remaining': 0,
                    'messages_this_window': 0,
                    'debug_info': f'Still in cooldown until {potential_window_start}'
                }
        else:
            # No recent rate limit, start from recent activity
            window_start = first_recent
            logger.info(f"Window start based on recent activity: {window_start} (messages: {len(recent_user_messages)})")
    
    elif last_rate_limit:
        # No recent activity, but have old rate limit
        potential_window_start = last_rate_limit + COOLDOWN_DURATION
        if potential_window_start <= now:
            # Cooldown ended, but no activity - window could start now but has no messages
            window_start = now  # Window available but unused
            logger.info(f"Window available after cooldown, but no recent activity: {window_start}")
        else:
            # Still in cooldown period
            return {
                'window_started': None,
                'time_elapsed': 0,
                'estimated_remaining': 0,
                'messages_this_window': 0,
                'debug_info': f'Still in cooldown until {potential_window_start}'
            }
    else:
        # No rate limits at all - look for any user activity
        max_lookback = now - timedelta(hours=6)
        first_user_message = None
        
        for timestamp, entry in valid_entries:
            if timestamp >= max_lookback and is_user_message(entry):
                first_user_message = timestamp
                break
        
        if first_user_message:
            # Check if this activity is still within a valid window
            elapsed_from_first = (now - first_user_message).total_seconds()
            if elapsed_from_first <= 18000:  # Within 5 hours
                window_start = first_user_message
                logger.info(f"Window start based on user activity: {window_start}")
            else:
                # Old activity is beyond 5 hours, session expired
                return {
                    'window_started': first_user_message.isoformat(),
                    'time_elapsed': int(elapsed_from_first),
                    'estimated_remaining': 0,
                    'messages_this_window': 0,
                    'debug_info': f'Session expired {int(elapsed_from_first - 18000)} seconds ago'
                }
        else:
            # No user messages found, assume window just started
            window_start = now
            logger.info("No user messages found, assuming window just started")
    
    # Step 4: Calculate time elapsed and remaining
    elapsed_seconds = int((now - window_start).total_seconds())
    
    # Sanity check: elapsed time cannot exceed 5 hours in an active window
    if elapsed_seconds > 18000:  # 5 hours = 18000 seconds
        # Window has expired, should be in cooldown
        return {
            'window_started': window_start.isoformat(),
            'time_elapsed': elapsed_seconds,
            'estimated_remaining': 0,
            'messages_this_window': 0,
            'debug_info': f'Window expired {elapsed_seconds - 18000} seconds ago'
        }
    
    remaining_seconds = max(0, 18000 - elapsed_seconds)
    
    # Step 5: Count user messages in current window
    message_count = 0
    for timestamp, entry in valid_entries:
        if timestamp >= window_start and is_user_message(entry):
            message_count += 1
    
    debug_info = f'Analyzed {len(valid_entries)} entries, found {message_count} user messages'
    if last_rate_limit:
        debug_info += f', last rate limit: {last_rate_limit}'
    
    logger.info(f"Window analysis: start={window_start}, elapsed={elapsed_seconds}s, remaining={remaining_seconds}s, messages={message_count}")
    
    return {
        'window_started': window_start.isoformat(),
        'time_elapsed': elapsed_seconds,
        'estimated_remaining': remaining_seconds,
        'messages_this_window': message_count,
        'debug_info': debug_info
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
        
        # Get recent log files (look at last 12 hours to catch rate limits and window resets)
        log_files = get_recent_log_files(log_dir, hours=12)
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