import json
import os
import logging
from pathlib import Path
from config import TICKETS
from datetime import datetime
from typing import List, Dict, Any

# Configure logging for CRUD operations
crud_logger = logging.getLogger('napkinwire_crud')

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