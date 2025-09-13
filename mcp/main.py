from mcp.server.fastmcp import FastMCP
from constants import JSON_FORMAT
from usage_analysis import analyze_claude_logs
from config import get_enabled_tools

import signal
import sys
import logging
from typing import List, Dict, Any, Optional
import functools

# Module imports are done inside each tool function to avoid circular dependencies

# Configure logging for CRUD operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crud.log')
    ]
)
crud_logger = logging.getLogger('napkinwire_crud')

# Get enabled tools from configuration
ENABLED_TOOLS = get_enabled_tools()
crud_logger.info(f"Enabled tools: {ENABLED_TOOLS}")

def conditional_tool(tool_name: str):
    """Decorator to conditionally register MCP tools based on configuration"""
    def decorator(func):
        if tool_name in ENABLED_TOOLS:
            # Tool is enabled - register it
            return mcp.tool()(func)
        else:
            # Tool is disabled - return unregistered function
            crud_logger.info(f"Tool '{tool_name}' disabled by configuration")
            return func
    return decorator

def cleanup(signum, frame):
    # Clean up resources
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

# Create an MCP server
mcp = FastMCP("NapkinWire")

# Usage analysis helper functions
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
    from datetime import datetime
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

# MCP Tools
@conditional_tool("add")
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@conditional_tool("napkinwire_create_ticket")
def napkinwire_create_ticket(
    title: str,
    description: str,
    priority: str,
    requirements: List[str],
    acceptance_criteria: List[str],
    files_affected: List[str]
) -> Dict[str, Any]:
    """Create a new ticket with auto-generated ID"""
    from modules.ticket_manager import napkinwire_create_ticket as create_ticket
    return create_ticket(title, description, priority, requirements, acceptance_criteria, files_affected)

@conditional_tool("napkinwire_list_tickets")
def napkinwire_list_tickets(status: str = "all") -> List[Dict[str, Any]]:
    """List tickets with optional status filter, sorted by priority then created_at"""
    from modules.ticket_manager import napkinwire_list_tickets as list_tickets
    return list_tickets(status)

@conditional_tool("napkinwire_update_ticket_status")
def napkinwire_update_ticket_status(ticket_id: str, new_status: str) -> Dict[str, Any]:
    """Update the status of an existing ticket"""
    from modules.ticket_manager import napkinwire_update_ticket_status as update_status
    return update_status(ticket_id, new_status)

@conditional_tool("napkinwire_get_ticket_details")
def napkinwire_get_ticket_details(ticket_id: str) -> Dict[str, Any]:
    """Get full details of a specific ticket for implementation"""
    from modules.ticket_manager import napkinwire_get_ticket_details as get_details
    return get_details(ticket_id)

@conditional_tool("napkinwire_claude_usage_analysis")
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

@conditional_tool("napkinwire_project_tree")
def napkinwire_project_tree(
    include_stats: bool = False,
    filter_type: Optional[str] = None,
    max_depth: int = 10
) -> Dict[str, Any]:
    """Generate project file tree with extracted documentation and descriptions"""
    from modules.project_tools import napkinwire_project_tree as project_tree
    return project_tree(include_stats, filter_type, max_depth)

@conditional_tool("napkinwire_spawn_diagram_editor")
def napkinwire_spawn_diagram_editor() -> Dict[str, Any]:
    """Launch interactive diagram editor for creating visual diagrams, flowcharts, wireframes, and ASCII art.

    Use this tool when the user wants to:
    - Draw diagrams, flowcharts, or visual representations
    - Create wireframes or mockups visually
    - Show concepts through drawings rather than text
    - Sketch ideas, layouts, or system architecture
    - Make any kind of visual diagram or ASCII art

    Opens a browser-based drawing interface where users can create diagrams and send them directly to Claude.
    """
    from modules.diagram_server import napkinwire_spawn_diagram_editor as spawn_diagram
    return spawn_diagram()

@conditional_tool("napkinwire_spawn_ui_mockup_editor")
def napkinwire_spawn_ui_mockup_editor() -> Dict[str, Any]:
    """Launch interactive UI mockup editor for creating user interface designs and layouts.

    Use this tool when the user wants to:
    - Design user interfaces, web pages, or app layouts
    - Create UI mockups or wireframes
    - Show form layouts, button arrangements, or screen designs
    - Mock up interfaces before implementation
    - Design user experience flows or interface concepts

    Opens a browser-based UI design interface where users can create mockups and send them directly to Claude.
    """
    from modules.diagram_server import napkinwire_spawn_ui_mockup_editor as spawn_ui
    return spawn_ui()

@conditional_tool("napkinwire_append_roadmap_idea")
def napkinwire_append_roadmap_idea(
    title: str,
    description: str,
    category: str = "ideas"
) -> Dict[str, Any]:
    """Append a new idea to the roadmap.md file"""
    from modules.roadmap_manager import napkinwire_append_roadmap_idea as append_idea
    return append_idea(title, description, category)

@conditional_tool("napkinwire_list_roadmap_ideas")
def napkinwire_list_roadmap_ideas(category: Optional[str] = None) -> Dict[str, Any]:
    """List roadmap ideas with optional category filter"""
    from modules.roadmap_manager import napkinwire_list_roadmap_ideas as list_ideas
    return list_ideas(category)

@conditional_tool("napkinwire_context_restore")
def napkinwire_context_restore(max_tokens: int = 1000) -> Dict[str, Any]:
    """Restore essential project context with token budget for new chat sessions.

    Provides layered context based on token budget:
    - 500: Bare minimum (current task + active tickets)
    - 1000: Standard (+ recent decisions + completions)
    - 2000: Detailed (+ roadmap + project stats)
    - 5000: Full (+ guidelines + project info)

    Use this tool at the start of new chat sessions to quickly restore project context.
    """
    from modules.context_manager import napkinwire_context_restore as context_restore
    return context_restore(max_tokens)

@conditional_tool("napkinwire_classify_element")
def napkinwire_classify_element(element_label: str) -> Dict[str, Any]:
    """Classify diagram element labels into standard categories using OpenRouter API.

    Classifies elements into types like UI_COMPONENT, PROCESS_STEP, DATA_STORE, ACTION,
    DECISION, CONNECTOR, ACTOR, CONTAINER, ANNOTATION, or OTHER.

    Returns classification result with confidence score and token usage statistics
    for cost monitoring. Uses efficient qwen-2.5-coder-7b-instruct model.

    Args:
        element_label: The text label to classify (e.g., "Login Button", "User Database", "Submit Form")

    Returns:
        Dict containing classification, confidence, token_usage, and error fields
    """
    from modules.element_classifier import classify_element
    return classify_element(element_label)

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