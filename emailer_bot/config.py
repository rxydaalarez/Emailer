from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List



@dataclass(frozen=True)
class IMAPConfig:
    host: str
    port: int
    username: str
    password: str
    folder: str = "INBOX"


@dataclass(frozen=True)
class OneDriveConfig:
    access_token: str
    drive_id: str
    folder_path: str
    max_files: int = 25


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str


@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    subject_prefix: str = "[Investment Alert]"


@dataclass(frozen=True)
class Recipient:
    name: str
    email: str


@dataclass(frozen=True)
class AppConfig:
    investment_keyword: str
    poll_interval_seconds: int
    imap: IMAPConfig
    onedrive: OneDriveConfig
    openai: OpenAIConfig
    smtp: SMTPConfig
    recipients: List[Recipient]


def load_config(path: str | Path) -> AppConfig:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    recipients = [Recipient(**r) for r in raw["recipients"]]
    return AppConfig(
        investment_keyword=raw["investment_keyword"],
        poll_interval_seconds=raw.get("poll_interval_seconds", 30),
        imap=IMAPConfig(**raw["imap"]),
        onedrive=OneDriveConfig(**raw["onedrive"]),
        openai=OpenAIConfig(**raw["openai"]),
        smtp=SMTPConfig(**raw["smtp"]),
        recipients=recipients,
    )
