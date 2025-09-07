from mcp.server.fastmcp import FastMCP
from constants import JSON_FORMAT

import signal
import sys
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


def cleanup(signum, frame):
    # Clean up resources
    print("Shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)


# Create an MCP server
mcp = FastMCP("NapkinWire")

# Helper functions for ticket management
def get_tickets_file_path() -> str:
    """Get the path to the tickets.json file"""
    project_path = os.getenv("NAPKINWIRE_PROJECT", ".")
    return os.path.join(project_path, "tickets.json")

def load_tickets_data() -> Dict[str, Any]:
    """Load tickets data from JSON file or create default structure"""
    file_path = get_tickets_file_path()
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default structure if file doesn't exist
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
        print(f"Error loading tickets file: {e}")
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
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Replace original file
        os.replace(temp_path, file_path)
        return True
    except (IOError, OSError) as e:
        print(f"Error saving tickets file: {e}")
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
    try:
        # Validate priority
        valid_priorities = ["high", "medium", "low"]
        if priority not in valid_priorities:
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
            print(f"Created ticket {ticket_id}: {title}")
            return {"success": True, "ticket_id": ticket_id}
        else:
            return {"success": False, "error": "Failed to save ticket data"}
            
    except Exception as e:
        print(f"Error creating ticket: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def napkinwire_list_tickets(status: str = "all") -> List[Dict[str, Any]]:
    """List tickets with optional status filter, sorted by priority then created_at"""
    try:
        # Validate status
        valid_statuses = ["todo", "in_progress", "done", "blocked", "all"]
        if status not in valid_statuses:
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
        
        print(f"Listed {len(result)} tickets with status filter: {status}")
        return result
        
    except Exception as e:
        print(f"Error listing tickets: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def napkinwire_update_ticket_status(ticket_id: str, new_status: str) -> Dict[str, Any]:
    """Update the status of an existing ticket"""
    try:
        # Validate status
        valid_statuses = ["todo", "in_progress", "done", "blocked"]
        if new_status not in valid_statuses:
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
                    print(f"Updated {ticket_id} from {old_status} to {new_status}")
                    return {
                        "success": True,
                        "message": f"Updated {ticket_id} to {new_status}"
                    }
                else:
                    return {"success": False, "error": "Failed to save ticket data"}
        
        if not ticket_found:
            return {"success": False, "error": f"Ticket {ticket_id} not found"}
            
    except Exception as e:
        print(f"Error updating ticket status: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def napkinwire_get_ticket_details(ticket_id: str) -> Dict[str, Any]:
    """Get full details of a specific ticket for implementation"""
    try:
        # Load data
        data = load_tickets_data()
        tickets = data.get("tickets", [])
        
        # Find the ticket
        for ticket in tickets:
            if ticket.get("id") == ticket_id:
                print(f"Retrieved details for {ticket_id}")
                return ticket
        
        # Ticket not found
        return {"error": f"Ticket {ticket_id} not found"}
        
    except Exception as e:
        print(f"Error getting ticket details: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_ticket_format() -> str:
    """Get the ticket format from the resource"""
    print("Called fetch ticketing format")
    
    
    return "Ticket format example:\n" +JSON_FORMAT


@mcp.resource("file://tickets/format.json")
def get_ticketing_format():
    
    """ Sample resource """
   
    return "Reference format for project tickets" + JSON_FORMAT


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
