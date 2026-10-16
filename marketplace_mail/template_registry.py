"""Marketplace lifecycle decisions and their server-side template assets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence


class OrderEvent(str, Enum):
    LISTING_PUBLISHED = "listing_published"
    PAYMENT_CONFIRMED = "payment_confirmed"
    READY_FOR_HANDOFF = "ready_for_handoff"


@dataclass(frozen=True)
class TemplateAsset:
    key: str
    audience: str
    subject: str
    html: str
    required_vars: Sequence[str]


ASSETS = {
    OrderEvent.LISTING_PUBLISHED: TemplateAsset(
        key="seller-asset-live",
        audience="seller",
        subject="{{item_name}} is live in the marketplace",
        html="<h1>Your listing is live</h1><p>{{seller_name}}, {{item_name}} is ready for buyers.</p>",
        required_vars=("seller_name", "item_name"),
    ),
    OrderEvent.PAYMENT_CONFIRMED: TemplateAsset(
        key="buyer-payment-update",
        audience="buyer",
        subject="Payment confirmed for order {{order_id}}",
        html="<h1>Payment confirmed</h1><p>{{buyer_name}}, the seller is preparing {{item_name}}.</p>",
        required_vars=("buyer_name", "item_name", "order_id"),
    ),
    OrderEvent.READY_FOR_HANDOFF: TemplateAsset(
        key="order-handoff",
        audience="buyer",
        subject="Order {{order_id}} is ready for handoff",
        html="<h1>Ready for handoff</h1><p>{{buyer_name}}, use handoff code {{handoff_code}}.</p>",
        required_vars=("buyer_name", "handoff_code", "order_id"),
    ),
}


def choose_asset(event: OrderEvent, template_vars: dict[str, str]) -> TemplateAsset:
    asset = ASSETS[event]
    missing = [name for name in asset.required_vars if not template_vars.get(name)]
    if missing:
        raise ValueError(f"missing template_vars: {', '.join(missing)}")
    return asset


def publish_asset(infrai: Any, asset: TemplateAsset, release: str) -> str:
    name = f"marketplace-{release}-{asset.key}"
    data = infrai.email.template.create(
        name=name,
        subject=asset.subject,
        html=asset.html,
    )
    return str(data["template_id"])


def publish_catalog(infrai: Any, release: str) -> dict[OrderEvent, str]:
    return {
        event: publish_asset(infrai, asset, release) for event, asset in ASSETS.items()
    }
