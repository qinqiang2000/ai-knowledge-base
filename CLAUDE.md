# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Agent service built with FastAPI and the Claude Agent SDK. The service provides a customer service chatbot that uses Claude Code as a skill to answer questions about invoice management products by searching through a knowledge base.

**Key Architecture Pattern**: This service uses Claude Code (via Claude Agent SDK) as a **skill** to search knowledge bases and answer customer questions. The knowledge base is mounted as the working directory (`cwd`), and Claude Code has access to specialized skills defined in `.claude/skills/`.

## Common Commands
### Interactive CLI Tool

The CLI tool provides an interactive REPL for testing the customer service agent:

```bash
source .venv/bin/activate
python cli.py
```

### Running the Service

```bash
# Start with auto-restart (development mode)
./run.sh start

# Stop the service
./run.sh stop

# Restart the service (default)
./run.sh
./run.sh restart
```

The service runs on `http://localhost:9090` by default (configurable via `PORT` in `.env.prod`).

## Architecture

### Request Flow

1. **API Request** → FastAPI endpoint (`/api/customer-service/query` or `/api/query`)
2. **AgentService** → Builds prompt with skill and context
3. **Claude Agent SDK** → Creates ClaudeSDKClient with:
   - System prompt: `claude_code` preset
   - Working directory: project root (mounted as knowledge base)
   - Allowed tools: `Skill`, `Read`, `Grep`, `Glob`, `Bash`, `WebFetch`, `WebSearch`
   - Skills: `.claude/skills/` (e.g., `customer-service`)
4. **StreamProcessor** → Processes streaming responses, extracts session IDs and todos
5. **SSE Response** → Streamed back to client via Server-Sent Events


### Key Components

**AgentService** (`api/services/agent_service.py`):
- Assembles prompts using `build_initial_prompt()`
- Configures Claude SDK options
- Sets `cwd` to project root to expose knowledge base
- Delegates streaming to `StreamProcessor`

**StreamProcessor** (`api/core/streaming.py`):
- Processes Claude SDK message stream
- Handles session registration/unregistration (for interrupt support)
- Extracts todos from `TodoWrite` tool calls
- Formats SSE messages

**SessionService** (`api/services/session_service.py`):
- Manages active sessions (maps session_id → ClaudeSDKClient)
- Supports interrupting sessions via `interrupt(session_id)`

**ConfigService** (`api/services/config_service.py`):
- Manages model configurations (defined in `api/services/config_service.py`)
- Supports multiple providers: `claude-router` (local proxy), `glm` (智谱清言)
- Default config set via `DEFAULT_MODEL_CONFIG` in `.env.prod`

### Prompt Building Strategy

Initial prompts are built by `build_initial_prompt()` (`api/utils/prompt_builder.py`):

The skill file (`.claude/skills/customer-service/skill.md`) contains the actual business logic and instructions for how Claude Code should search the knowledge base.

### Session Continuity

Sessions are managed by `SessionService`:
- New sessions: `session_id` extracted from Claude SDK's `SystemMessage` (subtype='init')
- Resume sessions: Pass `session_id` in request, Claude SDK resumes via `options.resume`
- Interrupt support: `SessionService.register()` maps session_id to active `ClaudeSDKClient`, allowing `interrupt(session_id)` to call `client.interrupt()`

## Configuration

### Environment Variables

Configuration is loaded from `.env.prod`:

```bash
DEFAULT_MODEL_CONFIG=glm          # or "claude-router"
GLM_AUTH_TOKEN=<your-token>       # 智谱清言 API token
CLAUDE_ROUTER_AUTH_TOKEN=test     # Local proxy token
PORT=9090                         # Service port
LOG_LEVEL=INFO                    # Logging level
```

## API Endpoints

- `GET /` - Chat UI
- `POST /api/query` - Generic agent query (configurable skill)
- `POST /api/customer-service/query` - Customer service specific endpoint (fixed skill)
- `GET /docs` - OpenAPI documentation
- Admin endpoints at `/admin/*` (config management, log viewing)
