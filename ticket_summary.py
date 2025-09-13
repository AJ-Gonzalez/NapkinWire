#!/usr/bin/env python3
"""
Ticket Summary Tool
Reads tickets.json and outputs a formatted summary grouped by status and priority.
"""

import json
import sys
from collections import defaultdict


def load_tickets(file_path="tickets.json"):
    """Load tickets from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('tickets', [])
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing {file_path}: {e}")
        sys.exit(1)


def group_tickets_by_status(tickets):
    """Group tickets by status and sort by priority within each group."""
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    grouped = defaultdict(list)

    for ticket in tickets:
        status = ticket.get('status', 'unknown')
        grouped[status].append(ticket)

    # Sort each group by priority
    for status in grouped:
        grouped[status].sort(key=lambda t: priority_order.get(t.get('priority', 'low'), 3))

    return dict(grouped)


def format_ticket_line(ticket):
    """Format a single ticket line."""
    ticket_id = ticket.get('id', 'NO-ID')
    title = ticket.get('title', 'No title')
    priority = ticket.get('priority', 'unknown').upper()

    # Truncate long titles
    if len(title) > 70:
        title = title[:67] + "..."

    return f"  {ticket_id} [{priority:6}] {title}"


def print_section(status, tickets, color_code=""):
    """Print a section for tickets with given status."""
    status_display = status.replace('_', ' ').title()
    count = len(tickets)

    print(f"\n{color_code}{'='*60}")
    print(f"{status_display.upper()} ({count} tickets)")
    print(f"{'='*60}\033[0m")

    if not tickets:
        print("  No tickets")
        return

    for ticket in tickets:
        print(format_ticket_line(ticket))


def print_summary_counts(grouped_tickets):
    """Print summary counts at the top."""
    total = sum(len(tickets) for tickets in grouped_tickets.values())

    print("\033[1m" + "="*60)
    print("NAPKINWIRE TICKET SUMMARY")
    print("="*60 + "\033[0m")

    print(f"\nTotal Tickets: {total}")

    for status in ['todo', 'in_progress', 'done', 'blocked']:
        count = len(grouped_tickets.get(status, []))
        if count > 0:
            print(f"  {status.replace('_', ' ').title()}: {count}")


def main():
    """Main function to generate ticket summary."""
    tickets = load_tickets()
    grouped = group_tickets_by_status(tickets)

    print_summary_counts(grouped)

    # Define colors for different statuses
    colors = {
        'blocked': '\033[91m',     # Red
        'in_progress': '\033[93m', # Yellow
        'todo': '\033[94m',        # Blue
        'done': '\033[92m'         # Green
    }

    # Print sections in priority order
    status_order = ['blocked', 'in_progress', 'todo', 'done']

    for status in status_order:
        if status in grouped:
            color = colors.get(status, "")
            print_section(status, grouped[status], color)

    # Print any other statuses not in the main order
    for status in grouped:
        if status not in status_order:
            print_section(status, grouped[status])

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()