# claude_monitor.py
import os
from pathlib import Path
from datetime import datetime, timedelta

# Windows path
CLAUDE_LOGS = Path(os.environ['APPDATA']) / 'Claude' / 'logs'
# Or check: %LOCALAPPDATA%\Claude\logs

def analyze_claude_logs():
    """
    Find patterns like:
    - Message timestamps
    - Model switches (Opus vs Sonnet)
    - Rate limit messages
    - Session boundaries
    """
    with open(CLAUDE_LOGS, 'r', encoding="utf-8") as log_file:
        pass
    # Parse log files
    # Look for timestamp patterns
    # Identify usage windows
    # Calculate burn rate