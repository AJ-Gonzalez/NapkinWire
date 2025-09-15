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

## [Later] NapkinWire Ultimate TUI Orchestration Interface
*Added: 2025-09-13 03:54 UTC*
Build complete NapkinWire TUI using Textual - the ultimate orchestration interface. Six-panel layout: (1) Chat input with voice hotkey, (2) Scrollable chat with TTS, (3) Initiative feed summary, (4) Ticket status dashboard, (5) Security/quality alerts, (6) Git-aware project tree with file status coloring. Designed for thin clients and SSH access - run on cheap ARM laptop, orchestrate beefy desktop remotely. No GUI needed, pure terminal interface. This is the endgame interface where all NapkinWire components come together in one unified TUI. Must be lightweight, responsive, and work over slow connections. Future: TUI diagram editors for complete terminal-only workflow.
---

## [Soon] Aider + Qwen integration for automated code implementation
*Added: 2025-09-13 07:23 UTC*
Integrate Aider with OpenRouter Qwen2.5-Coder for automated ticket implementation. Create MCP tool to queue tickets for Aider processing - non-blocking subprocess that starts Aider with ticket requirements as prompt. Aider handles all file editing with git integration while using Qwen for code generation at fraction of Claude's cost. Tool monitors Aider status, tracks completion, updates ticket status automatically. Enables parallel ticket processing. Architecture: Opus designs → Queue to Aider+Qwen → Sonnet reviews. Requires: Aider config with OpenRouter, ticket-to-prompt templates, process manager for multiple instances, status tracking via files.
---

## [Next] Graceful Forgetfulness Engine - Controlled Context Management
*Added: 2025-09-13 12:53 UTC*
LLMs need both selective memory AND controlled forgetting. Current context windows fill exponentially with no control over what gets forgotten. Solution requires two systems: (1) REMEMBER: Critical information extraction to ChromaDB - project constants, decisions, key context, user preferences. (2) FORGET: Seamless chat rotation with context handoff - automatically spawn new chat with only essential context carried over. User experiences continuous conversation while backend manages context boundaries. Implementation: Monitor token usage, identify context bloat, extract key facts before rotation, inject minimal bootstrap context into new session. Goal: Infinite effective context through intelligent pruning. The LLM should 'shed' irrelevant context like a snake sheds skin, keeping only what matters.
---

## [Later] Context analysis tool for auto-identifying important decisions
*Added: 2025-09-13 13:03 UTC*
Automated context analysis tool that scans current chat and identifies key decisions that should be saved. At the end of a session or periodically, it could analyze the conversation and suggest: 'Here are 5 key decisions from this chat that should be saved.' Could use pattern matching for decision indicators like 'decided to', 'will use', 'going with', 'the plan is', etc. Output formatted save_decision commands ready to execute.
---

## [Soon] Taiga integration for professional ticket management
*Added: 2025-09-13 22:08 UTC*
Replace basic JSON ticket system with Taiga integration. Taiga is open source project management with Kanban/Scrum boards, epics, user stories, Git integration (GitHub/GitLab), and REST API. Features: sync tickets bidirectionally, create tickets from MCP tools, update status from Claude Code, leverage proper project management workflows, maintain Git commit linking. Self-hosted or cloud options. Much more professional than current ticket.json approach while staying open source. Could integrate with existing ticket tools or replace entirely.
---

## [Ideas] Image search capability for competitive analysis and visual research
*Added: 2025-09-14 04:26 UTC*
Add image search capability to Claude for better competitive analysis and research. Would enable visual research for tools, UI patterns, API documentation examples, competitor analysis, etc. Could be integrated as MCP tool or requested as core Claude feature. Useful for understanding visual design patterns when building sketch-to-code tools and comparing against existing solutions.
---

## [Next] API Flow diagram editor with OpenAPI prompt generation
*Added: 2025-09-14 04:42 UTC*
Add API Flow diagram editor to NapkinWire as a third tab alongside UI Mockups and Diagrams. Core features: (1) Simplified diagram editor for API design - boxes represent resources/endpoints (Pet, User, Order), arrows represent relationships/flows between endpoints, clickable arrow labeling system for adding HTTP methods (GET, POST, PUT, DELETE), authentication requirements, data flow indicators. (2) Structured export system - convert diagram to JSON format with boxes, arrows, labels instead of ASCII for easier parsing. Example: {"boxes": [{"id": "pet", "label": "Pet API", "position": {...}}], "arrows": [{"from": "pet", "to": "auth", "label": "requires OAuth2"}]}. (3) OpenAPI prompt generation - transform diagram JSON into structured LLM prompt: "Create OpenAPI spec for Pet API with GET/POST endpoints, requires OAuth2 auth, returns JSON responses..." Users copy/paste prompt into their preferred AI tool (ChatGPT, Claude, etc.). Technical implementation: Extend existing diagram editor, reuse ASCII conversion logic but adapt for API patterns, add arrow interaction system for labeling, create prompt template engine. This validates API documentation market without AI hosting costs or reliability issues. Week 1 MVP plan: Days 1-2 modify diagram editor, Days 3-4 implement arrow labeling, Day 5 build prompt generation, Days 6-7 integrate into NapkinWire and polish.
---

## [Next] ASCII-to-SVG diagram renderer via MCP tool
*Added: 2025-09-14 05:31 UTC*
Reverse ASCII-to-visual converter via MCP tool integration. LLMs generate ASCII/Unicode diagrams but users need actual visuals for presentations and documentation. Tool parses ASCII characters into geometric shapes, maps common diagram patterns (boxes, arrows, connectors, network topologies), and renders clean SVG output. MCP integration allows seamless workflow: LLM creates ASCII diagram → calls MCP tool → browser popup displays rendered SVG → user saves as PNG/SVG. Technical implementation: reverse-engineer existing ASCII conversion logic, add SVG rendering engine, support multiple diagram types (flowcharts, network diagrams, org charts), include styling themes (corporate, minimal, colorful). Solves real friction point where LLMs produce ugly text diagrams but users need professional visuals. Natural extension of existing NapkinWire ASCII conversion capabilities running in reverse direction.
---

## [Soon] Multi-project context management and memory system
*Added: 2025-09-15 02:39 UTC*
Build project context management system to enable multi-project AI assistance. Core functionality: create_project(), switch_project(), list_projects(), get_current_project() for project management. Memory tools per project: save_context(), load_context(), update_project_status() for persistent project-specific information. Cross-project capabilities: link_projects(), search_all_projects() for finding connections and information across multiple projects. Current project cache eliminates need to reload context when switching between projects (NapkinWire, real estate lead qualification, etc.). Addresses the "glass jar" isolation problem by giving AI tools to maintain multiple working contexts and switch seamlessly between them. Technical implementation: project-specific data storage, context switching logic, memory persistence across sessions, project relationship mapping. This enables the distributed agentic thinking architecture by providing foundational memory and context management capabilities.
---
