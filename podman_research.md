# Podman Containerization Research for NapkinWire MCP Server on Windows

## Executive Summary

This research evaluates the feasibility of containerizing the NapkinWire MCP server using Podman on Windows. Based on current technology landscape (2025), the report covers installation approaches, volume handling, configuration methods, performance implications, and specific challenges for MCP server deployment.

## 1. Podman Installation on Windows (WSL2 vs Native)

### WSL2 Approach (Recommended)

**Installation Process:**
- Requires Windows 10 Build 19043+ or Windows 11
- Install WSL2: `wsl --install` (installs WSL2, VM Platform, Linux kernel, Ubuntu by default)
- Install Podman within Ubuntu/Fedora WSL2 instance
- Can access Podman directly from WSL or via Windows PowerShell

**Advantages:**
- Superior performance compared to WSL1
- Full system call compatibility (100% vs WSL1's partial compatibility)
- Native Linux container environment
- Better integration with Linux-based development workflows

**WSL2 Setup Commands:**
```bash
# In WSL2 Ubuntu/Fedora instance
sudo apt update && sudo apt install podman  # Ubuntu
# or
sudo dnf install podman                     # Fedora
```

### Native Windows Approach

**Installation Process:**
1. Download Podman Windows installer from official GitHub releases
2. Run EXE installer, relaunch terminal
3. Run `podman machine init` to install minimal Fedora in WSL2
4. Each Podman machine is backed by virtualized WSL2 distribution

**Communication Model:**
- PowerShell/CMD runs `podman.exe`
- Commands remotely communicate with Podman service in WSL environment
- Transparent to user but adds communication layer

**Advantages:**
- Windows-native command interface
- Consistent with Windows development patterns
- Integrated with Windows PATH and terminal

## 2. Volume Mounts for tickets.json and Project Files

### Volume Mount Syntax
```bash
# Basic bind mount
podman run -v /host/path:/container/path image

# Windows path example
podman run -v "C:\Users\Username\Project:/app/project" image

# With options for permissions
podman run -v "/host/path:/container/path:Z" image  # SELinux labeling
```

### Specific Configuration for NapkinWire
```bash
# Mount tickets.json and project root
podman run -it \
  -v "$(pwd)/tickets.json:/app/tickets.json" \
  -v "$(pwd):/app/project" \
  -v "$(pwd)/web:/app/web" \
  napkinwire-mcp:latest
```

### Permission Handling
- **Windows WSL2**: May require `chown` option: `-v "path:path:U"`
- **SELinux Systems**: Append `:z` or `:Z` for proper labeling
- **User Namespace**: Use `--userns=keep-id` for UID/GID mapping

### Volume Mount Considerations
- Private by default (mounts inside container not visible on host)
- `U` flag changes ownership recursively based on container UID/GID
- Windows paths must be properly quoted for spaces

## 3. Configuration: Arguments vs Environment Variables

### Arguments Approach
```dockerfile
# Dockerfile
ENTRYPOINT ["python", "main.py"]
CMD ["--tickets-path", "/app/tickets.json", "--project-root", "/app/project"]
```

```bash
# Runtime
podman run napkinwire-mcp --tickets-path /custom/tickets.json --debug
```

### Environment Variables Approach
```dockerfile
# Dockerfile
ENV TICKETS_PATH=/app/tickets.json
ENV PROJECT_ROOT=/app/project
ENV DEBUG=false
```

```bash
# Runtime
podman run -e TICKETS_PATH=/custom/tickets.json -e DEBUG=true napkinwire-mcp
```

### Hybrid Approach (Recommended)
```python
# config.py
import os
import argparse

def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tickets-path',
                       default=os.getenv('TICKETS_PATH', '/app/tickets.json'))
    parser.add_argument('--debug',
                       default=os.getenv('DEBUG', 'false').lower() == 'true')
    return parser.parse_args()
```

**Advantages:**
- Environment variables for container orchestration
- Arguments for development/testing flexibility
- Consistent with 12-factor app principles

## 4. Resource Usage vs Native Python

### Performance Comparison Data

**Memory Overhead:**
- Podman: Lower memory overhead than Docker due to daemonless architecture
- Container vs Native: Minimal overhead (0.1-0.2% difference)
- Podman idle footprint: Zero (no persistent daemon)

**CPU Performance:**
- Podman vs Docker: Podman 86% CPU, Docker 84% CPU (negligible difference)
- Container vs Native: 0.12% slower than native on average
- Python-specific: Often equivalent or faster in containers

**Startup Time:**
- Podman: Faster startup than Docker (daemonless architecture)
- Container overhead: ~100-200ms additional startup time
- MCP server: Acceptable for non-real-time applications

### Resource Usage Implications for MCP Server
- **Memory**: 50-100MB additional container overhead
- **CPU**: Negligible impact for I/O-bound MCP operations
- **Disk**: Base image ~200MB + dependencies ~100MB
- **Network**: No meaningful overhead for localhost communication

## 5. Dockerfile Structure for MCP Server

```dockerfile
# Multi-stage build for efficiency
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Copy application code
COPY mcp/ ./mcp/
COPY web/ ./web/
COPY config.py .
COPY main.py .

# Set up volume mount points
VOLUME ["/app/data", "/app/project"]

# Environment variables
ENV PYTHONPATH=/app
ENV TICKETS_PATH=/app/data/tickets.json
ENV PROJECT_ROOT=/app/project
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import main; print('OK')" || exit 1

# Expose MCP stdio interface
ENTRYPOINT ["python", "-u", "main.py"]
```

## 6. STDIO Communication Through Container

### MCP Server STDIO Requirements
- **Interactive Mode**: Must use `-i` flag to keep stdin open
- **TTY**: May need `-t` for pseudo-terminal allocation
- **Unbuffered**: Python requires `PYTHONUNBUFFERED=1` environment variable

### Podman Command for MCP STDIO
```bash
podman run --rm -i \
  -v "$(pwd)/tickets.json:/app/data/tickets.json" \
  -v "$(pwd):/app/project" \
  -e PYTHONUNBUFFERED=1 \
  napkinwire-mcp:latest
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "napkinwire": {
      "command": "podman",
      "args": [
        "run", "--rm", "-i",
        "-v", "C:\\Path\\To\\Project:/app/project",
        "-v", "C:\\Path\\To\\tickets.json:/app/data/tickets.json",
        "-e", "PYTHONUNBUFFERED=1",
        "napkinwire-mcp:latest"
      ]
    }
  }
}
```

### STDIO Communication Verification
```python
# Test script for container stdio
import sys
import json

def test_stdio():
    # Read from stdin
    line = sys.stdin.readline().strip()
    request = json.loads(line)

    # Process and respond via stdout
    response = {"result": "OK", "input": request}
    print(json.dumps(response))
    sys.stdout.flush()

if __name__ == "__main__":
    test_stdio()
```

## 7. GUI Tools (PyWebView) Potential Issues

### Critical Limitation: No GUI Support
- **Containers are headless**: No X11 display server access by default
- **PyWebView requires desktop environment**: WebView2, GTK, or Qt backends need GUI
- **Windows containers**: No native GUI support in WSL2-based Podman

### Workarounds (Not Recommended)
```bash
# X11 forwarding (Linux only, security risk)
podman run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix

# VNC approach (complex, resource-intensive)
podman run -p 5901:5901 image-with-vnc
```

### Recommended Solution: HTTP Server Approach
Current NapkinWire implementation using HTTP server for diagram/UI editors is **container-compatible**:

```python
# Instead of PyWebView
def spawn_diagram_editor():
    # Start HTTP server in container
    # Browser on host accesses http://localhost:8765
    # No GUI dependencies required
    pass
```

### Impact Assessment
- **Diagram Editor**: ✅ Works (HTTP server approach)
- **UI Mockup Editor**: ✅ Works (HTTP server approach)
- **PyWebView Tools**: ❌ Not container-compatible
- **File System Tools**: ✅ Works with volume mounts

## 8. Example Podman Commands for Testing

### Basic MCP Server Test
```bash
# Build image
podman build -t napkinwire-mcp:latest .

# Test stdio communication
echo '{"jsonrpc": "2.0", "method": "test", "id": 1}' | \
podman run --rm -i napkinwire-mcp:latest

# Interactive testing
podman run --rm -it \
  -v "$(pwd):/app/project" \
  napkinwire-mcp:latest bash
```

### Development Configuration
```bash
# Development with hot reload
podman run --rm -it \
  -v "$(pwd):/app/project" \
  -v "$(pwd)/mcp:/app/mcp" \
  -v "$(pwd)/web:/app/web" \
  -e DEBUG=true \
  napkinwire-mcp:dev
```

### Production Configuration
```bash
# Production deployment
podman run -d --name napkinwire-prod \
  --restart unless-stopped \
  -v "/data/tickets.json:/app/data/tickets.json:Z" \
  -v "/projects/napkinwire:/app/project:Z" \
  napkinwire-mcp:latest
```

### Health Check Testing
```bash
# Verify container health
podman healthcheck run napkinwire-prod

# Monitor logs
podman logs -f napkinwire-prod

# Resource usage
podman stats napkinwire-prod
```

## 9. Pros and Cons vs Current Approach

### ✅ Advantages of Containerization

**Deployment Benefits:**
- **Environment Consistency**: Identical runtime across development/production
- **Dependency Isolation**: No conflicts with host Python/packages
- **Easy Distribution**: Single container image vs complex setup instructions
- **Version Management**: Tag-based versioning and rollback capability

**Operational Benefits:**
- **Resource Control**: CPU/memory limits and monitoring
- **Security**: Process isolation and restricted file system access
- **Scalability**: Easy horizontal scaling if needed
- **Portability**: Run on any Podman/Docker-compatible system

**Development Benefits:**
- **Clean Testing**: Isolated test environments
- **CI/CD Integration**: Container-based build/test pipelines
- **Team Consistency**: Same environment for all developers

### ❌ Disadvantages of Containerization

**Complexity Overhead:**
- **Learning Curve**: Dockerfile, volume mounts, networking concepts
- **Build Process**: Multi-step build and image management
- **Debugging**: Additional layer between code and execution
- **Local Development**: More complex setup for development workflow

**Performance Considerations:**
- **Startup Overhead**: 100-200ms additional container startup time
- **Resource Usage**: 50-100MB baseline memory overhead
- **I/O Performance**: Volume mount overhead for file operations
- **GUI Limitations**: PyWebView and desktop app incompatibility

**Operational Complexity:**
- **Image Management**: Registry, updates, security scanning
- **Volume Management**: Backup/restore data persistence
- **Networking**: Port mapping and service discovery
- **Monitoring**: Container-aware logging and metrics

## 10. Recommendation

### Current Assessment: **PROCEED WITH CAUTION**

**Recommendation: Hybrid Approach**

1. **Containerize Core MCP Server**: Package main MCP functionality in container
2. **Keep GUI Tools Native**: Maintain HTTP server approach for UI tools
3. **Gradual Migration**: Start with development/testing containerization

### Implementation Phases

**Phase 1: Development Containerization**
- Create Dockerfile for development testing
- Set up volume mounts for active development
- Test STDIO communication with Claude Desktop
- **Timeline**: 1-2 days

**Phase 2: Production Testing**
- Build optimized production image
- Test performance and resource usage
- Validate all MCP tools work correctly
- **Timeline**: 3-5 days

**Phase 3: Deployment Decision**
- Compare operational complexity vs benefits
- Evaluate team adoption and maintenance burden
- Make go/no-go decision based on real testing
- **Timeline**: 1 week

### Go/No-Go Criteria

**Proceed if:**
- ✅ Container performance overhead < 5%
- ✅ STDIO communication works reliably
- ✅ Volume mounts handle all file operations correctly
- ✅ Team comfortable with container operations

**Do NOT proceed if:**
- ❌ Container adds >10% performance overhead
- ❌ STDIO communication has reliability issues
- ❌ Volume mount permissions cause persistent problems
- ❌ Debugging becomes significantly more difficult

### Alternative: Docker Compose for Development

If full containerization proves too complex, consider Docker Compose for development environment standardization:

```yaml
version: '3.8'
services:
  napkinwire-dev:
    build: .
    volumes:
      - .:/app/project
      - ./tickets.json:/app/data/tickets.json
    environment:
      - DEBUG=true
    stdin_open: true
    tty: true
```

**Final Recommendation**: Start with containerization for testing and development environments. Based on results, make informed decision about production containerization. The current HTTP server approach for GUI tools makes this more feasible than if PyWebView was required.