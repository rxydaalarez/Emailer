from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from .auth import generate_oauth2_string
from .config import Recipient, SMTPConfig


class Notifier:
    def __init__(self, config: SMTPConfig):
        self.config = config
        self.access_token = config.password if getattr(config, "auth_method", "password") == "oauth" else None

    def update_token(self, token: str) -> None:
        self.access_token = token

    def send(
        self,
        recipients: Iterable[Recipient],
        subject: str,
        body: str,
        graph_path: Path | None = None,
    ) -> None:
        msg = EmailMessage()
        msg["From"] = self.config.from_email
        msg["To"] = ", ".join([r.email for r in recipients])
        msg["Subject"] = f"{self.config.subject_prefix} {subject}".strip()
        msg.set_content(body)

        if graph_path and graph_path.exists():
            with open(graph_path, "rb") as f:
                data = f.read()
            msg.add_attachment(
                data,
                maintype="image",
                subtype="png",
                filename=graph_path.name,
            )

        with smtplib.SMTP(self.config.host, self.config.port) as server:
            server.starttls()
            if getattr(self.config, "auth_method", "password") == "oauth":
                token = self.access_token or self.config.password
                auth_str = generate_oauth2_string(self.config.username, token)
                server.auth("XOAUTH2", lambda x: auth_str)
            else:
                server.login(self.config.username, self.config.password)
            server.send_message(msg)
