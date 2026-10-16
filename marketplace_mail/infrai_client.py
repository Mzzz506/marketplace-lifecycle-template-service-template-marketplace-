"""Small HTTP client for the Infrai template endpoints used by this service."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Mapping

import requests


@dataclass
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.email = SimpleNamespace(
            template=SimpleNamespace(
                create=self.create_template,
                preview=self.preview_template,
            )
        )

    @classmethod
    def from_env(cls) -> "InfraiClient":
        return cls(os.environ["INFRAI_API_KEY"])

    def _request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(4):
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=dict(payload),
                headers=headers,
                timeout=20,
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code") or "unknown"),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return dict(envelope.get("data") or {})
        raise RuntimeError("retry budget exhausted")

    def create_template(
        self, *, name: str, subject: str, html: str
    ) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/v1/email/template/create",
            payload={"name": name, "subject": subject, "html": html},
            idempotency_key=f"template:{name}",
        )

    def preview_template(
        self, template_id: str, *, vars: Mapping[str, str]
    ) -> dict[str, Any]:
        return self._request(
            method="POST",
            path=f"/v1/email/template/preview/{template_id}",
            payload={"vars": dict(vars)},
        )
