from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import aiosmtplib
from pydantic import BaseModel, EmailStr

from ..utils.api_client import AsyncApiClient
from ..utils.error_handler import ValidationError, require
from ..utils.logger import get_logger


logger = get_logger(__name__)


class EmailPayload(BaseModel):
    to: EmailStr
    subject: str
    html: str
    text: Optional[str] = None


class EmailAgent:
    def __init__(self, config: Dict[str, Any]):
        self.provider = config.get("provider", "sendgrid").lower()
        self.from_email = config["from_email"]
        self.default_confirmation_recipient = config.get("default_confirmation_recipient")
        self._sendgrid_key = config.get("sendgrid", {}).get("api_key")
        self._resend_key = config.get("resend", {}).get("api_key")
        self._smtp = config.get("smtp", {})
        self._http_client: Optional[AsyncApiClient] = None

        if self.provider == "sendgrid":
            require(self._sendgrid_key, "SendGrid API key required for sendgrid provider")
            self._http_client = AsyncApiClient(
                base_url="https://api.sendgrid.com/v3",
                default_headers={
                    "Authorization": f"Bearer {self._sendgrid_key}",
                    "Content-Type": "application/json",
                },
            )
        elif self.provider == "resend":
            require(self._resend_key, "Resend API key required for resend provider")
            self._http_client = AsyncApiClient(
                base_url="https://api.resend.com",
                default_headers={
                    "Authorization": f"Bearer {self._resend_key}",
                    "Content-Type": "application/json",
                },
            )
        elif self.provider == "smtp":
            require(self._smtp.get("host"), "SMTP host required for smtp provider")
        else:
            raise ValidationError(f"Unsupported email provider {self.provider}")

    async def send(self, payload: EmailPayload) -> Dict[str, Any]:
        if self.provider == "sendgrid":
            body = {
                "personalizations": [
                    {"to": [{"email": str(payload.to)}]}
                ],
                "from": {"email": self.from_email},
                "subject": payload.subject,
                "content": [
                    {"type": "text/plain", "value": payload.text or ""},
                    {"type": "text/html", "value": payload.html},
                ],
            }
            res = await self._http_client.post("/mail/send", json=body)  # type: ignore[union-attr]
            # SendGrid returns 202 with no body on success
            return {"status": "queued", "provider": "sendgrid", "response": res}
        elif self.provider == "resend":
            body = {
                "from": self.from_email,
                "to": [str(payload.to)],
                "subject": payload.subject,
                "html": payload.html,
            }
            if payload.text:
                body["text"] = payload.text
            res = await self._http_client.post("/emails", json=body)  # type: ignore[union-attr]
            return {"status": "queued", "provider": "resend", "response": res}
        else:
            # SMTP
            message = (f"From: {self.from_email}\r\n"
                       f"To: {payload.to}\r\n"
                       f"Subject: {payload.subject}\r\n"
                       f"MIME-Version: 1.0\r\n"
                       f"Content-Type: text/html; charset=utf-8\r\n\r\n"
                       f"{payload.html}")
            host = self._smtp.get("host")
            port = int(self._smtp.get("port", 587))
            username = self._smtp.get("username")
            password = self._smtp.get("password")
            use_tls = bool(self._smtp.get("use_tls", True))

            if use_tls:
                await aiosmtplib.send(
                    message,
                    hostname=host,
                    port=port,
                    start_tls=True,
                    username=username,
                    password=password,
                    sender=self.from_email,
                    recipients=[str(payload.to)],
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=host,
                    port=port,
                    start_tls=False,
                    username=username,
                    password=password,
                    sender=self.from_email,
                    recipients=[str(payload.to)],
                )
            return {"status": "sent", "provider": "smtp"}

    async def send_confirmation(self, to_email: Optional[str], summary_html: str, subject: Optional[str] = None) -> Dict[str, Any]:
        recipient = to_email or self.default_confirmation_recipient
        require(recipient is not None, "No recipient email provided or configured for confirmation")
        subject_final = subject or "CRM Action Confirmation"
        return await self.send(EmailPayload(to=recipient, subject=subject_final, html=summary_html))

    async def aclose(self) -> None:
        if self._http_client:
            await self._http_client.close()
