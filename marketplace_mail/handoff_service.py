"""Typed FastAPI boundary for selecting, publishing, and previewing lifecycle mail."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infrai_client import InfraiClient, InfraiError
from .template_registry import OrderEvent, choose_asset, publish_asset


class PreviewRequest(BaseModel):
    event: OrderEvent
    template_vars: dict[str, str] = Field(min_length=1)
    release: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$")


class PreviewResult(BaseModel):
    event: OrderEvent
    audience: str
    template_id: str
    preview: dict


app = FastAPI(title="Marketplace lifecycle template service")


@app.post("/lifecycle/preview", response_model=PreviewResult)
def preview_lifecycle_mail(request: PreviewRequest) -> PreviewResult:
    try:
        asset = choose_asset(request.event, request.template_vars)
        release = request.release or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        infrai = InfraiClient.from_env()
        template_id = publish_asset(infrai, asset, release)
        preview = infrai.email.template.preview(template_id, vars=request.template_vars)
        return PreviewResult(
            event=request.event,
            audience=asset.audience,
            template_id=template_id,
            preview=preview,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=error.detail) from error
