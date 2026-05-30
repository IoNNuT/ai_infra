"""Email provider implementations behind a common interface."""

from email_cleanup.providers.base import EmailMessage, EmailProvider, EmailSummary

__all__ = ["EmailMessage", "EmailProvider", "EmailSummary"]
