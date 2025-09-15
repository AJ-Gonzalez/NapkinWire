import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import TICKETS

# Configure logging
crud_logger = logging.getLogger('napkinwire_crud')

def estimate_tokens(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 characters"""
    return len(text) // 4

def get_project_root() -> Path:
    """Get project root from TICKETS file path directory"""
    tickets_path = Path(TICKETS)
    return tickets_path.parent

def load_tickets() -> Dict[str, Any]:
    """Load tickets from tickets.json"""
    try:
        tickets_path = Path(TICKETS)
        if tickets_path.exists():
            with open(tickets_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"tickets": []}
    except Exception as e:
        crud_logger.error(f"Error loading tickets: {e}")
        return {"tickets": []}

def get_active_tickets(max_count: int = 3) -> List[Dict[str, Any]]:
    """Get active high-priority todo tickets"""
    tickets_data = load_tickets()
    active_tickets = []

    for ticket in tickets_data.get("tickets", []):
        if ticket.get("status") == "todo" and ticket.get("priority") == "high":
            active_tickets.append({
                "id": ticket.get("id"),
                "title": ticket.get("title"),
                "priority": ticket.get("priority")
            })

    # Sort by created_at and return most recent
    active_tickets.sort(key=lambda x: x.get("id", ""), reverse=True)
    return active_tickets[:max_count]

def get_recent_completed(max_count: int = 3) -> List[Dict[str, Any]]:
    """Get recently completed tickets"""
    tickets_data = load_tickets()
    completed_tickets = []

    for ticket in tickets_data.get("tickets", []):
        if ticket.get("status") == "done":
            completed_tickets.append({
                "id": ticket.get("id"),
                "title": ticket.get("title"),
                "updated_at": ticket.get("updated_at")
            })

    # Sort by updated_at and return most recent
    completed_tickets.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return completed_tickets[:max_count]

def get_ticket_stats() -> Dict[str, int]:
    """Get ticket statistics"""
    tickets_data = load_tickets()
    stats = {"todo": 0, "done": 0, "in_progress": 0, "blocked": 0, "cancelled": 0, "obsolete": 0}

    for ticket in tickets_data.get("tickets", []):
        status = ticket.get("status", "unknown")
        if status in stats:
            stats[status] += 1

    return stats

def get_roadmap_items(max_count: int = 3) -> List[str]:
    """Get roadmap items from roadmap.md"""
    try:
        project_root = get_project_root()
        roadmap_path = project_root / "roadmap.md"

        if not roadmap_path.exists():
            return []

        content = roadmap_path.read_text(encoding='utf-8')
        items = []

        # Extract items from Next and Soon sections
        lines = content.split('\n')
        in_next_or_soon = False

        for line in lines:
            if line.startswith('## Next') or line.startswith('## Soon'):
                in_next_or_soon = True
                continue
            elif line.startswith('## ') and in_next_or_soon:
                break
            elif in_next_or_soon and line.strip().startswith('-'):
                item = line.strip()[1:].strip()
                if item:
                    items.append(item)

        return items[:max_count]
    except Exception as e:
        crud_logger.error(f"Error reading roadmap: {e}")
        return []

def get_claude_md_info() -> str:
    """Get key information from CLAUDE.md"""
    try:
        project_root = get_project_root()
        claude_md_path = project_root / "CLAUDE.md"

        if not claude_md_path.exists():
            return "No CLAUDE.md found"

        content = claude_md_path.read_text(encoding='utf-8')

        # Extract key principles or first few lines
        lines = content.split('\n')
        key_info = []

        for line in lines[:10]:  # First 10 lines for key info
            if line.strip() and not line.startswith('#'):
                key_info.append(line.strip())
                if len(key_info) >= 3:  # Limit to 3 key points
                    break

        return "; ".join(key_info) if key_info else "CLAUDE.md exists but no key info extracted"
    except Exception as e:
        crud_logger.error(f"Error reading CLAUDE.md: {e}")
        return "Error reading CLAUDE.md"

def get_recent_decisions(max_count: int = 3) -> List[str]:
    """Get recent decisions from decisions.json (placeholder for future implementation)"""
    # For now, return some key architectural decisions from the codebase
    return [
        "Use HTTP server instead of PyWebView for diagram editor",
        "Refactor main.py into modules for maintainability",
        "Use YAML config with tool filtering for prod/dev modes"
    ][:max_count]

def get_mission_summary() -> str:
    """Get mission summary from mission.md (placeholder for future implementation)"""
    try:
        project_root = get_project_root()
        mission_path = project_root / "mission.md"

        if not mission_path.exists():
            return "NapkinWire: Visual diagram and UI mockup tools for Claude"

        content = mission_path.read_text(encoding='utf-8')
        # Get first non-header line as mission summary
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                return line.strip()

        return "NapkinWire: Visual diagram and UI mockup tools for Claude"
    except Exception as e:
        crud_logger.error(f"Error reading mission.md: {e}")
        return "NapkinWire: Visual diagram and UI mockup tools for Claude"

def build_context_summary(max_tokens: int = 1000) -> str:
    """Build layered context summary based on token budget"""
    summary = ""
    token_count = 0

    # LAYER 1: Critical (always include, ~200 tokens)
    mission = get_mission_summary()
    active_tickets = get_active_tickets(max=3)
    active_list = [f"{t['id']}: {t['title']}" for t in active_tickets]

    critical = f"""=== NAPKINWIRE CONTEXT ===
📍 MISSION: {mission}
🎯 CURRENT: {len(active_tickets)} active high-priority tickets
⚡ ACTIVE: {', '.join(active_list[:2]) if active_list else 'No active tickets'}"""

    summary += critical
    token_count += estimate_tokens(critical)

    # LAYER 2: Helpful (if budget allows, ~300 tokens)
    if token_count < max_tokens - 300:
        recent_decisions = get_recent_decisions(max=3)
        recent_completed = get_recent_completed(max=3)
        completed_list = [f"{t['id']}: {t['title']}" for t in recent_completed]

        helpful = f"""

📌 DECISIONS: {'; '.join(recent_decisions)}
✅ COMPLETED: {'; '.join(completed_list[:3])}"""

        summary += helpful
        token_count += estimate_tokens(helpful)

    # LAYER 3: Detailed (if budget allows, ~500 tokens)
    if token_count < max_tokens - 500:
        stats = get_ticket_stats()
        roadmap_items = get_roadmap_items(max=3)

        detailed = f"""

🔧 STATS: {stats['done']} done, {stats['todo']} todo, {stats['in_progress']} in progress
📋 ROADMAP: {'; '.join(roadmap_items) if roadmap_items else 'No roadmap items'}"""

        summary += detailed
        token_count += estimate_tokens(detailed)

    # LAYER 4: Full context (if budget allows)
    if token_count < max_tokens - 800:
        claude_info = get_claude_md_info()

        full = f"""

📖 GUIDELINES: {claude_info}
💻 PROJECT: NapkinWire MCP Tools - Visual diagram and UI mockup generation"""

        summary += full
        token_count += estimate_tokens(full)

    return summary

def napkinwire_context_restore(max_tokens: int = 1000) -> Dict[str, Any]:
    """Restore essential project context with token budget

    Args:
        max_tokens: Maximum tokens for context (default 1000)
            - 500: Bare minimum (current task + active tickets)
            - 1000: Standard (+ recent decisions + completions)
            - 2000: Detailed (+ roadmap + project stats)
            - 5000: Full (+ guidelines + project info)
    """
    crud_logger.info(f"Building context restore with max_tokens: {max_tokens}")

    try:
        context_summary = build_context_summary(max_tokens)
        estimated_tokens = estimate_tokens(context_summary)

        return {
            "success": True,
            "context": context_summary,
            "estimated_tokens": estimated_tokens,
            "max_tokens": max_tokens,
            "detail_level": "layered_based_on_budget"
        }

    except Exception as e:
        crud_logger.error(f"Error building context restore: {e}")
        return {
            "success": False,
            "error": str(e),
            "context": "Failed to restore project context"
        }