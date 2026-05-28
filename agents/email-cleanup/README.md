# email-cleanup

Gmail + iCloud inbox cleanup, exposed as an **MCP server**.

Wire it into Claude Code / Claude Desktop and chat with Claude to clean your inbox. A dedicated subagent (`email-cleanup`) is registered at `~/Projects/.claude/agents/` so prompts like *"clean up my email"* auto-delegate to it.

## Status

Step 1 of the [build order](../../../email_cleaner_mcp_plan.txt): skeleton server with `list_accounts` returning hardcoded `["gmail", "icloud"]`. No real provider integration yet.

## Install

```bash
cd agents/email-cleanup
uv sync
```

## Run the MCP server (stdio)

```bash
uv run email-cleanup-server
```

The server speaks MCP over stdio. To use it from Claude Code, add to your `~/.claude.json` (or workspace MCP config):

```json
{
  "mcpServers": {
    "email-cleanup": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/ionutbucheru/Projects/portfolio_analysis_prj/portfolio-analysis/ai_infra/agents/email-cleanup",
        "run",
        "email-cleanup-server"
      ]
    }
  }
}
```

Then in a Claude Code session: *"clean up my email"* — the `email-cleanup` subagent will route the request and call this server's tools.

## Layout

```
src/email_cleanup/
  server.py     # FastMCP server — defines tools
```

## Roadmap

Next, per the [plan](../../../email_cleaner_mcp_plan.txt):

- **Step 2:** Gmail provider + `search_emails` + `get_email` (read-only).
- **Step 3:** `move_email`, `delete_email` with `dry_run=True` default.
- **Step 4:** iCloud IMAP provider behind the same interface.
- **Step 5:** Rules engine + `apply_rules`.

Provider code will land under `src/email_cleanup/providers/` behind a common `EmailProvider` ABC so Gmail and iCloud look the same to the tool layer.
