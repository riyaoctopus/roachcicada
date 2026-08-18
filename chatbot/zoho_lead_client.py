"""
Standalone Zoho lead push for the Roach Cicada chatbot.

Deliberately independent of code/axon-automation — it does NOT import that
package, so this chatbot can be deployed on its own without any risk to the
existing lead-worker codebase. It DOES reuse the exact same contract that
codebase already validated against Zoho (see ../docs/02-BLL-API-REFERENCE.md
and code/axon-automation/services/real_estate_lead_worker.py):

  - The worker never talks to Zoho directly or holds Zoho credentials; it
    calls the gateway's `/v1/zoho/crm/worker/*` BLL. We do the same.
  - Header trio: X-Source-Service: axon-automation, X-Company-ID: <id>,
    Content-Type: application/json  (see `_worker_headers` in the worker).
  - Dedupe first via POST /leads/search {email, phone}, then create via
    POST /leads {"fields": {...}} — same two-step flow the email worker uses,
    so a repeat website visitor doesn't create duplicate Zoho Leads.
  - Field names (Last_Name, First_Name, Phone, Mobile, Email, Lead_Source,
    Description, Tag) match the worker's `_build_lead_fields` conventions.
    Tag must be `[{"name": "..."}]` — a bare string array is rejected by
    Zoho v6 (see doc 08 troubleshooting notes).

Reachability note: `GATEWAY_URL` defaults to the same internal Docker DNS
name the worker uses (`http://axon-gateway-v2-dev:9200`), which is only
reachable from inside the `axonbos-v2-dev` network — not from a laptop
running this demo locally. That's expected. Every lead is persisted locally
first (source of truth for this demo); the Zoho push is best-effort and
failures never block the buyer's chat experience. Once this chatbot is
deployed on the same network as the gateway (or GATEWAY_URL is pointed at a
reachable address, e.g. via SSH tunnel), the push will start succeeding
without any code change — see sync_pending_leads.py to retry anything
queued while offline.
"""
import json
import time
from typing import Any

import httpx

from common import (
    GATEWAY_URL,
    ZOHO_COMPANY_ID,
    ZOHO_LEAD_SOURCE,
    ZOHO_SOURCE_SERVICE_HEADER,
)

TIMEOUT_SECONDS = 6.0


def _worker_headers(company_id: int) -> dict[str, str]:
    return {
        "X-Source-Service": ZOHO_SOURCE_SERVICE_HEADER,
        "X-Company-ID": str(company_id),
        "Content-Type": "application/json",
    }


def _split_name(full_name: str) -> tuple[str, str | None]:
    parts = full_name.strip().split()
    if not parts:
        return "Website Enquiry", None
    if len(parts) == 1:
        return parts[0], None
    return parts[-1], " ".join(parts[:-1])


def _build_fields(*, name: str, email: str, whatsapp: str, message: str) -> dict[str, Any]:
    last_name, first_name = _split_name(name)
    description_lines = [
        "Source: Roach Cicada website chatbot (roachcicada.co)",
        f"WhatsApp: {whatsapp}",
    ]
    if message:
        description_lines.append(f"\nBuyer message:\n{message}")
    fields: dict[str, Any] = {
        "Last_Name": last_name,
        "Lead_Source": ZOHO_LEAD_SOURCE,
        "Description": "\n".join(description_lines),
        "Phone": whatsapp,
        "Mobile": whatsapp,
        "Email": email,
        # Zoho v6 Tag.name has a 25-char max (probed live: INVALID_DATA on
        # "roachcicada:website-chatbot", 27 chars) — keep this short.
        "Tag": [{"name": "roachcicada:website"}],
    }
    if first_name:
        fields["First_Name"] = first_name
    return fields


def search_existing_lead(client: httpx.Client, *, email: str, phone: str) -> str | None:
    """Mirrors _zoho_search_leads. Returns an existing lead_id or None."""
    url = f"{GATEWAY_URL}/v1/zoho/crm/worker/leads/search"
    resp = client.post(
        url,
        headers=_worker_headers(ZOHO_COMPANY_ID),
        json={"email": email or "", "phone": phone or "", "limit": 5},
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    envelope = resp.json()
    if not envelope.get("success"):
        return None
    leads = (envelope.get("data") or {}).get("leads") or []
    return leads[0]["id"] if leads else None


def append_note(client: httpx.Client, *, lead_id: str, title: str, content: str) -> str | None:
    url = f"{GATEWAY_URL}/v1/zoho/crm/worker/leads/{lead_id}/notes"
    resp = client.post(
        url,
        headers=_worker_headers(ZOHO_COMPANY_ID),
        json={"title": title, "content": content},
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    envelope = resp.json()
    if not envelope.get("success"):
        return None
    return (envelope.get("data") or {}).get("note_id")


def create_lead(client: httpx.Client, fields: dict[str, Any]) -> dict[str, Any]:
    url = f"{GATEWAY_URL}/v1/zoho/crm/worker/leads"
    resp = client.post(
        url,
        headers=_worker_headers(ZOHO_COMPANY_ID),
        json={"fields": fields},
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()


def push_lead_to_zoho(*, name: str, email: str, whatsapp: str, message: str) -> dict[str, Any]:
    """
    Best-effort push. Never raises — always returns a status dict so the
    caller (server.py) can persist the outcome and continue regardless.
    """
    fields = _build_fields(name=name, email=email, whatsapp=whatsapp, message=message)
    try:
        with httpx.Client() as client:
            existing_id = search_existing_lead(client, email=email, phone=whatsapp)
            if existing_id:
                note_id = append_note(
                    client,
                    lead_id=existing_id,
                    title=f"Website chatbot enquiry — {time.strftime('%Y-%m-%d %H:%M')}",
                    content=fields["Description"],
                )
                return {
                    "status": "noted_existing",
                    "lead_id": existing_id,
                    "note_id": note_id,
                }

            result = create_lead(client, fields)
            data = result.get("data") or {}
            if data.get("ok"):
                return {"status": "created", "lead_id": data.get("lead_id")}
            if data.get("error_code") == "DUPLICATE_DATA" and data.get("duplicate_record_id"):
                dup_id = data["duplicate_record_id"]
                note_id = append_note(
                    client,
                    lead_id=dup_id,
                    title=f"Website chatbot enquiry — {time.strftime('%Y-%m-%d %H:%M')}",
                    content=fields["Description"],
                )
                return {"status": "noted_existing", "lead_id": dup_id, "note_id": note_id}
            return {"status": "zoho_rejected", "detail": data}
    except Exception as exc:  # network unreachable, timeout, gateway down, etc.
        return {"status": "queued_offline", "reason": str(exc)}
