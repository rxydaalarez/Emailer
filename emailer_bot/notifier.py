from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from .config import Recipient, SMTPConfig


class Notifier:
    def __init__(self, config: SMTPConfig):
        self.config = config

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
            server.login(self.config.username, self.config.password)
            server.send_message(msg)
