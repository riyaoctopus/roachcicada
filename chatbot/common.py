import os
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # RoachCicada/
CHATBOT_DIR = Path(__file__).resolve().parent  # RoachCicada/chatbot/
INDEX_PATH = CHATBOT_DIR / "index" / "chunks.json"
DATA_DIR = CHATBOT_DIR / "data"
LEADS_PATH = DATA_DIR / "leads.jsonl"

EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# --- Zoho lead push, reusing the octopus-automations gateway BLL contract ---
# See ../docs/02-BLL-API-REFERENCE.md and code/axon-automation/services/real_estate_lead_worker.py
# (_worker_headers, POST /v1/zoho/crm/worker/leads). This chatbot never talks to Zoho
# directly and never holds Zoho credentials — same rule as the email worker.
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://axon-gateway-v2-dev:9200")
ZOHO_COMPANY_ID = int(os.environ.get("ZOHO_COMPANY_ID", "29"))
ZOHO_LEAD_SOURCE = os.environ.get("ZOHO_LEAD_SOURCE", "Octopus Website")
ZOHO_SOURCE_SERVICE_HEADER = "axon-automation"

MEDIA_EXT_PATTERN = re.compile(
    r"assets/[A-Za-z0-9_\-./]+\.(?:png|jpe?g|webp|avif|mp4)", re.IGNORECASE
)


def load_api_key() -> str:
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key.strip()
    secret_file = ROOT / ".secrets" / "openaiapi.txt"
    if secret_file.exists():
        return secret_file.read_text().strip()
    raise RuntimeError(
        "No OpenAI API key found. Set OPENAI_API_KEY or put one in RoachCicada/.secrets/openaiapi.txt"
    )


def extract_media_paths(text: str):
    paths = MEDIA_EXT_PATTERN.findall if False else None
    matches = MEDIA_EXT_PATTERN.finditer(text)
    images, videos = [], []
    seen = set()
    for m in matches:
        p = m.group(0)
        if p in seen:
            continue
        seen.add(p)
        if p.lower().endswith(".mp4"):
            videos.append(p)
        else:
            images.append(p)
    return images, videos


def load_chunks():
    with open(INDEX_PATH, "r") as f:
        return json.load(f)


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
