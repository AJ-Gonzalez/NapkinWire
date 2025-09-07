# Run server in claude desttop with

```json
{
  "mcpServers": {
    "napkinwire": {
      "command": "uv",
      "args": ["--directory", "/path/to/your/project", "run", "napkinwire_mcp.py"],
      "env": {
        "NAPKINWIRE_PROJECT": "path to env"
      }
    }
  }
}
```