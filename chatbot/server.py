"""
Roach Cicada — local RAG sales-chat demo.

Flow: buyer fills the lead form (name/email/WhatsApp/message) -> lead is
persisted locally and best-effort pushed to Zoho CRM via the existing
octopus-automations gateway contract -> chat unlocks -> every reply is
grounded in the RoachCicada/*.md knowledge base via embedding retrieval,
with relevant images/videos surfaced alongside the text.

Run: uvicorn server:app --reload --port 8420
"""
import re
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

from common import ROOT, CHAT_MODEL, EMBEDDING_MODEL, load_api_key
from retrieval import Retriever
import leads_store
from zoho_lead_client import push_lead_to_zoho

client = OpenAI(api_key=load_api_key())
retriever = Retriever()

app = FastAPI(title="Roach Cicada Sales Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=str(ROOT / "assets")), name="assets")

# session_id -> {"name": str, "history": [{"role": ..., "content": ...}]}
SESSIONS: dict[str, dict] = {}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WHATSAPP_RE = re.compile(r"^\+?[0-9 ()-]{8,18}$")

SYSTEM_PROMPT_TEMPLATE = """You are Ananya, a senior sales consultant for Roach Cicada, a luxury residential
project by Roach Lifescapes in Junnasandra, off Sarjapur Road, Bangalore. You are speaking with
{buyer_name}, a prospective buyer who has already shared their contact details, so treat this as a
warm, qualified conversation with someone you respect and who has genuine buying capacity — many of
your buyers are High-Net-Worth Individuals and NRIs (Non-Resident Indians) evaluating this as an
investment or a home to return to.

How to behave:
- Be warm, unhurried, and consultative — never pushy, never use high-pressure sales tactics. Address
  {buyer_name} by name naturally, not in every message.
- Ground every factual claim (price, size, RERA number, amenities, distances, developer history,
  payment schedule) ONLY in the CONTEXT provided below. Never invent a number, a date, or a fact that
  isn't in the context. If something isn't in the context, say so plainly and offer to confirm with
  the sales/CRM team rather than guessing.
- When the context includes image or video file paths (they look like assets/folder/file.ext), and a
  relevant one exists for what you're discussing, say something natural in the PAST/PRESENT tense like
  "I've shared a few photos below" or "here's a short video of that" — the interface has ALREADY
  attached and rendered the actual media beneath your message by the time the buyer reads it, so never
  phrase it as an offer ("let me know if you'd like to see...") or a future action. You must NEVER
  write a markdown image tag like ![...](...) and NEVER type out a raw file path (assets/...) anywhere
  in your reply, under any circumstance. Just describe what you're sharing in plain words.
- For NRI buyers: you may give general, non-binding context that IS in the retrieved knowledge base
  (e.g. that GST applies to under-construction property, that stamp duty/registration are extra, that
  RERA registration exists). Do NOT give personalized investment, tax, or legal advice, and do NOT
  quote live currency exchange rates as fact — if asked to convert INR to USD/AED/GBP etc., give a
  rough approximate figure at most and clearly say to check the current rate, and recommend they
  consult their own CA/financial advisor for investment or tax decisions. Operational logistics specific
  to NRI buyers — remote/Power-of-Attorney purchase process, NRE/NRO banking, repatriation, TDS on
  sale — are NOT in the knowledge base. If asked, say plainly that you don't have those specifics in
  front of you and offer to have the sales team follow up with exact detail; do NOT assert or imply a
  capability (e.g. "yes we can do the whole purchase remotely") unless it is explicitly stated in the
  retrieved context.
- Never fabricate availability of a specific unit number, floor, or discount. Pricing in the context
  is a prelaunch cost sheet that is explicitly time-limited and subject to change — say so if asked
  whether the price is final.
- Keep replies concise and warm — a few short paragraphs at most, not an exhaustive dump. Offer a
  natural next step when it fits (e.g. a site visit, a call with the sales team at +91 81472 29590,
  or seeing more photos/floor plans) without being pushy.
- If asked something entirely outside this project (unrelated topics), politely redirect to how you
  can help with Roach Cicada.

CONTEXT (retrieved from the official knowledge base for this conversation — cite it faithfully):
{context_block}
"""


class LeadRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    whatsapp: str
    message: str = Field(default="", max_length=2000)
    consent: bool


class LeadResponse(BaseModel):
    session_id: str
    name: str
    zoho_status: str


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    images: list[str]
    videos: list[str]


@app.get("/")
def root():
    return FileResponse(str(ROOT / "chatbot" / "static" / "index.html"))


@app.post("/api/lead", response_model=LeadResponse)
def submit_lead(payload: LeadRequest):
    name = payload.name.strip()
    email = payload.email.strip()
    whatsapp = payload.whatsapp.strip()
    message = payload.message.strip()

    if not name:
        raise HTTPException(400, "Please enter your name.")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address.")
    if not WHATSAPP_RE.match(whatsapp):
        raise HTTPException(400, "Please enter a valid WhatsApp number, with country code (e.g. +91 98765 43210).")
    if not payload.consent:
        raise HTTPException(400, "Please confirm you're okay being contacted on WhatsApp about this property.")

    zoho_result = push_lead_to_zoho(name=name, email=email, whatsapp=whatsapp, message=message)
    leads_store.save_lead(name=name, email=email, whatsapp=whatsapp, message=message, zoho_result=zoho_result)

    session_id = str(uuid.uuid4())
    first_name = name.split()[0]
    SESSIONS[session_id] = {
        "name": first_name,
        "history": [],
    }
    return LeadResponse(session_id=session_id, name=first_name, zoho_status=zoho_result.get("status", "unknown"))


def _embed(text: str):
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return resp.data[0].embedding


MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
BARE_ASSET_PATH_RE = re.compile(r"`?/?assets/[A-Za-z0-9_\-./]+\.(?:png|jpe?g|webp|avif|mp4)`?")


def _strip_raw_media_paths(text: str) -> str:
    """Safety net: the model is instructed not to print raw asset paths (the
    frontend renders images/videos from the API's images/videos arrays
    instead), but LLMs don't always comply. Strip anything that looks like
    a leaked markdown image tag or bare asset path, then tidy whitespace."""
    text = MD_IMAGE_RE.sub("", text)
    text = BARE_ASSET_PATH_RE.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _build_context_block(hits):
    lines = []
    for h in hits:
        lines.append(f"### {h['doc_title']} — {h['heading'] or '(intro)'}\n{h['text']}")
    return "\n\n---\n\n".join(lines)


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    session = SESSIONS.get(payload.session_id)
    if not session:
        raise HTTPException(400, "Session not found — please submit your contact details first.")

    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(400, "Message is empty.")

    query_embedding = _embed(user_message)
    hits = retriever.search(query_embedding, top_k=6)
    context_block = _build_context_block(hits)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        buyer_name=session["name"], context_block=context_block
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(session["history"][-10:])  # keep last 10 turns for context window sanity
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    reply = _strip_raw_media_paths(completion.choices[0].message.content.strip())

    session["history"].append({"role": "user", "content": user_message})
    session["history"].append({"role": "assistant", "content": reply})

    images, videos = [], []
    for h in hits[:4]:
        for img in h.get("images", []):
            if img not in images:
                images.append(img)
        for vid in h.get("videos", []):
            if vid not in videos:
                videos.append(vid)
    images = images[:4]
    videos = videos[:1]

    # Relative (no leading slash) so it resolves correctly whether this app is
    # served at domain root (local dev) or behind a reverse-proxy path prefix
    # like https://dev.axonbos.com/roachcicada-chat/ (production).
    return ChatResponse(reply=reply, images=list(images), videos=list(videos))
