"""
Aider integration for automated ticket implementation using OpenRouter free models.
This module provides functions to execute Aider with ticket requirements.
"""

import subprocess
import os
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Configure logging
logger = logging.getLogger('aider_integration')

def run_aider_on_ticket(ticket_id: str, ticket_description: str, requirements: List[str]) -> Tuple[str, int]:
    """Execute Aider with ticket requirements as prompt

    Args:
        ticket_id: The ticket identifier (e.g., "TICKET-023")
        ticket_description: Brief description of what needs to be implemented
        requirements: List of specific requirements from the ticket

    Returns:
        Tuple of (output_string, return_code)
    """
    # Build the prompt from ticket information
    prompt = f"""Implement {ticket_id}: {ticket_description}

Requirements:
""" + '\n'.join(f"- {req}" for req in requirements)

    # Basic aider command
    cmd = ['aider', '--message', prompt, '--yes']

    logger.info(f"Running Aider for {ticket_id}")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=get_project_root(),
            timeout=300  # 5 minute timeout
        )

        logger.info(f"Aider completed with return code: {result.returncode}")
        if result.returncode != 0:
            logger.error(f"Aider stderr: {result.stderr}")

        return result.stdout, result.returncode

    except subprocess.TimeoutExpired:
        logger.error(f"Aider timed out after 5 minutes for {ticket_id}")
        return "ERROR: Aider execution timed out", 1

    except Exception as e:
        logger.error(f"Error running Aider: {e}")
        return f"ERROR: Failed to run Aider - {str(e)}", 1

def run_aider_with_files(message: str, files: List[str] = None) -> Tuple[str, int]:
    """Run Aider with a specific message and optional file list

    Args:
        message: The instruction/prompt for Aider
        files: Optional list of specific files to work on

    Returns:
        Tuple of (output_string, return_code)
    """
    cmd = ['aider', '--message', message, '--yes']

    if files:
        cmd.extend(files)

    logger.info(f"Running Aider with message: {message[:50]}...")
    logger.debug(f"Files: {files if files else 'all tracked files'}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=get_project_root(),
            timeout=300
        )

        return result.stdout, result.returncode

    except Exception as e:
        logger.error(f"Error running Aider: {e}")
        return f"ERROR: {str(e)}", 1

def check_aider_setup() -> Dict[str, Any]:
    """Check if Aider is properly configured and can connect to OpenRouter

    Returns:
        Dict with setup status and details
    """
    result = {
        "aider_installed": False,
        "config_exists": False,
        "openrouter_key_set": False,
        "errors": []
    }

    # Check if aider command is available
    try:
        subprocess.run(['aider', '--version'], capture_output=True, timeout=10)
        result["aider_installed"] = True
    except Exception as e:
        result["errors"].append(f"Aider not installed or not in PATH: {e}")

    # Check if config file exists
    config_path = get_project_root() / ".aider.conf.yml"
    if config_path.exists():
        result["config_exists"] = True
    else:
        result["errors"].append("Config file .aider.conf.yml not found")

    # Check if OpenRouter API key is set
    if os.getenv('OPENROUTER_API_KEY'):
        result["openrouter_key_set"] = True
    else:
        result["errors"].append("OPENROUTER_API_KEY environment variable not set")

    result["ready"] = all([
        result["aider_installed"],
        result["config_exists"],
        result["openrouter_key_set"]
    ])

    return result

def get_project_root() -> Path:
    """Get the project root directory"""
    # Find project root by looking for .git directory
    current = Path.cwd()
    while current.parent != current:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Fallback to current directory
    return Path.cwd()

def test_aider_connection() -> Dict[str, Any]:
    """Test Aider connection with a simple task

    Returns:
        Dict with test results
    """
    test_message = "Add a comment '# Aider test successful' to the add function in main.py"

    logger.info("Testing Aider connection...")

    try:
        output, return_code = run_aider_with_files(test_message)

        return {
            "success": return_code == 0,
            "output": output,
            "return_code": return_code,
            "message": "Aider connection test completed"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Aider connection test failed"
        }

if __name__ == "__main__":
    # Simple test when run directly
    setup_status = check_aider_setup()
    logger.info("Aider Setup Status:")
    for key, value in setup_status.items():
        logger.info(f"  {key}: {value}")

    if setup_status["ready"]:
        logger.info("Running connection test...")
        test_result = test_aider_connection()
        logger.info(f"Test result: {test_result}")
    else:
        logger.warning("Setup incomplete - fix errors before testing")