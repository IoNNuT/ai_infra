"""MCP server entrypoint for email cleanup.

Exposes a small composable tool surface. Tools dispatch to provider implementations
(`EmailProvider`) so Gmail (API) and iCloud (IMAP) look the same to the tool layer.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from email_cleanup.providers import EmailProvider
from email_cleanup.providers.icloud import ICloudProvider

mcp = FastMCP("email-cleanup")


@lru_cache(maxsize=None)
def _provider(account: str) -> EmailProvider:
    if account == "icloud":
        return ICloudProvider()
    if account == "gmail":
        raise NotImplementedError("gmail provider not wired up yet (build order step 2)")
    raise ValueError(f"unknown account: {account!r} — expected one of: gmail, icloud")


@mcp.tool()
def list_accounts() -> list[str]:
    """Return the email accounts this server can operate on."""
    return ["gmail", "icloud"]


@mcp.tool()
def search_emails(
    account: str,
    query: str | None = None,
    folder: str = "INBOX",
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Search `folder` on `account`, newest first. Returns up to `max_results` summaries.

    Query syntax is provider-specific. For iCloud (IMAP), pass raw IMAP search criteria
    like `UNSEEN`, `FROM "github.com"`, `SINCE 1-Jan-2026`, or leave as None for all.
    """
    max_results = max(1, min(max_results, 200))
    summaries = _provider(account).search(query=query, folder=folder, max_results=max_results)
    return [_serialize(asdict(s)) for s in summaries]


@mcp.tool()
def list_folders(account: str) -> list[dict[str, Any]]:
    """List the mailbox folders on `account`.

    Each entry has `name` (use it as `folder`/`dest_folder` in other tools) and
    `special_use` — the IMAP special-use flag if the folder is well-known (e.g. `\\Trash`,
    `\\Archive`, `\\Junk`), else null. Use this to resolve the exact destination for
    `move_email`, since folder names are case-sensitive.
    """
    return [_serialize(asdict(f)) for f in _provider(account).list_folders()]


@mcp.tool()
def get_email(account: str, message_id: str, folder: str = "INBOX") -> dict[str, Any]:
    """Fetch the full body of one email by id (uid for IMAP) in `folder`."""
    message = _provider(account).get(message_id=message_id, folder=folder)
    return _serialize(asdict(message))


@mcp.tool()
def move_email(
    account: str,
    message_ids: list[str],
    dest_folder: str,
    folder: str = "INBOX",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Move one or more emails from `folder` to `dest_folder` on `account`.

    `message_ids` are the ids (IMAP uids) returned by `search_emails`. Defaults to a dry
    run: with `dry_run=True` nothing is moved and the response lists what *would* move —
    review it, then call again with `dry_run=False` to actually move them. Fails without
    moving anything if any id is missing or `dest_folder` does not exist.
    """
    affected = _provider(account).move(
        message_ids=message_ids,
        dest_folder=dest_folder,
        folder=folder,
        dry_run=dry_run,
    )
    return {
        "dry_run": dry_run,
        "moved": not dry_run,
        "source_folder": folder,
        "dest_folder": dest_folder,
        "count": len(affected),
        "emails": [_serialize(asdict(s)) for s in affected],
    }


@mcp.tool()
def delete_email(
    account: str,
    message_ids: list[str],
    folder: str = "INBOX",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Delete one or more emails on `account` by moving them to Trash (recoverable).

    `message_ids` are the ids (IMAP uids) returned by `search_emails`. This is NOT a
    permanent purge — messages are moved to the account's Trash folder and stay
    recoverable until Trash is emptied. Defaults to a dry run: with `dry_run=True` nothing
    is deleted and the response lists what *would* be deleted — review it, then call again
    with `dry_run=False`. Fails without deleting anything if any id is missing or `folder`
    is itself the Trash folder.
    """
    affected = _provider(account).delete(
        message_ids=message_ids,
        folder=folder,
        dry_run=dry_run,
    )
    return {
        "dry_run": dry_run,
        "deleted": not dry_run,
        "source_folder": folder,
        "to_trash": True,
        "count": len(affected),
        "emails": [_serialize(asdict(s)) for s in affected],
    }


def _serialize(d: dict[str, Any]) -> dict[str, Any]:
    """JSON-friendly: ISO-format datetimes, rename `from_` → `from`."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = "from" if k == "from_" else k
        if hasattr(v, "isoformat"):
            out[key] = v.isoformat()
        else:
            out[key] = v
    return out


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
