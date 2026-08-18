# Roach Cicada — Sales Chat Demo (local RAG)

A local, working demo of a real-estate sales assistant for **Roach Cicada**, aimed at HNI and NRI
buyers. Visitors submit a name/email/WhatsApp lead-capture form (with explicit consent) before the
chat unlocks; the lead is pushed to Zoho CRM through the existing octopus-automations gateway
contract, and every chat reply is grounded in the property knowledge base in the parent `RoachCicada/`
folder — including surfacing real photos and videos inline when relevant.

This is intentionally **independent of `code/axon-automation`** — it doesn't import that package or
touch its files, so it can be built, run, and deployed on its own without any risk to the existing
lead-worker pipeline. It does *reuse* the same Zoho gateway contract (endpoints, headers, field names)
that pipeline already validated — see `zoho_lead_client.py` for exactly what's reused and why.

## What's in here

| File | Purpose |
|---|---|
| `build_index.py` | One-time (or re-run-on-change) script: chunks the `../*.md` knowledge base and embeds each chunk with OpenAI, writing `index/chunks.json`. |
| `retrieval.py` | In-memory cosine-similarity search over the embedded chunks (numpy — no vector DB needed at this scale). |
| `server.py` | FastAPI app: `POST /api/lead`, `POST /api/chat`, serves the frontend and `/assets` (photos/videos). |
| `zoho_lead_client.py` | Standalone Zoho CRM push, reusing the `axon-gateway` `/v1/zoho/crm/worker/*` contract documented in `../../docs/02-BLL-API-REFERENCE.md`. Best-effort — never blocks the chat if the gateway is unreachable. |
| `leads_store.py` | Local JSONL lead log (`data/leads.jsonl`) — the source of truth for this demo regardless of Zoho reachability. |
| `sync_pending_leads.py` | Retries any leads that couldn't reach Zoho yet. Run this once the gateway is actually reachable. |
| `common.py` | Shared config: API key loading, model names, Zoho gateway settings. |
| `static/index.html` | The whole frontend — lead-gate form + chat UI, vanilla HTML/CSS/JS, no build step. |

## Running it

```bash
cd RoachCicada/chatbot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# One-time: build the embedding index (re-run any time the ../*.md docs change)
python build_index.py

# Start the server
uvicorn server:app --reload --port 8420
```

Then open **http://localhost:8420** in a browser.

The OpenAI API key is read from `OPENAI_API_KEY` if set, otherwise from `../.secrets/openaiapi.txt`
(already present and gitignored — see the parent repo's `.gitignore`, which already excludes
`.secrets/`).

## The Zoho CRM integration — what to expect locally vs. in production

The lead form always saves to `data/leads.jsonl` first, then **best-effort** pushes to Zoho via the
gateway. `GATEWAY_URL` defaults to `http://axon-gateway-v2-dev:9200` — the same internal Docker DNS
name the email lead-worker uses — which is **only reachable from inside the `axonbos-v2-dev` Docker
network**, not from a laptop running this demo. That means:

- **Running locally (this demo):** every lead push will fail with a connection error, and the lead is
  recorded locally with `zoho_status: "queued_offline"`. This is expected — the chat still unlocks
  immediately regardless, so the demo isn't blocked by network reachability.
- **Once deployed** on the same network as `axon-gateway-v2-dev` (or with `GATEWAY_URL` pointed at a
  reachable address, e.g. via an SSH tunnel), the push will start succeeding with no code change.
  Retry anything that was queued while offline:
  ```bash
  GATEWAY_URL=http://localhost:9200 python sync_pending_leads.py
  ```

### Before relying on this in production

1. **Validate `Lead_Source`.** It defaults to `"Website"` (env: `ZOHO_LEAD_SOURCE`) — a common Zoho
   built-in value, but it has **not** been confirmed against Octopus's actual configured picklist for
   `company_id=29`. Check it the same way doc 07 recommends for onboarding a new source:
   ```
   GET /v1/zoho/crm/worker/picklist/Leads/Lead_Source
   ```
   and update `ZOHO_LEAD_SOURCE` (or the code) to match a real picklist value before going live.
2. **Confirm `ZOHO_COMPANY_ID=29` is intentional.** This reuses Octopus Estates' Zoho org because
   that's the tenant octopus-automations already has gateway access to — confirm that's where Roach
   Cicada leads should land, or point `ZOHO_COMPANY_ID` at a different tenant's config once one exists
   (see `real_estate_lead_config` in the main docs — multi-tenant Zoho is explicitly *not yet done*
   per doc 07).
3. This demo keeps chat history and buyer name **in server memory only** (`SESSIONS` dict in
   `server.py`) — it resets on server restart. Fine for a demo; would need a real session store
   (Redis/DB) for production.

## Env vars

| Var | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | (reads `../.secrets/openaiapi.txt`) | OpenAI auth |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for retrieval |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model for replies |
| `GATEWAY_URL` | `http://axon-gateway-v2-dev:9200` | axon-gateway BLL base URL |
| `ZOHO_COMPANY_ID` | `29` | `X-Company-ID` header (Octopus Estates tenant) |
| `ZOHO_LEAD_SOURCE` | `Website` | `Lead_Source` field value — validate before production use |

## Design notes

- **Retrieval, not fine-tuning:** every reply is grounded in retrieved chunks from the markdown docs,
  passed to the model as context in the system prompt. The persona prompt explicitly forbids inventing
  prices, dates, or facts not present in the retrieved context.
- **Images/videos are retrieved, not generated or guessed:** each markdown chunk was indexed together
  with any `assets/...` file paths mentioned in its text (see `common.extract_media_paths`). When a
  chunk is retrieved as relevant context, its associated media paths are returned to the frontend and
  rendered inline — the model itself never has to (and is told not to) print raw file paths.
- **No investment/tax advice:** the system prompt explicitly restricts the assistant from giving
  personalized financial, tax, or legal advice (relevant for NRI buyers asking about repatriation,
  TDS, currency conversion, etc.) and instructs it to suggest consulting a professional instead.
