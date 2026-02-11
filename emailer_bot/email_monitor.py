from __future__ import annotations

import email
import imaplib
import re
from dataclasses import dataclass
from email.message import Message
from typing import Iterable, List

from .config import IMAPConfig


@dataclass
class IncomingEmail:
    uid: str
    subject: str
    from_email: str
    body: str


class EmailMonitor:
    def __init__(self, config: IMAPConfig):
        self.config = config

    def fetch_unseen(self) -> List[IncomingEmail]:
        mails: list[IncomingEmail] = []
        with imaplib.IMAP4_SSL(self.config.host, self.config.port) as client:
            client.login(self.config.username, self.config.password)
            client.select(self.config.folder)

            status, data = client.uid("search", None, "UNSEEN")
            if status != "OK":
                return mails

            for uid in data[0].decode().split():
                f_status, raw = client.uid("fetch", uid, "(BODY.PEEK[])")
                if f_status != "OK" or not raw or not raw[0]:
                    continue
                msg = email.message_from_bytes(raw[0][1])
                mails.append(self._parse_message(uid, msg))

        return mails

    def mark_as_read(self, uid: str) -> None:
        with imaplib.IMAP4_SSL(self.config.host, self.config.port) as client:
            client.login(self.config.username, self.config.password)
            client.select(self.config.folder)
            client.uid("store", uid, "+FLAGS", "\\Seen")

    def has_keyword(self, email_item: IncomingEmail, keyword: str) -> bool:
        pattern = rf"\b{re.escape(keyword)}\b"
        return bool(re.search(pattern, f"{email_item.subject}\n{email_item.body}", re.IGNORECASE))

    @staticmethod
    def _parse_message(uid: str, msg: Message) -> IncomingEmail:
        subject = msg.get("Subject", "")
        from_email = msg.get("From", "")
        body = "\n".join(_extract_text_parts(msg))
        return IncomingEmail(uid=uid, subject=subject, from_email=from_email, body=body)


def _extract_text_parts(msg: Message) -> Iterable[str]:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True) or b""
                yield payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True) or b""
        yield payload.decode(errors="ignore")
