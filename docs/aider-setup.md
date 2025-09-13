# Aider Setup Guide for NapkinWire

This guide explains how to set up Aider with OpenRouter free models for automated ticket implementation, preserving Claude usage for high-level design decisions.

## Overview

Aider is an AI pair programming tool that can automatically implement code changes using various LLMs. By configuring it with free OpenRouter models, we can automate routine ticket implementation while reserving Claude for complex design work.

## Prerequisites

- Python 3.8+ installed
- Git repository initialized
- OpenRouter API key (free tier available)

## Installation

### 1. Install Aider

```bash
pip install aider-chat
```

**Note**: If installation fails with dependency conflicts (common with Python 3.13), try:
- Using a virtual environment
- Installing with `--user` flag
- Using conda instead of pip

### 2. Environment Setup

Set your OpenRouter API key:

```bash
# Windows
set OPENROUTER_API_KEY=your-key-here

# Linux/Mac
export OPENROUTER_API_KEY=your-key-here
```

The key is already configured in `mcp/local_config.py` for this project.

## Configuration

### .aider.conf.yml

The project includes a pre-configured `.aider.conf.yml` file with:

```yaml
# Primary free model
model: openrouter/qwen/qwen-2.5-coder-32b-instruct

# Alternative free models
# - openrouter/microsoft/phi-3-mini-128k-instruct:free
# - openrouter/google/gemma-2-9b-it:free
# - openrouter/meta-llama/llama-3.2-3b-instruct:free

# Behavior settings
auto_commits: true
git: true
show_diffs: true
```

## Usage

### Basic Commands

1. **Simple code changes**:
   ```bash
   aider --message "Add docstring to the add function in main.py"
   ```

2. **Implement specific tickets**:
   ```bash
   aider --message "Implement TICKET-023: Refactor main.py into modules"
   ```

3. **Work with specific files**:
   ```bash
   aider mcp/main.py --message "Extract ticket functions to ticket_manager.py"
   ```

### Using the Integration Module

The project includes `mcp/tools/aider_integration.py` with helper functions:

```python
from mcp.tools.aider_integration import run_aider_on_ticket, check_aider_setup

# Check setup
status = check_aider_setup()
print(status)

# Run Aider on a ticket
output, code = run_aider_on_ticket(
    "TICKET-023",
    "Refactor main.py into modules",
    ["Extract ticket functions", "Update imports", "Preserve functionality"]
)
```

## Free Models on OpenRouter

### Recommended Models

1. **Qwen2.5-Coder-32B** (Primary)
   - Best for code generation
   - Good at following requirements
   - Model: `openrouter/qwen/qwen-2.5-coder-32b-instruct`

2. **Phi-3-Mini-128K** (Fallback)
   - Fast responses
   - Good for simple tasks
   - Model: `openrouter/microsoft/phi-3-mini-128k-instruct:free`

3. **Gemma-2-9B** (Alternative)
   - General purpose
   - Good reasoning
   - Model: `openrouter/google/gemma-2-9b-it:free`

### Switching Models

Edit `.aider.conf.yml` and change the `model:` line, or use command line:

```bash
aider --model openrouter/microsoft/phi-3-mini-128k-instruct:free --message "Your task"
```

## Workflow Integration

### Ticket-to-Aider Process

1. **Design with Claude**: Use Claude for architectural decisions and complex design
2. **Implement with Aider**: Use free models for routine implementation
3. **Review and test**: Always review Aider's changes before committing

### Example Workflow

```bash
# 1. Get ticket requirements from Claude
# 2. Use Aider for implementation
aider --message "Implement TICKET-025: Setup pytest infrastructure
Requirements:
- Install pytest and pytest-cov
- Create tests/ directory
- Write basic test fixtures
- Create test templates"

# 3. Review the changes
git diff

# 4. Test and refine if needed
pytest
```

## Troubleshooting

### Common Issues

1. **"aider: command not found"**
   - Aider may not be in PATH
   - Try: `python -m aider --version`
   - Reinstall with `--user` flag

2. **OpenRouter API errors**
   - Check your API key is set: `echo $OPENROUTER_API_KEY`
   - Verify the model name is correct
   - Try a different free model

3. **Git repository errors**
   - Ensure you're in a git repository
   - Commit any uncommitted changes first

4. **Model context limits**
   - Use `--no-stream` for large files
   - Work with specific files using `aider file1.py file2.py`

### Getting Help

```bash
aider --help
aider --models  # List available models
```

## Cost Tracking

Since we're using free models, costs should be minimal. Monitor usage at:
- OpenRouter dashboard: https://openrouter.ai/activity

## Best Practices

1. **Start small**: Test with simple tasks before complex tickets
2. **Review everything**: Always review Aider's changes
3. **Specific prompts**: Be explicit about requirements
4. **File-specific**: Target specific files when possible
5. **Commit frequently**: Use Aider's auto-commit feature

## Integration with NapkinWire MCP

Future enhancements could include:
- MCP tool to queue tickets for Aider
- Automated ticket processing daemon
- Integration with ticket management system

---

This setup preserves Claude usage for high-level design while leveraging free models for routine implementation, making the development process more cost-effective.