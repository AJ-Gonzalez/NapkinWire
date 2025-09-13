from mcp.server.fastmcp import FastMCP
from constants import JSON_FORMAT
from usage_analysis import analyze_claude_logs

import signal
import sys
import json
import os
import logging
import ast
import re
import time
import threading
import subprocess
import tempfile
from pathlib import Path
from config import TICKETS
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
try:
    import fcntl  # For file locking on Unix
except ImportError:
    fcntl = None
try:
    import msvcrt  # For file locking on Windows
except ImportError:
    msvcrt = None

# PyWebView import with fallback
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    crud_logger = logging.getLogger('napkinwire_crud')
    crud_logger.warning("PyWebView not available - spawn_diagram_editor will be disabled")

# Configure logging for CRUD operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crud.log')
    ]
)
crud_logger = logging.getLogger('napkinwire_crud')


def cleanup(signum, frame):
    # Clean up resources
    sys.exit(0)


signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)


# Create an MCP server
mcp = FastMCP("NapkinWire")

# Helper functions for ticket management
def get_tickets_file_path() -> str:
    """Get the path to the tickets.json file"""
    tickets_path = TICKETS
    crud_logger.info(f"Tickets file path: {tickets_path}")
    return tickets_path

def load_tickets_data() -> Dict[str, Any]:
    """Load tickets data from JSON file or create default structure"""
    file_path = get_tickets_file_path()
    try:
        if os.path.exists(file_path):
            crud_logger.info(f"Loading existing tickets file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default structure if file doesn't exist
            crud_logger.info(f"Creating new tickets file structure at: {file_path}")
            default_data = {
                "metadata": {
                    "version": "1.0.0",
                    "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_id": 1,
                    "project": "napkinwire"
                },
                "tickets": [],
                "templates": {
                    "bug_fix": {
                        "priority": "high",
                        "requirements": ["Root cause identified", "Fix implemented", "Test added"],
                        "acceptance_criteria": ["Bug no longer reproduces", "No regressions"]
                    },
                    "feature": {
                        "priority": "medium",
                        "requirements": ["User story clear", "Implementation complete"],
                        "acceptance_criteria": ["Feature works as described", "Code reviewed"]
                    }
                }
            }
            return default_data
    except (json.JSONDecodeError, IOError) as e:
        crud_logger.error(f"Error loading tickets file {file_path}: {e}")
        # Return minimal structure to allow recovery
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "next_id": 1,
                "project": "napkinwire"
            },
            "tickets": [],
            "templates": {}
        }

def save_tickets_data(data: Dict[str, Any]) -> bool:
    """Save tickets data to JSON file with pretty formatting"""
    file_path = get_tickets_file_path()
    try:
        # Update last_updated timestamp
        data["metadata"]["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Write to temp file first for atomic operation
        temp_path = file_path + ".tmp"
        crud_logger.info(f"Saving tickets data to: {file_path}")
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Replace original file
        os.replace(temp_path, file_path)
        crud_logger.info(f"Successfully saved tickets data to: {file_path}")
        return True
    except (IOError, OSError) as e:
        crud_logger.error(f"Error saving tickets file {file_path}: {e}")
        return False


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def napkinwire_create_ticket(
    title: str,
    description: str,
    priority: str,
    requirements: List[str],
    acceptance_criteria: List[str],
    files_affected: List[str]
) -> Dict[str, Any]:
    """Create a new ticket with auto-generated ID"""
    crud_logger.info(f"Creating new ticket: '{title}' with priority '{priority}'")
    try:
        # Validate priority
        valid_priorities = ["high", "medium", "low"]
        if priority not in valid_priorities:
            crud_logger.warning(f"Invalid priority '{priority}' provided for ticket '{title}'")
            return {"success": False, "error": f"Priority must be one of: {valid_priorities}"}
        
        # Load current data
        data = load_tickets_data()
        
        # Generate ticket ID
        next_id = data["metadata"]["next_id"]
        ticket_id = f"TICKET-{next_id:03d}"
        
        # Create timestamp
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create new ticket
        new_ticket = {
            "id": ticket_id,
            "title": title,
            "status": "todo",
            "priority": priority,
            "created_at": now,
            "updated_at": now,
            "description": description,
            "requirements": requirements,
            "acceptance_criteria": acceptance_criteria,
            "files_affected": files_affected,
            "dependencies": [],
            "outcome": None,
            "notes": None
        }
        
        # Add ticket to data
        data["tickets"].append(new_ticket)
        
        # Update next_id
        data["metadata"]["next_id"] = next_id + 1
        
        # Save data
        if save_tickets_data(data):
            crud_logger.info(f"Successfully created ticket {ticket_id}: {title}")
            return {"success": True, "ticket_id": ticket_id}
        else:
            crud_logger.error(f"Failed to save ticket data for {ticket_id}: {title}")
            return {"success": False, "error": "Failed to save ticket data"}
            
    except Exception as e:
        crud_logger.error(f"Exception creating ticket '{title}': {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def napkinwire_list_tickets(status: str = "all") -> List[Dict[str, Any]]:
    """List tickets with optional status filter, sorted by priority then created_at"""
    crud_logger.info(f"Listing tickets with status filter: '{status}'")
    try:
        # Validate status
        valid_statuses = ["todo", "in_progress", "done", "blocked", "all"]
        if status not in valid_statuses:
            crud_logger.warning(f"Invalid status filter '{status}' provided")
            return [{"error": f"Status must be one of: {valid_statuses}"}]
        
        # Load data
        data = load_tickets_data()
        tickets = data.get("tickets", [])
        
        # Filter by status if not "all"
        if status != "all":
            tickets = [t for t in tickets if t.get("status") == status]
        
        # Define priority order for sorting
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        # Sort by priority first, then by created_at
        sorted_tickets = sorted(
            tickets,
            key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 1),
                t.get("created_at", "")
            )
        )
        
        # Return simplified list with key fields
        result = []
        for ticket in sorted_tickets:
            result.append({
                "id": ticket.get("id"),
                "title": ticket.get("title"),
                "status": ticket.get("status"),
                "priority": ticket.get("priority"),
                "created_at": ticket.get("created_at")
            })
        
        crud_logger.info(f"Successfully listed {len(result)} tickets with status filter: {status}")
        return result
        
    except Exception as e:
        crud_logger.error(f"Exception listing tickets with status '{status}': {e}")
        return [{"error": str(e)}]

