import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import fcntl  # For file locking on Unix
except ImportError:
    fcntl = None
try:
    import msvcrt  # For file locking on Windows
except ImportError:
    msvcrt = None

# Configure logging
crud_logger = logging.getLogger('napkinwire_crud')

def get_project_root() -> Path:
    """Get project root from TICKETS file path directory"""
    from config import TICKETS
    tickets_path = Path(TICKETS)
    return tickets_path.parent

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