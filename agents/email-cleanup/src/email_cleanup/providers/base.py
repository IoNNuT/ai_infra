"""Provider interface — Gmail and iCloud implement this so the tool layer is provider-agnostic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailSummary:
    """Lightweight view returned by `search` — enough to triage without fetching bodies."""

    id: str
    folder: str
    from_: str
    to: str
    subject: str
    date: datetime | None
    unread: bool
    flagged: bool


@dataclass
class EmailMessage:
    """Full message returned by `get` — body included."""

    id: str
    folder: str
    from_: str
    to: str
    subject: str
    date: datetime | None
    unread: bool
    flagged: bool
    body_text: str
    body_html: str


@dataclass
class FolderInfo:
    """A mailbox folder. `special_use` is the IMAP special-use flag if any (e.g. `\\Trash`)."""

    name: str
    flags: tuple[str, ...]
    special_use: str | None


class EmailProvider(ABC):
    """Provider-agnostic surface. Implementations: Gmail (API), iCloud (IMAP)."""

    @abstractmethod
    def search(
        self,
        query: str | None = None,
        folder: str = "INBOX",
        max_results: int = 20,
    ) -> list[EmailSummary]:
        """Return up to `max_results` summaries in `folder` matching `query`.

        Query syntax is provider-specific for now; the tool layer passes it through.
        """

    @abstractmethod
    def list_folders(self) -> list[FolderInfo]:
        """List the mailbox folders on the account (names usable as `folder`/`dest_folder`)."""

    @abstractmethod
    def get(self, message_id: str, folder: str = "INBOX") -> EmailMessage:
        """Fetch the full message body for `message_id` in `folder`."""

    @abstractmethod
    def move(
        self,
        message_ids: list[str],
        dest_folder: str,
        folder: str = "INBOX",
        dry_run: bool = True,
    ) -> list[EmailSummary]:
        """Move `message_ids` from `folder` to `dest_folder`.

        Returns summaries of the affected messages. When `dry_run` is True nothing is
        moved — the returned summaries are what *would* move. Raises if any id is missing
        from `folder` or if `dest_folder` does not exist, so callers fail before mutating.
        """

    @abstractmethod
    def delete(
        self,
        message_ids: list[str],
        folder: str = "INBOX",
        dry_run: bool = True,
    ) -> list[EmailSummary]:
        """Delete `message_ids` from `folder` by moving them to the account's Trash.

        Recoverable — messages go to Trash, not a permanent expunge. Same contract as
        `move`: returns affected summaries, `dry_run=True` moves nothing, raises (without
        mutating) if any id is missing or `folder` is itself the Trash folder.
        """
