# email-cleanup

Gmail + iCloud inbox cleanup, exposed as an **MCP server**.

Wire it into Claude Code / Claude Desktop and chat with Claude to clean your inbox. A dedicated subagent (`email-cleanup`) is registered at `~/Projects/.claude/agents/` so prompts like *"clean up my email"* auto-delegate to it.

## Status

Per the [build order](../../../email_cleaner_mcp_plan.txt):

- **Step 1 done:** `list_accounts`.
- **Step 4 (partial) done:** iCloud IMAP provider with `search_emails`, `get_email`, `list_folders`.
- **Step 3 done:** `move_email` + `delete_email` (iCloud, `dry_run=True` default; delete = move to Trash).
- **Step 2 deferred:** Gmail provider (focusing on iCloud for now).
- **Step 5 pending:** rules engine.

## Install

```bash
cd agents/email-cleanup
uv sync
```

## iCloud credentials

iCloud blocks regular passwords for IMAP — you need an **app-specific password**:

1. Sign in at https://appleid.apple.com
2. *Sign-In and Security* → *App-Specific Passwords* → *Generate an app-specific password*
3. Label it `email-cleanup-mcp` and copy the 16-char password

Set both vars in the MCP server's `env` block (see below). Server reads them at startup.

## Run the MCP server (stdio)

```bash
ICLOUD_EMAIL=you@icloud.com ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx uv run email-cleanup-server
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
      ],
      "env": {
        "ICLOUD_EMAIL": "you@icloud.com",
        "ICLOUD_APP_PASSWORD": "xxxx-xxxx-xxxx-xxxx"
      }
    }
  }
}
```

Then in a Claude Code session: *"clean up my email"* — the `email-cleanup` subagent will route the request and call this server's tools.

## Tools

| Tool | Status | Notes |
|---|---|---|
| `list_accounts` | done | Returns `["gmail", "icloud"]`. |
| `list_folders(account)` | iCloud only | Lists mailbox folders. Each entry: `name` (use as `folder`/`dest_folder`) + `special_use` (`\Trash`, `\Archive`, `\Junk`, … or null). |
| `search_emails(account, query, folder, max_results)` | iCloud only | `query` is raw IMAP search syntax (e.g. `UNSEEN`, `FROM "github.com"`, `SINCE 1-Jan-2026`); `None` = all. Newest first. Capped at 200. |
| `get_email(account, message_id, folder)` | iCloud only | `message_id` is the IMAP uid returned by `search_emails`. |
| `move_email(account, message_ids, dest_folder, folder, dry_run)` | iCloud only | Moves a list of uids from `folder` to `dest_folder`. **`dry_run=True` default** — returns what *would* move; re-run with `dry_run=False` to move. Fails without moving if any uid is missing or `dest_folder` doesn't exist. |
| `delete_email(account, message_ids, folder, dry_run)` | iCloud only | Deletes a list of uids by moving them to Trash (recoverable, not a permanent purge). **`dry_run=True` default**. Fails without deleting if any uid is missing or `folder` is the Trash folder. |

Gmail dispatch raises `NotImplementedError` until step 2 lands.

## Layout

```
src/email_cleanup/
  server.py              # FastMCP server — tool surface, dispatches to providers
  providers/
    __init__.py
    base.py              # EmailProvider ABC + EmailSummary / EmailMessage dataclasses
    icloud.py            # iCloud IMAP impl (imap.mail.me.com:993, app-specific password)
```

## Roadmap

Next, per the [plan](../../../email_cleaner_mcp_plan.txt):

- **Step 5:** Rules engine + `apply_rules`.
- **Step 2 (deferred):** Gmail provider behind the same `EmailProvider` ABC.
