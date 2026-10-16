from types import SimpleNamespace

from marketplace_mail.infrai_client import InfraiClient
from marketplace_mail.template_registry import OrderEvent, choose_asset, publish_asset


class RecordingAPI:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.email = SimpleNamespace(
            template=SimpleNamespace(create=self.create_template)
        )

    def create_template(self, **payload: str) -> dict:
        self.created.append(payload)
        return {"template_id": "tpl_handoff_42"}


def test_handoff_event_selects_buyer_asset_and_stable_write_key() -> None:
    values = {
        "buyer_name": "Mina",
        "handoff_code": "4821",
        "order_id": "ORD-42",
    }
    asset = choose_asset(OrderEvent.READY_FOR_HANDOFF, values)
    api = RecordingAPI()

    template_id = publish_asset(api, asset, release="cutover-7")

    assert asset.audience == "buyer"
    assert asset.key == "order-handoff"
    assert template_id == "tpl_handoff_42"
    assert api.created[0]["name"] == "marketplace-cutover-7-order-handoff"


def test_preview_sends_template_vars(monkeypatch) -> None:
    recorded: dict = {}

    def record_request(**kwargs) -> dict:
        recorded.update(kwargs)
        return SimpleNamespace(
            json=lambda: {"ok": True, "data": {"html": "Hello Mina"}},
            status_code=200,
            headers={},
        )

    monkeypatch.setattr("marketplace_mail.infrai_client.requests.request", record_request)
    client = InfraiClient("test-key")

    result = client.email.template.preview(
        "tpl_handoff_42", vars={"buyer_name": "Mina"}
    )

    assert result == {"html": "Hello Mina"}
    assert recorded["json"] == {"vars": {"buyer_name": "Mina"}}
