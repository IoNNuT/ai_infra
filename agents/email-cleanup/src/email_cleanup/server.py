"""MCP server entrypoint for email cleanup.

Exposes a small composable tool surface (currently just `list_accounts`).
Runs over stdio so it can be wired into Claude Code interactively and into
the agent runner for autonomous/scheduled use — single source of truth for
the tool layer.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("email-cleanup")


@mcp.tool()
def list_accounts() -> list[str]:
    """Return the email accounts this server can operate on."""
    return ["gmail", "icloud"]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
