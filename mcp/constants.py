JSON_FORMAT = """
{
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2025-01-09T10:30:00Z",
    "next_id": 4,
    "project": "napkinwire"
  },
  "tickets": [
    {
      "id": "TICKET-001",
      "title": "Create MCP tool for real-time project context",
      "status": "todo",
      "priority": "high",
      "created_at": "2025-01-09T10:00:00Z",
      "updated_at": "2025-01-09T10:00:00Z",
      "description": "Build tool that returns intelligent file tree structure, ignoring common build artifacts",
      "requirements": [
        "Skip venv, __pycache__, node_modules, .git objects",
        "Show tree structure with recent changes",
        "Include file sizes and last modified times",
        "Return as formatted string the AI can parse"
      ],
      "acceptance_criteria": [
        "Tool returns clean tree structure",
        "Respects .napkinignore patterns",
        "Performance: <1s for typical projects"
      ],
      "files_affected": [
        "main.py"
      ],
      "dependencies": [],
      "outcome": null,
      "notes": null
    },
    {
      "id": "TICKET-002", 
      "title": "Implement ticket CRUD operations",
      "status": "todo",
      "priority": "high",
      "created_at": "2025-01-09T10:05:00Z",
      "updated_at": "2025-01-09T10:05:00Z",
      "description": "Create MCP tools for ticket management operations",
      "requirements": [
        "create_ticket tool with validation",
        "list_tickets with status filtering",
        "update_ticket_status tool",
        "get_ticket_details for implementation"
      ],
      "acceptance_criteria": [
        "All CRUD operations work",
        "Ticket IDs auto-increment",
        "File stays valid JSON after updates"
      ],
      "files_affected": [
        "main.py",
        "tickets.json"
      ],
      "dependencies": [],
      "outcome": null,
      "notes": null
    },
    {
      "id": "TICKET-003",
      "title": "Add ticket outcome tracking",
      "status": "todo",
      "priority": "medium",
      "created_at": "2025-01-09T10:10:00Z",
      "updated_at": "2025-01-09T10:10:00Z",
      "description": "Tool to record what happened when ticket was implemented",
      "requirements": [
        "Record success/fail/partial status",
        "Log what was learned or what broke",
        "Support for generating follow-up tickets",
        "Build patterns library over time"
      ],
      "acceptance_criteria": [
        "Outcomes are persisted",
        "Can query outcomes by status",
        "Follow-up tickets reference parent"
      ],
      "files_affected": [
        "main.py",
        "tickets.json"
      ],
      "dependencies": ["TICKET-002"],
      "outcome": null,
      "notes": null
    }
  ],
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

"""
