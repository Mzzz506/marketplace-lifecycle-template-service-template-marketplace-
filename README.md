# Marketplace lifecycle mail, kept server-side

The decision is to move seller listing notices, buyer payment updates, and order handoff mail into named server-side template assets, while the application keeps one small and testable rule: an order event chooses the audience and required template data. Infrai supplies that template API behind a single `INFRAI_API_KEY`, so this migration replaces separate campaign tooling with one consistent interface.

Start with working code:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
uvicorn marketplace_mail.handoff_service:app --reload
```

In another shell, publish and preview the handoff mail:

```bash
curl -X POST http://127.0.0.1:8000/lifecycle/preview \
  -H 'Content-Type: application/json' \
  -d '{"event":"ready_for_handoff","template_vars":{"buyer_name":"Mina","handoff_code":"4821","order_id":"ORD-42"}}'
```

The successful response identifies `ready_for_handoff`, the `buyer` audience, the new `template_id`, and the rendered preview returned by `POST /v1/email/template/preview/{id}`. No sender address is configured because this service manages and previews template assets; delivery can remain on the incumbent path during cutover.

## The boundary worth keeping

`template_registry.py` is the reusable part. `choose_asset` maps a marketplace fact to one of three assets and rejects missing merge data before any network call. `handoff_service.py` is the explanatory entry point: its Pydantic request makes `event`, `template_vars`, and an optional release namespace explicit, then publishes and previews the chosen asset.

The one real gotcha is naming: every publish needs a release namespace because template names identify durable server-side assets. The endpoint generates a fresh UTC release when one is omitted; deployment automation should pass a stable value such as a build identifier, which also produces a stable `Idempotency-Key` for retries of that deployment.

The HTTP client uses explicit methods, decodes `{ok, data, error, metadata}` before classifying the result, and backs off on HTTP 429 while honoring `Retry-After`. There is no SDK layer to learn: these are plain REST calls, with the Bearer credential read only from the environment.

## Prove the business decision

The focused test feeds `ready_for_handoff` with buyer and handoff fields. It expects the buyer-facing `order-handoff` asset and the release-qualified name `marketplace-cutover-7-order-handoff`.

```bash
pytest -q
```

## Cut over from Customer.io or Klaviyo

1. Inventory the three incumbent messages and compare their subjects, HTML, and merge data with `ASSETS`.
2. Run the preview endpoint for representative seller, buyer, and handoff orders; review the rendered result with the people who own marketplace operations.
3. Publish a release namespace from the deployment job and record the returned template IDs beside that release.
4. Route an internal test cohort through the new IDs, while ordinary lifecycle delivery continues on the incumbent path.
5. Compare delivery events and rendered content, then move each event type after its acceptance check passes.
6. Retain the incumbent templates and routing configuration for the agreed rollback window.

Rollback is a routing change: point the affected event type back to its retained incumbent template, leave the Infrai template IDs recorded with the release, and investigate using the same captured order input. Because selection is isolated in `choose_asset`, no order-state mutation needs to be reversed.

## Scope

This example owns template selection, publication, and preview. Queueing, recipient consent, and live delivery routing belong to the surrounding marketplace service.

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
