from fastmcp import FastMCP
import os
import logging
import asyncio
import time
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('napkinwire-mcp')
mcp = FastMCP("napkinwire")


@mcp.tool
def project_tree(
    max_depth: int = 3,
    show_hidden: bool = False
) -> str:
    logger.info(f"project_tree called with max_depth={max_depth}, show_hidden={show_hidden}")

    try:
        project_root = os.environ.get('NAPKINWIRE_PROJECT', os.getcwd())
        root_path = Path(project_root)

        if not root_path.exists():
            return f"Error: Project root does not exist: {project_root}"

        if not root_path.is_dir():
            return f"Error: Project root is not a directory: {project_root}"

        tree_lines = [f"{root_path.name}/"]

        def build_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return
            try:
                items = list(path.iterdir())
                if not show_hidden:
                    items = [item for item in items if not item.name.startswith('.')]
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                    if item.is_dir():
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        build_tree(item, next_prefix, depth + 1)
            except Exception as e:
                tree_lines.append(f"{prefix}└── [Error: {str(e)}]")

        build_tree(root_path)
        return "\n".join(tree_lines)

    except Exception as e:
        logger.error(f"Error generating project tree: {str(e)}")
        return f"Error: {str(e)}"


@mcp.tool
async def watch_for_file(
    mode: str,
    timeout: int = 30
) -> str:
    """Watch for completed napkinwire files in temp directory
    
    Args:
        mode: Either 'diagram' or 'UI' to specify file type to watch for
        timeout: Maximum time to wait in seconds (default: 30)
    
    Returns:
        File contents when found, or error message if timeout/failure
    """
    logger.info(f"watch_for_file called with mode={mode}, timeout={timeout}")
    
    # Validate mode parameter
    if mode not in ["diagram", "UI"]:
        return f"Error: Invalid mode '{mode}'. Must be 'diagram' or 'UI'"
    
    # Validate timeout parameter
    if timeout <= 0 or timeout > 300:  # Max 5 minutes
        return f"Error: Invalid timeout {timeout}. Must be between 1 and 300 seconds"
    
    try:
        # Get system temp directory
        temp_dir = Path(tempfile.gettempdir())
        logger.info(f"Watching temp directory: {temp_dir}")
        
        # File pattern to match
        pattern = f"napkinwire_{mode}_*.txt"
        
        # Start time for timeout calculation
        start_time = time.time()
        poll_interval = 0.5  # 500ms
        
        while True:
            # Check if timeout exceeded
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return f"Timeout: No {mode} file found after {timeout} seconds"
            
            # Look for matching files
            matching_files = list(temp_dir.glob(pattern))
            
            if matching_files:
                # Sort by modification time, get newest
                newest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"Found file: {newest_file}")
                
                try:
                    # Read file contents
                    content = newest_file.read_text(encoding='utf-8')
                    
                    # Clean up - delete the file after reading
                    newest_file.unlink()
                    logger.info(f"File {newest_file.name} processed and deleted")
                    
                    # Return structured response
                    return f"File found: {newest_file.name}\n\nContent:\n{content}"
                    
                except PermissionError:
                    return f"Error: Permission denied accessing file {newest_file.name}"
                except UnicodeDecodeError:
                    return f"Error: Unable to decode file {newest_file.name} as UTF-8"
                except Exception as e:
                    return f"Error reading file {newest_file.name}: {str(e)}"
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            
    except Exception as e:
        logger.error(f"Error in watch_for_file: {str(e)}")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting NapkinWire MCP server")
    mcp.run()
    mcp.enable_openapi()

# TODO: Flesh out note taking, add tool for it. 
# TODO: ask cheper llm for code snippet
# TODO: trigger claude code action
# TODO: push to github (maybe)
# TODO: add memory MCP to Claude (other tool, not here)
