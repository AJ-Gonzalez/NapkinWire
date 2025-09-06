from fastmcp import FastMCP
import os
import logging
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
    

if __name__ == "__main__":
    logger.info("Starting NapkinWire MCP server")
    mcp.run()
    mcp.enable_openapi()

# TODO: Flesh out note taking, add tool for it. 
# TODO: ask cheper llm for code snippet
# TODO: trigger claude code action
# TODO: push to github (maybe)
# TODO: add memory MCP to Claude (other tool, not here)
