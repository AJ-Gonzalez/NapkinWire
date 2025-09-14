import os
import yaml
from pathlib import Path
from local_config import TICKETS, OPEN_ROUTER_KEY

TICKETS = TICKETS
OPEN_ROUTER_KEY = OPEN_ROUTER_KEY

# Always load config from the same directory as this config.py file
CONFIG_DIR = Path(__file__).parent
CONFIG_PATH = CONFIG_DIR / "config.yaml"

def load_config():
    """Load YAML configuration with fallback defaults"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        # Fallback configuration if YAML file is missing or invalid
        return {
            'is_prod': False,
            'production': ['napkinwire_spawn_diagram_editor', 'napkinwire_spawn_ui_mockup_editor'],
            'development': [
                'add', 'napkinwire_create_ticket', 'napkinwire_list_tickets',
                'napkinwire_update_ticket_status', 'napkinwire_get_ticket_details',
                'napkinwire_claude_usage_analysis', 'napkinwire_project_tree',
                'napkinwire_append_roadmap_idea', 'napkinwire_list_roadmap_ideas'
            ]
        }

def get_enabled_tools():
    """Get list of enabled tools based on configuration"""
    config = load_config()
    is_prod = config.get('is_prod', False)

    if is_prod:
        # Production mode: only production tools
        return config.get('production', [])
    else:
        # Development mode: all tools (production + development)
        prod_tools = config.get('production', [])
        dev_tools = config.get('development', [])
        return prod_tools + dev_tools

