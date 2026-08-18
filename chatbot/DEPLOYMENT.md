# Production Deployment

Live at: **https://dev.axonbos.com/roachcicada-chat/**

Deployed independently of the AxonBOS Core / octopus-automations codebases — its own directory, its
own systemd service, its own Python venv. It happens to live on the same AWS Lightsail host as the
AxonBOS V2 stack (reusing existing infrastructure per the original request), and it reaches the
`axon-gateway-v2-dev` container over the host's published port for the live Zoho CRM push, but nothing
about this deployment depends on or modifies any AxonBOS/Octopus container, image, or compose file.

## Server layout

| Item | Value |
|---|---|
| Host | `13.127.216.95` (AWS Lightsail, ap-south-1) — same server as AxonBOS Core V2 |
| SSH | `ssh -i "sshkey/LightsailDefaultKey-ap-south-1 (1).pem" ubuntu@13.127.216.95` |
| App directory | `/opt/roachcicada/` (independent of `/opt/axonbos/`) |
| Python venv | `/opt/roachcicada/chatbot/.venv` |
| Secret | `/opt/roachcicada/.secrets/openaiapi.txt` (chmod 600, scp'd directly — never committed) |
| Process manager | systemd unit `roachcicada-chatbot.service`, runs `uvicorn server:app --host 127.0.0.1 --port 8420` |
| Reverse proxy | nginx, appended `location /roachcicada-chat/` block to the existing `/etc/nginx/sites-enabled/dev.axonbos.com` (prefix-stripped proxy to `127.0.0.1:8420`, matching the existing `/tally-chat-bll/` pattern on that same file) |
| Zoho gateway reachability | `GATEWAY_URL=http://127.0.0.1:9200` — the `axon-gateway-v2-dev` container publishes to the host on that port, so no Docker network join was needed |

## Config actually used in production (systemd `Environment=` lines)

```
GATEWAY_URL=http://127.0.0.1:9200
ZOHO_COMPANY_ID=29
ZOHO_LEAD_SOURCE=Octopus Website
```

`ZOHO_LEAD_SOURCE=Octopus Website` was verified against the live picklist
(`GET /v1/zoho/crm/worker/picklist/Leads/Lead_Source`) — it's the one value out of 63 that reads as a
generic website-sourced lead. `common.py`'s default now matches this.

**Zoho `Tag.name` has a 25-character server-side limit** — discovered live via `INVALID_DATA` on the
first real deploy attempt (`"roachcicada:website-chatbot"` was 27 chars). Fixed to `"roachcicada:website"`
(19 chars) in `zoho_lead_client.py`. Keep any future tag values under 25 chars.

## Redeploying after a code change

```bash
KEY="sshkey/LightsailDefaultKey-ap-south-1 (1).pem"
HOST=ubuntu@13.127.216.95

# Sync source (excludes venv/data/index/secrets — those stay server-side)
rsync -az --exclude='.git' --exclude='chatbot/.venv' --exclude='chatbot/__pycache__' \
  --exclude='chatbot/data' --exclude='chatbot/index' --exclude='assets/unrelated-do-not-use' \
  --exclude='.secrets' --exclude='.DS_Store' \
  -e "ssh -i \"$KEY\"" ./ "$HOST:/opt/roachcicada/"

# If requirements.txt changed:
ssh -i "$KEY" $HOST "cd /opt/roachcicada/chatbot && source .venv/bin/activate && pip install -q -r requirements.txt"

# If any *.md knowledge-base file changed, rebuild the embedding index:
ssh -i "$KEY" $HOST "cd /opt/roachcicada/chatbot && source .venv/bin/activate && python build_index.py"

# Restart
ssh -i "$KEY" $HOST "sudo systemctl restart roachcicada-chatbot"
```

## Known state after first deploy (2026-08-18)

Two real test leads landed in the **live** Octopus Estates Zoho CRM during verification (before the
`Tag` length bug was found, most create attempts correctly failed with `INVALID_DATA` and never reached
Zoho — only these two actually got created):

- "Server Smoke Test 3" — `smoketest3@example.com` — Zoho id `5044293000054120004`
- "Public URL Test" — `publictest@example.com`

There is no delete-lead endpoint in the gateway BLL contract this client uses, so these need to be
removed manually by someone with Zoho CRM access. Worth a quick check for any other stray
`smoketest*@example.com` / `*test@example.com` leads tagged `roachcicada:website` before this goes in
front of real buyers.

## Still needed for the floating-button embed on roachcicada.co

This deployment makes the chat reachable at a stable HTTPS URL with CORS open (`Access-Control-Allow-Origin: *`,
verified). What's left is purely front-end: a small floating-button + iframe/panel snippet added to
Webflow's site-wide custom code (Project Settings → Custom Code → Footer Code), pointing at
`https://dev.axonbos.com/roachcicada-chat/`. Not yet built — say the word and it's a small addition.
