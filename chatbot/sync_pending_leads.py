"""
Retries any locally-queued leads whose Zoho push previously failed
(status "queued_offline" or "zoho_rejected").

Run this once the gateway is actually reachable — e.g. after deploying this
chatbot onto the axonbos-v2-dev Docker network, or via an SSH tunnel:

    ssh -L 9200:axon-gateway-v2-dev:9200 ubuntu@<server> -N &
    GATEWAY_URL=http://localhost:9200 python sync_pending_leads.py

Usage: python sync_pending_leads.py
"""
from leads_store import load_all_leads, rewrite_all
from zoho_lead_client import push_lead_to_zoho


def main():
    records = load_all_leads()
    if not records:
        print("No leads on file.")
        return

    pending = [r for r in records if r.get("zoho_status") not in ("created", "noted_existing")]
    print(f"{len(records)} total leads, {len(pending)} pending Zoho push.")

    for record in pending:
        result = push_lead_to_zoho(
            name=record["name"],
            email=record["email"],
            whatsapp=record["whatsapp"],
            message=record.get("message", ""),
        )
        record["zoho_status"] = result.get("status")
        record["zoho_lead_id"] = result.get("lead_id")
        record["zoho_detail"] = result.get("detail") or result.get("reason")
        print(f"  {record['name']} <{record['email']}> -> {result.get('status')}")

    rewrite_all(records)
    print("Done.")


if __name__ == "__main__":
    main()
