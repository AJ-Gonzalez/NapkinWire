# NapkinWire Roadmap

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



## [Later] Feedback tooling
*Added: 2025-09-12 12:05 UTC*
MCP integrated user feedback tool. Send optionally anonymous messages through LLM tool call. Capture feedback and announce new releases/features on GitHub. Example: 'napkinwire needs a tool for connecting to databases. Sent from claude code 4 sonnet.'
---

## [Later] Security audit tooling
*Added: 2025-09-12 12:05 UTC*
LLM call via OpenRouter to cheap model for code analysis. Look for vulnerabilities across codebase. Will need code sanitization.
---

## [Soon] OpenRouter and self-hosted LLM support
*Added: 2025-09-12 12:05 UTC*
Support for OpenRouter and self-hosted models via OpenAI API format. Enable cheaper models for routine tasks and local/VPS hosted alternatives.
---

## [Later] RAG for language reference and style guides
*Added: 2025-09-12 12:05 UTC*
Add Chroma DB or similar vector database for language references and style guides. Needs to be performant on CPU-only local machines. Use for maintaining coding standards across AI assistants.
---

## [Soon] Test coverage and code quality audit utility
*Added: 2025-09-12 12:05 UTC*
Run test coverage, linters, etc. Auto-generate tests as needed. Provide actionable items ranked by priority for code quality improvements.
---

## [Next] Venn diagram set notation editor
*Added: 2025-09-12 12:05 UTC*
Visual set theory tool for data filtering. Draw Venn diagrams that output formal set notation like (A ∩ B) \ C for pipeline operations and SQL generation.
---

## [Later] Neovim MCP client integration
*Added: 2025-09-12 12:05 UTC*
MCP client for Neovim using Lua. Enable AI assistance directly in editor with commands like :NapkinTicket, :NapkinAsk. Full flow state without leaving vim.
---

## [Later] NapkinWire Custom Client with Initiative Engine
*Added: 2025-09-12 16:06 UTC*
Build a custom NapkinWire client that wraps Claude/Anthropic API with scheduler, initiative engine, and full MCP support. Would enable scheduled tasks, autonomous monitoring, and event-driven AI interactions. Required because MCP is pull-only (request-response) - LLMs cannot receive push notifications or maintain persistent connections. The client would orchestrate AI calls based on schedules and triggers, maintaining state between sessions. Could route between Opus/Sonnet based on task complexity. Architecture: Client runs continuously → monitors events → triggers AI calls → manages conversation state.
---

## [Later] MCP Protocol Limitations Documentation
*Added: 2025-09-12 16:06 UTC*
Research MCP protocol limitations and document architectural constraints. MCP is strictly request-response (pull-based), not event-driven. Servers cannot push updates to LLMs, no persistent connections, no webhooks/callbacks. Each tool call is independent and stateless. This affects Initiative Engine design - must work around these constraints with polling patterns or external orchestration. Document patterns for working within these limits: accumulator patterns, status checking tools, notification bridges to humans.
---

## [Later] Browser Automation Bridge for Claude Desktop
*Added: 2025-09-12 16:06 UTC*
Implement browser automation wrapper using Playwright/Selenium to programmatically control Claude Desktop. Interim solution before API access. Would enable scheduled tasks and automated workflows by driving the UI. Could paste contexts, read responses, and manage conversations programmatically. Less elegant than API but available now. Would provide pathway to test Initiative Engine concepts before full client build.
---

## [Later] Permanent Context Management System
*Added: 2025-09-12 16:28 UTC*
Automated context management system for custom client - eliminate manual chat management. Persistent context across all interactions, automatic context pruning and summarization, intelligent context loading based on current task. No new chat creation, just continuous workflow. Include: vector DB for long-term memory, automatic context summarization when approaching limits, smart context retrieval based on relevance, conversation threading by topic/project, automatic archival of old contexts. Goal: Never lose context, never manually manage chats, just continuous flow state.
---

## [Soon] Ticket visualization dashboard
*Added: 2025-09-12 16:33 UTC*
Tool to visualize all tickets in a dashboard view - show status, priority, dependencies, and completion progress. Help decide what to implement next. Could show burn-down chart, velocity metrics, blocked tickets. Maybe HTML output or ASCII art dashboard.
---

## [Soon] Project context and philosophy manager
*Added: 2025-09-12 16:33 UTC*
Maintain project philosophy, coding standards, and architectural decisions in a central place. Tools to fetch current context and update as project evolves. Should include: why certain decisions were made, coding conventions, project goals, preferred patterns, anti-patterns to avoid. This becomes the 'institutional knowledge' that persists across sessions.
---

## [Soon] Documentation engine
*Added: 2025-09-12 16:33 UTC*
Automated documentation generator that creates and maintains project docs. Should generate API docs from code, README updates from tickets, architecture diagrams from code structure, and decision records from commit messages. Keep documentation in sync with code automatically. Output in markdown for easy reading and version control.
---
