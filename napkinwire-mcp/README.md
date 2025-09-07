# Napkinwire MCP Server

A minimal MCP (Model Context Protocol) server template that demonstrates the absolute bare minimum implementation.

## Installation

```bash
npm install
```

## Running the Server

```bash
npm start
```

This will start the MCP server and display "napkinwire-mcp server running" message.

## Configuration

To use this server with Claude Desktop, add the following to your Claude Desktop MCP settings file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "napkinwire-mcp": {
      "command": "node",
      "args": ["C:/path/to/napkinwire-mcp/src/index.js"]
    }
  }
}
```

Replace `C:/path/to/napkinwire-mcp/src/index.js` with the actual path to your index.js file.

## Expected Behavior

- Server connects successfully via stdio transport
- Responds to MCP protocol handshake
- Returns empty tools list (no tools available)
- No protocol errors should occur

## Testing

1. Run `npm install` to install dependencies
2. Run `npm start` to start the server
3. Configure the server in Claude Desktop settings
4. Verify connection works and shows no available tools
5. Check console for any errors

This serves as a working foundation that can be extended with actual tools and functionality.