@mcp.tool()
def napkinwire_update_ticket_status(ticket_id: str, new_status: str) -> Dict[str, Any]:
    """Update the status of an existing ticket"""
    crud_logger.info(f"Updating ticket {ticket_id} status to '{new_status}'")
    try:
        # Validate status
        valid_statuses = ["todo", "in_progress", "done", "blocked"]
        if new_status not in valid_statuses:
            crud_logger.warning(f"Invalid status '{new_status}' provided for ticket {ticket_id}")
            return {"success": False, "error": f"Status must be one of: {valid_statuses}"}
        
        # Load data
        data = load_tickets_data()
        tickets = data.get("tickets", [])
        
        # Find the ticket
        ticket_found = False
        for ticket in tickets:
            if ticket.get("id") == ticket_id:
                ticket_found = True
                old_status = ticket.get("status")
                
                # Update status and timestamp
                ticket["status"] = new_status
                ticket["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Save data
                if save_tickets_data(data):
                    crud_logger.info(f"Successfully updated {ticket_id} status from '{old_status}' to '{new_status}'")
                    return {
                        "success": True,
                        "message": f"Updated {ticket_id} to {new_status}"
                    }
                else:
                    crud_logger.error(f"Failed to save ticket data when updating {ticket_id}")
                    return {"success": False, "error": "Failed to save ticket data"}
        
        if not ticket_found:
            crud_logger.warning(f"Ticket {ticket_id} not found for status update")
            return {"success": False, "error": f"Ticket {ticket_id} not found"}
            
    except Exception as e:
        crud_logger.error(f"Exception updating ticket {ticket_id} status: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def napkinwire_get_ticket_details(ticket_id: str) -> Dict[str, Any]:
    """Get full details of a specific ticket for implementation"""
    crud_logger.info(f"Retrieving details for ticket {ticket_id}")
    try:
        # Load data
        data = load_tickets_data()
        tickets = data.get("tickets", [])
        
        # Find the ticket
        for ticket in tickets:
            if ticket.get("id") == ticket_id:
                crud_logger.info(f"Successfully retrieved details for ticket {ticket_id}")
                return ticket
        
        # Ticket not found
        crud_logger.warning(f"Ticket {ticket_id} not found when retrieving details")
        return {"error": f"Ticket {ticket_id} not found"}
        
    except Exception as e:
        crud_logger.error(f"Exception getting ticket {ticket_id} details: {e}")
        return {"error": str(e)}

def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration"""
    if seconds <= 0:
        return "0 seconds"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs > 0 and hours == 0:  # Only show seconds if less than an hour
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    
    return ", ".join(parts) if parts else "0 seconds"

def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to human-readable format"""
    try:
        if not iso_timestamp:
            return "Unknown"
        
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', ''))
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(diff.total_seconds() // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    except Exception:
        return iso_timestamp

def create_summary_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create summary format report"""
    if 'error' in data:
        return {
            "status": "error",
            "message": data['error'],
            "summary": "Unable to analyze Claude logs"
        }
    
    window_started = data.get('window_started')
    time_elapsed = data.get('time_elapsed', 0)
    estimated_remaining = data.get('estimated_remaining', 18000)
    messages_count = data.get('messages_this_window', 0)
    
    # Calculate burn rate (messages per hour)
    burn_rate = 0
    if time_elapsed > 0:
        burn_rate = round((messages_count / time_elapsed) * 3600, 1)
    
    # Create human-readable summary
    window_status = "Active" if estimated_remaining > 0 else "Expired"
    time_remaining_str = format_duration(estimated_remaining)
    time_elapsed_str = format_duration(time_elapsed)
    window_start_str = format_timestamp(window_started) if window_started else "Unknown"
    
    return {
        "window_status": window_status,
        "window_started": window_start_str,
        "time_elapsed": time_elapsed_str,
        "time_remaining": time_remaining_str,
        "messages_this_window": messages_count,
        "current_burn_rate": f"{burn_rate} messages/hour" if burn_rate > 0 else "No activity",
        "recommendation": "You're in good shape!" if estimated_remaining > 3600 else "Consider slowing down usage"
    }

def create_detailed_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create detailed format report"""
    if 'error' in data:
        return {
            "error": data['error'],
            "analysis": "Unable to perform detailed analysis"
        }
    
    model_usage = data.get('model_usage', {})
    total_models = sum(model_usage.values())
    
    # Model usage breakdown
    model_breakdown = {}
    for model, count in model_usage.items():
        if total_models > 0:
            percentage = round((count / total_models) * 100, 1)
            model_breakdown[model] = f"{count} messages ({percentage}%)"
        else:
            model_breakdown[model] = f"{count} messages"
    
    # Usage patterns analysis
    time_elapsed = data.get('time_elapsed', 0)
    messages_count = data.get('messages_this_window', 0)
    
    patterns = []
    if time_elapsed > 0 and messages_count > 0:
        avg_interval = time_elapsed / messages_count if messages_count > 0 else 0
        if avg_interval < 60:
            patterns.append("High intensity usage detected")
        elif avg_interval < 300:
            patterns.append("Moderate usage pattern")
        else:
            patterns.append("Light usage pattern")
    
    # Recommendations
    recommendations = []
    estimated_remaining = data.get('estimated_remaining', 18000)
    
    if estimated_remaining < 1800:  # Less than 30 minutes
        recommendations.append("Usage window expires soon - consider wrapping up current tasks")
    elif estimated_remaining < 3600:  # Less than 1 hour
        recommendations.append("About 1 hour remaining in current window")
    else:
        recommendations.append("Plenty of time remaining in current usage window")
    
    if messages_count > 100:
        recommendations.append("High message count - consider consolidating requests")
    
    return {
        "model_usage_breakdown": model_breakdown,
        "total_messages_analyzed": total_models,
        "usage_patterns": patterns,
        "session_analysis": {
            "average_message_interval": f"{time_elapsed // messages_count if messages_count > 0 else 0} seconds",
            "peak_usage_detected": messages_count > 50
        },
        "recommendations": recommendations,
        "raw_data": {
            "window_started": data.get('window_started'),
            "time_elapsed_seconds": time_elapsed,
            "estimated_remaining_seconds": estimated_remaining
        }
    }

@mcp.tool()
def napkinwire_claude_usage_analysis(detail_level: str = "summary") -> Dict[str, Any]:
    """Analyze Claude Desktop usage with configurable detail levels
    
    Args:
        detail_level: Level of detail - 'summary', 'detailed', or 'both'
    
    Returns:
        Dict with usage analysis based on detail_level
    """
    crud_logger.info(f"Running Claude usage analysis with detail_level: {detail_level}")
    
    try:
        # Validate detail_level
        valid_levels = ["summary", "detailed", "both"]
        if detail_level not in valid_levels:
            return {
                "error": f"Invalid detail_level '{detail_level}'. Must be one of: {valid_levels}"
            }
        
        # Get usage analysis data
        usage_data = analyze_claude_logs()
        
        # Generate reports based on detail level
        if detail_level == "summary":
            result = create_summary_report(usage_data)
            result["detail_level"] = "summary"
        
        elif detail_level == "detailed":
            result = create_detailed_report(usage_data)
            result["detail_level"] = "detailed"
        
        elif detail_level == "both":
            summary = create_summary_report(usage_data)
            detailed = create_detailed_report(usage_data)
            
            result = {
                "detail_level": "both",
                "summary": summary,
                "detailed": detailed
            }
        
        crud_logger.info(f"Successfully completed Claude usage analysis for {detail_level} mode")
        return result
        
    except Exception as e:
        crud_logger.error(f"Error in Claude usage analysis: {e}")
        return {
            "error": str(e),
            "detail_level": detail_level,
            "message": "Failed to analyze Claude usage logs"
        }

# Cache for project tree results
_project_tree_cache = {}
_cache_timestamp = 0
_cache_duration = 300  # 5 minutes

def get_project_root() -> Path:
    """Get project root from TICKETS file path directory"""
    tickets_path = Path(TICKETS)
    return tickets_path.parent

def load_napkin_ignore(project_root: Path) -> set:
    """Load .napkinignore file and return set of patterns to ignore"""
    ignore_file = project_root / '.napkinignore'
    ignore_patterns = {
        # Default ignores
        '__pycache__', '*.pyc', '.git', '.vscode', '.idea',
        'node_modules', 'venv', '.venv', 'env', '.env',
        '.DS_Store', 'Thumbs.db', '*.log', '.pytest_cache',
        'dist', 'build', '*.egg-info', '.mypy_cache'
    }
    
    if ignore_file.exists():
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.add(line)
        except Exception as e:
            crud_logger.warning(f"Error reading .napkinignore: {e}")
    
    return ignore_patterns

def should_ignore_path(path: Path, ignore_patterns: set, project_root: Path) -> bool:
    """Check if path should be ignored based on patterns"""
    rel_path = path.relative_to(project_root)
    path_str = str(rel_path)
    
    for pattern in ignore_patterns:
        if pattern in path_str or path.name == pattern:
            return True
        # Simple glob-like matching for *.extension patterns
        if pattern.startswith('*.') and path.suffix == pattern[1:]:
            return True
    return False

def extract_python_docstring(file_path: Path) -> Optional[str]:
    """Extract module-level docstring from Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Parse AST to get docstring
        tree = ast.parse(content)
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, (ast.Str, ast.Constant))):
            docstring = tree.body[0].value.s if hasattr(tree.body[0].value, 's') else tree.body[0].value.value
            if isinstance(docstring, str):
                # Return first line of docstring
                return docstring.split('\n')[0].strip()
    except Exception:
        pass
    return None

def extract_js_description(file_path: Path) -> Optional[str]:
    """Extract description from JavaScript/TypeScript file comments"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Look for file-level comments at the top
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            line = line.strip()
            if line.startswith('//'):
                desc = line[2:].strip()
                if desc and not desc.startswith('@') and len(desc) > 10:
                    return desc
            elif line.startswith('/*'):
                # Multi-line comment
                comment_lines = []
                for j in range(i, min(i + 10, len(lines))):
                    comment_line = lines[j].strip()
                    if '*/' in comment_line:
                        break
                    if comment_line.startswith('*'):
                        comment_line = comment_line[1:].strip()
                    comment_lines.append(comment_line)
                if comment_lines:
                    desc = ' '.join(comment_lines).strip()
                    if len(desc) > 10:
                        return desc[:100] + '...' if len(desc) > 100 else desc
    except Exception:
        pass
    return None

def extract_readme_description(file_path: Path) -> Optional[str]:
    """Extract description from README files"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Look for first paragraph or line after title
        lines = content.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('![') and len(line) > 20:
                return line[:100] + '...' if len(line) > 100 else line
    except Exception:
        pass
    return None

def get_file_description(file_path: Path) -> Optional[str]:
    """Get description for a file based on its type"""
    suffix = file_path.suffix.lower()
    
    if suffix == '.py':
        return extract_python_docstring(file_path)
    elif suffix in ['.js', '.ts', '.jsx', '.tsx']:
        return extract_js_description(file_path)
    elif file_path.name.lower() in ['readme.md', 'readme.txt', 'readme']:
        return extract_readme_description(file_path)
    elif suffix == '.json' and file_path.name == 'package.json':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('description', '')
        except Exception:
            pass
    
    return None

def build_tree_structure(project_root: Path, include_stats: bool = False) -> Dict[str, Any]:
    """Build hierarchical tree structure with descriptions"""
    ignore_patterns = load_napkin_ignore(project_root)
    tree_data = {
        'name': project_root.name,
        'type': 'directory',
        'path': str(project_root),
        'children': []
    }
    
    def scan_directory(dir_path: Path, parent_node: Dict[str, Any], depth: int = 0) -> None:
        if depth > 10:  # Prevent infinite recursion
            return
        
        try:
            items = []
            for item in dir_path.iterdir():
                if should_ignore_path(item, ignore_patterns, project_root):
                    continue
                items.append(item)
            
            # Sort: directories first, then files alphabetically
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                node = {
                    'name': item.name,
                    'type': 'file' if item.is_file() else 'directory',
                    'path': str(item)
                }
                
                # Add file stats if requested
                if include_stats:
                    try:
                        stat = item.stat()
                        node['size'] = stat.st_size
                        node['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    except Exception:
                        pass
                
                # Get description for files
                if item.is_file():
                    description = get_file_description(item)
                    if description:
                        node['description'] = description
                else:
                    node['children'] = []
                    scan_directory(item, node, depth + 1)
                
                parent_node['children'].append(node)
                
        except PermissionError:
            crud_logger.warning(f"Permission denied accessing {dir_path}")
        except Exception as e:
            crud_logger.error(f"Error scanning {dir_path}: {e}")
    
    scan_directory(project_root, tree_data)
    return tree_data

def format_tree_output(tree_data: Dict[str, Any], indent: str = "") -> List[str]:
    """Format tree data into readable text output"""
    lines = []
    name = tree_data['name']
    description = tree_data.get('description', '')
    
    if tree_data['type'] == 'directory':
        lines.append(f"{indent}📁 {name}/")
    else:
        icon = "📄"
        if name.endswith('.py'):
            icon = "🐍"
        elif name.endswith(('.js', '.ts', '.jsx', '.tsx')):
            icon = "⚡"
        elif name.endswith('.json'):
            icon = "📋"
        elif name.lower().startswith('readme'):
            icon = "📖"
        
        desc_suffix = f" - {description}" if description else ""
        lines.append(f"{indent}{icon} {name}{desc_suffix}")
    
    # Add children for directories
    if 'children' in tree_data and tree_data['children']:
        child_indent = indent + "  "
        for child in tree_data['children']:
            lines.extend(format_tree_output(child, child_indent))
    
    return lines

@mcp.tool()
def napkinwire_project_tree(
    include_stats: bool = False,
    filter_type: Optional[str] = None,
    max_depth: int = 10
) -> Dict[str, Any]:
    """Generate project file tree with extracted documentation and descriptions
    
    Args:
        include_stats: Include file size and modification date
        filter_type: Filter by file type (e.g., 'py', 'js', 'md')
        max_depth: Maximum directory depth to scan
        
    Returns:
        Dict with tree structure and formatted output
    """
    crud_logger.info(f"Generating project tree with stats={include_stats}, filter={filter_type}")
    
    try:
        # Check cache
        global _project_tree_cache, _cache_timestamp
        current_time = time.time()
        cache_key = f"{include_stats}_{filter_type}_{max_depth}"
        
        if (current_time - _cache_timestamp < _cache_duration and 
            cache_key in _project_tree_cache):
            crud_logger.info("Returning cached project tree")
            return _project_tree_cache[cache_key]
        
        # Get project root
        project_root = get_project_root()
        if not project_root.exists():
            return {
                "error": f"Project root does not exist: {project_root}",
                "project_root": str(project_root)
            }
        
        start_time = time.time()
        
        # Build tree structure
        tree_data = build_tree_structure(project_root, include_stats)
        
        # Apply filtering if requested
        if filter_type:
            def filter_tree(node: Dict[str, Any]) -> bool:
                if node['type'] == 'directory':
                    # Keep directories that have matching children
                    if 'children' in node:
                        node['children'] = [child for child in node['children'] if filter_tree(child)]
                        return len(node['children']) > 0
                    return True
                else:
                    # Keep files that match the filter
                    return node['name'].endswith(f'.{filter_type}')
            
            if 'children' in tree_data:
                tree_data['children'] = [child for child in tree_data['children'] if filter_tree(child)]
        
        # Format output
        formatted_lines = format_tree_output(tree_data)
        
        processing_time = round(time.time() - start_time, 2)
        
        result = {
            "project_root": str(project_root),
            "tree_structure": tree_data,
            "formatted_output": "\n".join(formatted_lines),
            "processing_time_seconds": processing_time,
            "total_items": len(formatted_lines),
            "filters_applied": {
                "include_stats": include_stats,
                "filter_type": filter_type,
                "max_depth": max_depth
            }
        }
        
        # Update cache
        _project_tree_cache[cache_key] = result
        _cache_timestamp = current_time
        
        crud_logger.info(f"Successfully generated project tree in {processing_time}s")
        return result
        
    except Exception as e:
        crud_logger.error(f"Error generating project tree: {e}")
        return {
            "error": str(e),
            "project_root": str(get_project_root()),
            "message": "Failed to generate project tree"
        }

# HTTP server diagram editor integration
@mcp.tool()
def napkinwire_spawn_diagram_editor() -> Dict[str, Any]:
    """Spawn local HTTP server for diagram editor and return ASCII diagram data

    Starts HTTP server on localhost, opens browser to diagram.html, waits for POST request
    with ASCII data, returns the diagram representation.

    Returns:
        Dict with diagram data or error message
    """
    crud_logger.info("Starting HTTP server for diagram editor")

    try:
        import socket
        import http.server
        import socketserver
        import threading
        import webbrowser
        import urllib.parse

        # Get project root and web directory path
        project_root = get_project_root()
        web_dir = project_root / "web"

        if not web_dir.exists():
            return {
                "error": f"Web directory not found: {web_dir}",
                "success": False
            }

        diagram_html_path = web_dir / "diagram.html"
        if not diagram_html_path.exists():
            return {
                "error": f"Diagram HTML file not found: {diagram_html_path}",
                "success": False
            }

        # Find available port starting from 8765
        def find_free_port(start_port=8765):
            for port in range(start_port, start_port + 100):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        return port
                except OSError:
                    continue
            raise Exception("No free port found in range 8765-8864")

        port = find_free_port()
        crud_logger.info(f"Using port {port} for HTTP server")

        # Storage for received diagram data
        received_data = {"diagram": None, "error": None, "received": False}

        class DiagramHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(web_dir), **kwargs)

            def do_POST(self):
                if self.path == '/send_to_claude':
                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)

                        # Parse form data or JSON
                        if self.headers.get('Content-Type', '').startswith('application/json'):
                            data = json.loads(post_data.decode('utf-8'))
                            ascii_data = data.get('diagram_data', '')
                        else:
                            # Form data
                            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                            ascii_data = parsed_data.get('diagram_data', [''])[0]

                        if ascii_data:
                            received_data["diagram"] = ascii_data
                            received_data["received"] = True
                            crud_logger.info(f"Received diagram data: {len(ascii_data)} characters")

                            # Send success response
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"error": "No diagram data"}).encode('utf-8'))

                    except Exception as e:
                        crud_logger.error(f"Error handling POST request: {e}")
                        received_data["error"] = str(e)
                        received_data["received"] = True

                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_OPTIONS(self):
                # Handle CORS preflight
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def log_message(self, format, *args):
                # Suppress default server logs to keep output clean
                pass

        # Start HTTP server in background thread
        with socketserver.TCPServer(("localhost", port), DiagramHTTPHandler) as httpd:
            httpd.timeout = 1  # Short timeout for serve_request to allow checking received_data

            server_thread = threading.Thread(target=lambda: httpd.serve_forever())
            server_thread.daemon = True
            server_thread.start()

            crud_logger.info(f"HTTP server started on http://localhost:{port}")

            # Open browser to diagram.html
            diagram_url = f"http://localhost:{port}/diagram.html"
            try:
                webbrowser.open(diagram_url)
                crud_logger.info(f"Opened browser to {diagram_url}")
            except Exception as e:
                crud_logger.warning(f"Failed to open browser automatically: {e}")
                return {
                    "error": f"Server started but failed to open browser. Please go to {diagram_url}",
                    "success": False
                }

            # Wait for data or timeout
            timeout_seconds = 60
            start_time = time.time()

            while not received_data["received"] and (time.time() - start_time) < timeout_seconds:
                time.sleep(0.5)

            # Shutdown server
            httpd.shutdown()
            server_thread.join(timeout=2)

            # Return result
            if received_data["received"]:
                if received_data["diagram"]:
                    crud_logger.info("Successfully received diagram data from HTTP server")
                    return {
                        "success": True,
                        "diagram_data": received_data["diagram"],
                        "method": "http_server"
                    }
                else:
                    crud_logger.error(f"HTTP server error: {received_data['error']}")
                    return {
                        "success": False,
                        "error": received_data["error"] or "Unknown error receiving diagram data"
                    }
            else:
                crud_logger.error("HTTP server timed out waiting for diagram data")
                return {
                    "success": False,
                    "error": "Diagram editor timed out after 60 seconds"
                }

    except Exception as e:
        crud_logger.error(f"Error in HTTP server diagram editor: {e}")
        return {
            "error": str(e),
            "success": False,
            "message": "Failed to start HTTP server for diagram editor"
        }

# Roadmap management tools
def get_roadmap_file_path() -> Path:
    """Get the path to the roadmap.md file"""
    project_root = get_project_root()
    return project_root / "roadmap.md"

def safe_file_operation(file_path: Path, operation: str, content: str = None) -> tuple[bool, str]:
    """Perform file operations with cross-platform locking"""
    try:
        if operation == "read":
            if not file_path.exists():
                return True, ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if fcntl:  # Unix
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                elif msvcrt:  # Windows
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                content = f.read()
                return True, content
        
        elif operation == "append":
            with open(file_path, 'a', encoding='utf-8') as f:
                if fcntl:  # Unix
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                elif msvcrt:  # Windows
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                f.write(content)
                f.flush()
                return True, "Successfully appended"
        
        elif operation == "create":
            with open(file_path, 'w', encoding='utf-8') as f:
                if fcntl:  # Unix
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                elif msvcrt:  # Windows
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                f.write(content)
                f.flush()
                return True, "Successfully created"
                
    except Exception as e:
        crud_logger.error(f"Error in file operation {operation}: {e}")
        return False, str(e)
    
    return False, "Unknown operation"

def create_initial_roadmap(file_path: Path) -> bool:
    """Create initial roadmap.md file with header"""
    initial_content = """# NapkinWire Roadmap

Ideas and plans for the NapkinWire project, organized by priority and timeline.

## Now
*Current active work*

## Next
*Coming up in the next sprint/iteration*

## Soon
*Planned for the near future*

## Later
*Future possibilities*

## Ideas
*Brain dumps and possibilities to explore*

---

"""
    success, message = safe_file_operation(file_path, "create", initial_content)
    if success:
        crud_logger.info(f"Created initial roadmap file: {file_path}")
    else:
        crud_logger.error(f"Failed to create initial roadmap: {message}")
    return success

@mcp.tool()
def napkinwire_append_roadmap_idea(
    title: str,
    description: str,
    category: str = "ideas"
) -> Dict[str, Any]:
    """Append a new idea to the roadmap.md file
    
    Args:
        title: Title of the idea
        description: Description of the idea
        category: Category (now, next, soon, later, ideas)
    
    Returns:
        Dict with success status and message
    """
    crud_logger.info(f"Appending roadmap idea: '{title}' in category '{category}'")
    
    try:
        # Validate category
        valid_categories = ["now", "next", "soon", "later", "ideas"]
        if category not in valid_categories:
            return {
                "success": False,
                "error": f"Invalid category '{category}'. Must be one of: {valid_categories}"
            }
        
        # Get roadmap file path
        roadmap_path = get_roadmap_file_path()
        
        # Create file if it doesn't exist
        if not roadmap_path.exists():
            if not create_initial_roadmap(roadmap_path):
                return {
                    "success": False,
                    "error": "Failed to create initial roadmap file"
                }
        
        # Create timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        # Format the new idea entry
        new_entry = f"""
## [{category.title()}] {title}
*Added: {timestamp}*
{description}
---
"""
        
        # Append to file
        success, message = safe_file_operation(roadmap_path, "append", new_entry)
        
        if success:
            crud_logger.info(f"Successfully appended idea '{title}' to roadmap")
            return {
                "success": True,
                "message": f"Added idea '{title}' to {category} section",
                "file_path": str(roadmap_path)
            }
        else:
            crud_logger.error(f"Failed to append idea '{title}': {message}")
            return {
                "success": False,
                "error": f"Failed to write to roadmap file: {message}"
            }
            
    except Exception as e:
        crud_logger.error(f"Exception appending roadmap idea '{title}': {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def napkinwire_list_roadmap_ideas(category: Optional[str] = None) -> Dict[str, Any]:
    """List roadmap ideas with optional category filter
    
    Args:
        category: Optional category filter (now, next, soon, later, ideas)
    
    Returns:
        Dict with formatted roadmap content and statistics
    """
    crud_logger.info(f"Listing roadmap ideas with category filter: '{category}'")
    
    try:
        # Validate category if provided
        valid_categories = ["now", "next", "soon", "later", "ideas"]
        if category and category not in valid_categories:
            return {
                "success": False,
                "error": f"Invalid category '{category}'. Must be one of: {valid_categories}"
            }
        
        # Get roadmap file path
        roadmap_path = get_roadmap_file_path()
        
        # Read file content
        success, content = safe_file_operation(roadmap_path, "read")
        
        if not success:
            return {
                "success": False,
                "error": f"Failed to read roadmap file: {content}",
                "file_path": str(roadmap_path)
            }
        
        if not content.strip():
            return {
                "success": True,
                "content": "Roadmap file is empty or doesn't exist yet.",
                "idea_count": 0,
                "file_path": str(roadmap_path)
            }
        
        # Apply category filter if specified
        if category:
            lines = content.split('\n')
            filtered_lines = []
            in_target_category = False
            
            for line in lines:
                # Check if this is a category header
                if line.strip().startswith(f'## [{category.title()}]'):
                    in_target_category = True
                    filtered_lines.append(line)
                elif line.strip().startswith('## [') and not line.strip().startswith(f'## [{category.title()}]'):
                    in_target_category = False
                elif in_target_category:
                    filtered_lines.append(line)
                elif not line.strip().startswith('## ['):
                    # Include non-category lines (headers, etc.)
                    filtered_lines.append(line)
            
            content = '\n'.join(filtered_lines)
        
        # Count ideas (entries starting with ## [)
        idea_count = len([line for line in content.split('\n') if line.strip().startswith('## [')])
        
        crud_logger.info(f"Successfully listed {idea_count} roadmap ideas")
        return {
            "success": True,
            "content": content,
            "idea_count": idea_count,
            "category_filter": category,
            "file_path": str(roadmap_path)
        }
        
    except Exception as e:
        crud_logger.error(f"Exception listing roadmap ideas: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": str(get_roadmap_file_path())
        }

# UI mockup editor HTTP server integration
@mcp.tool()
def napkinwire_spawn_ui_mockup_editor() -> Dict[str, Any]:
    """Spawn local HTTP server for UI mockup editor and return ASCII mockup data

    Starts HTTP server on localhost, opens browser to ui.html, waits for POST request
    with ASCII data, returns the UI mockup representation.

    Returns:
        Dict with UI mockup data or error message
    """
    crud_logger.info("Starting HTTP server for UI mockup editor")

    try:
        import socket
        import http.server
        import socketserver
        import threading
        import webbrowser
        import urllib.parse

        # Get project root and web directory path
        project_root = get_project_root()
        web_dir = project_root / "web"

        if not web_dir.exists():
            return {
                "error": f"Web directory not found: {web_dir}",
                "success": False
            }

        ui_html_path = web_dir / "ui.html"
        if not ui_html_path.exists():
            return {
                "error": f"UI HTML file not found: {ui_html_path}",
                "success": False
            }

        # Find available port starting from 8766
        def find_free_port(start_port=8766):
            for port in range(start_port, start_port + 100):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        return port
                except OSError:
                    continue
            raise Exception("No free port found in range 8766-8865")

        port = find_free_port()
        crud_logger.info(f"Using port {port} for UI mockup HTTP server")

        # Storage for received UI mockup data
        received_data = {"ui_mockup": None, "error": None, "received": False}

        class UIMockupHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(web_dir), **kwargs)

            def do_POST(self):
                if self.path == '/send_to_claude':
                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)

                        # Parse form data or JSON
                        if self.headers.get('Content-Type', '').startswith('application/json'):
                            data = json.loads(post_data.decode('utf-8'))
                            ascii_data = data.get('ui_mockup_data', '')
                        else:
                            # Form data
                            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                            ascii_data = parsed_data.get('ui_mockup_data', [''])[0]

                        if ascii_data:
                            received_data["ui_mockup"] = ascii_data
                            received_data["received"] = True
                            crud_logger.info(f"Received UI mockup data: {len(ascii_data)} characters")

                            # Send success response
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"error": "No UI mockup data"}).encode('utf-8'))

                    except Exception as e:
                        crud_logger.error(f"Error handling POST request: {e}")
                        received_data["error"] = str(e)
                        received_data["received"] = True

                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_OPTIONS(self):
                # Handle CORS preflight
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def log_message(self, format, *args):
                # Suppress default server logs to keep output clean
                pass

        # Start HTTP server in background thread
        with socketserver.TCPServer(("localhost", port), UIMockupHTTPHandler) as httpd:
            httpd.timeout = 1  # Short timeout for serve_request to allow checking received_data

            server_thread = threading.Thread(target=lambda: httpd.serve_forever())
            server_thread.daemon = True
            server_thread.start()

            crud_logger.info(f"HTTP server started on http://localhost:{port}")

            # Open browser to ui.html
            ui_url = f"http://localhost:{port}/ui.html"
            try:
                webbrowser.open(ui_url)
                crud_logger.info(f"Opened browser to {ui_url}")
            except Exception as e:
                crud_logger.warning(f"Failed to open browser automatically: {e}")
                return {
                    "error": f"Server started but failed to open browser. Please go to {ui_url}",
                    "success": False
                }

            # Wait for data or timeout
            timeout_seconds = 60
            start_time = time.time()

            while not received_data["received"] and (time.time() - start_time) < timeout_seconds:
                time.sleep(0.5)

            # Shutdown server
            httpd.shutdown()
            server_thread.join(timeout=2)

            # Return result
            if received_data["received"]:
                if received_data["ui_mockup"]:
                    crud_logger.info("Successfully received UI mockup data from HTTP server")
                    return {
                        "success": True,
                        "ui_mockup_data": received_data["ui_mockup"],
                        "method": "http_server"
                    }
                else:
                    crud_logger.error(f"HTTP server error: {received_data['error']}")
                    return {
                        "success": False,
                        "error": received_data["error"] or "Unknown error receiving UI mockup data"
                    }
            else:
                crud_logger.error("HTTP server timed out waiting for UI mockup data")
                return {
                    "success": False,
                    "error": "UI mockup editor timed out after 60 seconds"
                }

    except Exception as e:
        crud_logger.error(f"Error in HTTP server UI mockup editor: {e}")
        return {
            "error": str(e),
            "success": False,
            "message": "Failed to start HTTP server for UI mockup editor"
        }

# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."
