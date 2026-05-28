# ai_infra

Personal infrastructure for AI agents and MCP servers.

Each agent lives in its own self-contained Python package under [`agents/`](agents/) with its own `pyproject.toml`, virtualenv, and lifecycle. Shared code can move to `packages/` later if more than one agent needs it.

## Agents

| Agent | Path | Purpose |
|---|---|---|
| email-cleanup | [`agents/email-cleanup/`](agents/email-cleanup/) | Gmail + iCloud inbox cleanup — MCP server (tool layer) + thin agent runner (autonomous/scheduled use) |

## Layout

```
ai_infra/
  agents/
    email-cleanup/
      pyproject.toml
      src/email_cleanup/
        server.py        # MCP server entrypoint
        runner.py        # Claude Agent SDK runner
        providers/       # Gmail / iCloud backends
      tests/
  packages/              # shared libs, added when needed
```

## Conventions

- **Python + uv.** Each agent is created with `uv init --package` and uses the `src/<pkg>/` layout.
- **MCP server + runner pattern.** The MCP server is the dumb tool surface (search/move/delete). The runner wraps it with the Claude Agent SDK for autonomous or scheduled execution. Interactive use goes through Claude Code talking to the MCP server directly.
- **Local-only credentials.** Each agent stores secrets under `~/.<agent-name>/` (or the OS keyring), never in the repo.
- **Dry-run by default** for any destructive tool.

## Adding a new agent

```bash
cd agents
uv init --package <agent-name> --python 3.12
cd <agent-name>
uv add mcp claude-agent-sdk
```
