"""iCloud Mail provider — IMAP against imap.mail.me.com:993 with an app-specific password.

App-specific password is generated at https://appleid.apple.com → Sign-In and Security →
App-Specific Passwords. iCloud blocks regular account passwords for IMAP.
"""

from __future__ import annotations

import os

from imap_tools import AND, MailBox, MailMessage

from email_cleanup.providers.base import (
    EmailMessage,
    EmailProvider,
    EmailSummary,
    FolderInfo,
)

# IMAP special-use flags that mark well-known folders (RFC 6154).
_SPECIAL_USE = frozenset({r"\All", r"\Archive", r"\Drafts", r"\Flagged", r"\Junk", r"\Sent", r"\Trash"})

ICLOUD_HOST = "imap.mail.me.com"
ICLOUD_PORT = 993


class ICloudProvider(EmailProvider):
    """iCloud IMAP provider. Reads via `search`/`get`; mutates via `move`."""

    def __init__(self, email: str | None = None, app_password: str | None = None) -> None:
        self._email = email or os.environ.get("ICLOUD_EMAIL")
        self._app_password = app_password or os.environ.get("ICLOUD_APP_PASSWORD")
        if not self._email or not self._app_password:
            raise RuntimeError(
                "iCloud credentials missing — set ICLOUD_EMAIL and ICLOUD_APP_PASSWORD "
                "(app-specific password from appleid.apple.com) in the MCP server env."
            )

    def _connect(self, folder: str) -> MailBox:
        box = MailBox(ICLOUD_HOST, port=ICLOUD_PORT)
        box.login(self._email, self._app_password, initial_folder=folder)
        return box

    def search(
        self,
        query: str | None = None,
        folder: str = "INBOX",
        max_results: int = 20,
    ) -> list[EmailSummary]:
        criteria = query if query else AND(all=True)
        with self._connect(folder) as box:
            results: list[EmailSummary] = []
            for msg in box.fetch(
                criteria,
                limit=max_results,
                reverse=True,
                mark_seen=False,
                bulk=True,
                headers_only=True,
            ):
                results.append(_to_summary(msg, folder))
            return results

    def list_folders(self) -> list[FolderInfo]:
        with self._connect("INBOX") as box:
            return [
                FolderInfo(
                    name=f.name,
                    flags=tuple(f.flags),
                    special_use=next((fl for fl in f.flags if fl in _SPECIAL_USE), None),
                )
                for f in box.folder.list()
            ]

    def get(self, message_id: str, folder: str = "INBOX") -> EmailMessage:
        with self._connect(folder) as box:
            for msg in box.fetch(
                AND(uid=message_id),
                limit=1,
                mark_seen=False,
                bulk=False,
            ):
                return _to_message(msg, folder)
        raise LookupError(f"iCloud message uid={message_id} not found in folder={folder}")

    def move(
        self,
        message_ids: list[str],
        dest_folder: str,
        folder: str = "INBOX",
        dry_run: bool = True,
    ) -> list[EmailSummary]:
        if not message_ids:
            return []
        with self._connect(folder) as box:
            if not box.folder.exists(dest_folder):
                raise LookupError(
                    f"iCloud destination folder {dest_folder!r} does not exist — "
                    "create it first or check the exact name (folders are case-sensitive)."
                )
            found: dict[str, EmailSummary] = {}
            for msg in box.fetch(
                AND(uid=message_ids),
                mark_seen=False,
                bulk=True,
                headers_only=True,
            ):
                if msg.uid:
                    found[msg.uid] = _to_summary(msg, folder)
            missing = [uid for uid in message_ids if uid not in found]
            if missing:
                raise LookupError(
                    f"iCloud message uid(s) {missing} not found in folder={folder} — nothing moved."
                )
            if not dry_run:
                box.move(list(found), dest_folder)
            return list(found.values())

    def delete(
        self,
        message_ids: list[str],
        folder: str = "INBOX",
        dry_run: bool = True,
    ) -> list[EmailSummary]:
        if not message_ids:
            return []
        trash = self._trash_folder()
        if folder == trash:
            raise ValueError(
                f"folder {folder!r} is already the Trash folder — refusing to 'delete' "
                "within Trash (would be a no-op or a permanent purge)."
            )
        return self.move(message_ids, dest_folder=trash, folder=folder, dry_run=dry_run)

    def _trash_folder(self) -> str:
        """Resolve the Trash folder name via its IMAP `\\Trash` special-use flag.

        Falls back to iCloud's conventional name if the server doesn't advertise the flag.
        """
        for f in self.list_folders():
            if f.special_use == r"\Trash":
                return f.name
        return "Deleted Messages"


def _to_summary(msg: MailMessage, folder: str) -> EmailSummary:
    return EmailSummary(
        id=msg.uid or "",
        folder=folder,
        from_=msg.from_ or "",
        to=", ".join(msg.to) if msg.to else "",
        subject=msg.subject or "",
        date=msg.date,
        unread=r"\Seen" not in (msg.flags or ()),
        flagged=r"\Flagged" in (msg.flags or ()),
    )


def _to_message(msg: MailMessage, folder: str) -> EmailMessage:
    return EmailMessage(
        id=msg.uid or "",
        folder=folder,
        from_=msg.from_ or "",
        to=", ".join(msg.to) if msg.to else "",
        subject=msg.subject or "",
        date=msg.date,
        unread=r"\Seen" not in (msg.flags or ()),
        flagged=r"\Flagged" in (msg.flags or ()),
        body_text=msg.text or "",
        body_html=msg.html or "",
    )
