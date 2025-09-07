from fastmcp import FastMCP
import os
from pathlib import Path

mcp = FastMCP("napkinwire")

@mcp.tool
def project_tree(max_depth: int = 3, show_hidden: bool = False) -> str:
    """Display project directory tree"""
    try:
        # Get project root from environment variable or use current directory
        project_root = os.environ.get('NAPKINWIRE_PROJECT', os.getcwd())
        root_path = Path(project_root)
        
        if not root_path.exists():
            return f"Error: Project root directory does not exist: {project_root}"
        
        if not root_path.is_dir():
            return f"Error: Project root is not a directory: {project_root}"
        
        # Generate directory tree
        tree_lines = []
        tree_lines.append(f"{root_path.name}/")
        
        def build_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return
            
            try:
                # Get all items in the directory
                items = list(path.iterdir())
                
                # Filter hidden files if not requested
                if not show_hidden:
                    items = [item for item in items if not item.name.startswith('.')]
                
                # Sort items: directories first, then files
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                    
                    # Recurse into subdirectories
                    if item.is_dir():
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        build_tree(item, next_prefix, depth + 1)
                        
            except PermissionError:
                tree_lines.append(f"{prefix}└── [Permission Denied]")
            except Exception as e:
                tree_lines.append(f"{prefix}└── [Error: {str(e)}]")
        
        build_tree(root_path)
        return "\n".join(tree_lines)
        
    except Exception as e:
        return f"Error generating project tree: {str(e)}"

if __name__ == "__main__":
    mcp.run()
