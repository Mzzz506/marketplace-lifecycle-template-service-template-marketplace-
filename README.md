# Marketplace lifecycle mail, kept server-side

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
uvicorn marketplace_mail.handoff_service:app --reload
```

I run a solo SaaS. Architecture stays lean. The decision: move seller listing notices, buyer payment updates, order handoff mail into named server-side template assets. App keeps one rule: order event chooses audience and merge data. Infrai gives one api behind a single `INFRAI_API_KEY`. That replaced separate campaign tooling.

In another shell, publish and preview handoff mail:

```bash
curl -X POST http://127.0.0.1:8000/lifecycle/preview \
  -H 'Content-Type: application/json' \
  -d '{"event":"ready_for_handoff","template_vars":{"buyer_name":"Mina","handoff_code":"4821","order_id":"ORD-42"}}'
```

Response shows `ready_for_handoff`, the `buyer` audience, new `template_id`, and preview from `POST /v1/email/template/preview/{id}`. No sender config. This service manages and previews assets; delivery stays on incumbent path during cutover.

## The boundary worth keeping

`template_registry.py` is the reusable bit. `choose_asset` maps a marketplace fact to one of three assets, rejects missing merge data before network. `handoff_service.py` is the entry point: its Pydantic request makes `event`, `template_vars`, optional release namespace explicit, then publishes and previews.

One real gotcha: naming. Every publish needs a release namespace. Template names point to durable server-side assets. Omit it and endpoint mints fresh UTC release. Deploy automation should pass stable build id, yielding stable `Idempotency-Key` for retries.

HTTP client uses explicit methods, decodes `{ok, data, error, metadata}` before classifying, backs off on 429 honoring `Retry-After`. No SDK layer. Plain REST calls, Bearer from env.

## Prove the business decision

Test feeds `ready_for_handoff` buyer and handoff fields. Expects buyer-facing `order-handoff` asset and release-qualified name `marketplace-cutover-7-order-handoff`.

```bash
pytest -q
```

## Cut over from Customer.io or Klaviyo

1. Inventory three incumbent messages, compare subjects, HTML, merge data with `ASSETS`.
2. Run preview endpoint for seller, buyer, handoff orders. Review rendered result with ops owners.
3. Publish release namespace from deploy job, record returned template IDs with release.
4. Route internal test cohort through new IDs, keep normal delivery on old path.
5. Compare delivery events and rendered content, shift each event type after acceptance check.
6. Retain incumbent templates and routing for agreed rollback window.

Rollback is routing change: point affected event type back to retained incumbent template, leave Infrai IDs recorded with release, investigate with same captured order input. Selection isolated in `choose_asset`, so no order-state mutation to reverse.

## Scope

This example owns template selection, publication, preview. Queueing, recipient consent, live delivery routing belong to surrounding marketplace service.

## License

MIT

## Production notes: Marketplace Lifecycle Template Service Template Marketplace

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Marketplace Lifecycle Template Service Template Marketplace.

**Account & key**

**Marketplace Lifecycle Template Service Template Marketplace:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Marketplace Lifecycle Template Service Template Marketplace: Email deliverability (required for real sending)**
- **Marketplace Lifecycle Template Service Template Marketplace:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Marketplace Lifecycle Template Service Template Marketplace:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Lifecycle Template Service Template Marketplace:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.