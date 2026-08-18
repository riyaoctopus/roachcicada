"""Local JSONL lead store — the source of truth for this demo regardless of
whether the Zoho push succeeded. Each line is one lead record."""
import json
import time
import uuid

from common import LEADS_PATH, ensure_data_dir


def save_lead(*, name: str, email: str, whatsapp: str, message: str, zoho_result: dict) -> str:
    ensure_data_dir()
    lead_id = str(uuid.uuid4())
    record = {
        "id": lead_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "name": name,
        "email": email,
        "whatsapp": whatsapp,
        "message": message,
        "zoho_status": zoho_result.get("status"),
        "zoho_lead_id": zoho_result.get("lead_id"),
        "zoho_detail": zoho_result.get("detail") or zoho_result.get("reason"),
    }
    with open(LEADS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    return lead_id


def load_lead(lead_id: str) -> dict | None:
    if not LEADS_PATH.exists():
        return None
    with open(LEADS_PATH, "r") as f:
        for line in f:
            record = json.loads(line)
            if record["id"] == lead_id:
                return record
    return None


def load_all_leads() -> list[dict]:
    if not LEADS_PATH.exists():
        return []
    with open(LEADS_PATH, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def rewrite_all(records: list[dict]) -> None:
    ensure_data_dir()
    with open(LEADS_PATH, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
