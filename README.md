# AI CRM Automation

Natural-language control over HubSpot contacts and deals with automated confirmation emails. The project includes:

- **LangChain Orchestrator** – parses plain English, calls the right tools, and remembers the last eight turns for follow-ups.
- **HubSpot Agent** – contact/deal helpers with idempotent contact creation and optional deal associations.
- **Email Agent** – Resend by default or swap to SendGrid/SMTP.
- **Async Utilities** – httpx client with retries, JSON logs.
- **CLI + FastAPI backend** – run one-off commands or keep a server listening on port 8000.
- **Minimal frontend** – pg-lang inspired UI that submits prompts to the backend.

```
ai_crm_automation/
├─ agents/
│  ├─ orchestrator_agent.py
│  ├─ hubspot_agent.py
│  └─ email_agent.py
├─ utils/
│  ├─ api_client.py
│  ├─ error_handler.py
│  └─ logger.py
├─ main.py              # CLI entry
├─ server.py            # FastAPI app (port 8000)
├─ config.example.json
├─ README.md
frontend/
├─ index.html
├─ script.js
└─ styles.css
```

---

## Credentials Needed
| Service | Purpose | Env / Config Keys |
|---------|---------|-------------------|
| OpenAI  | LangChain LLM | `OPENAI_API_KEY` (optional `OPENAI_MODEL`) |
| HubSpot | Contacts & Deals | `HUBSPOT_ACCESS_TOKEN` (Private App token) or `hubspot.api_key` |
| Resend  | Confirmation emails | `RESEND_API_KEY`, `EMAIL_FROM_EMAIL` verified |
| SendGrid *(optional)* | Email alt | `SENDGRID_API_KEY` |
| SMTP *(optional)* | Email fallback | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` |

Secrets live in `.env` or `config.json` (both gitignored). Share only `.env.example` / `config.example.json`.

---

## Prerequisites
- Python 3.11 or 3.12 (3.13 not yet supported)
- [`uv`](https://docs.astral.sh/uv/) package manager
- Accounts/tokens for the providers you plan to use

---

## Setup
```bash
uv python install 3.12            # or 3.11
uv venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS/Linux
uv sync
```

Configure secrets:
- Copy `ai_crm_automation/config.example.json` → `ai_crm_automation/config.json` and fill values **or**
- Create `.env` from `.env.example` and optionally set `AI_CRM_CONFIG`.

Minimum environment (Resend + HubSpot):
```env
OPENAI_API_KEY=sk-...
HUBSPOT_ACCESS_TOKEN=pat-...
EMAIL_PROVIDER=resend
EMAIL_FROM_EMAIL=no-reply@haseebarshad.me
RESEND_API_KEY=re_...
```

---

## Backend (FastAPI + CLI)
Start the API:
```bash
uv run --env-file .env uvicorn ai_crm_automation.server:app --host 0.0.0.0 --port 8000
```
- `GET /health` → `{ "status": "ok" }`
- `POST /run` with `{ "prompt": "..." }` → `{ "output": "..." }`
- Orchestrator keeps the last 8 turns to maintain context.

Run an ad hoc command:
```bash
uv run --env-file .env python -m ai_crm_automation.main \
  "Create contact Jane Doe with email jane@haseebarshad.me and add a deal worth 5000 dollars"
```
Omit the argument for interactive mode.

---

## Frontend (static)
1. Ensure the backend is up on port 8000.
2. Serve `frontend/` (examples):
   ```bash
   npx serve frontend
   # or any static server (Live Server, python -m http.server, etc.)
   ```
3. Open the served URL. Buttons trigger `/run` calls immediately. To target a different backend, append `?api=https://your-host`.
4. Responses append to the transcript and align with the backend’s conversation memory.

---

## Troubleshooting
- **401 HubSpot** – token missing scopes/expired (needs `crm.objects.contacts/deals.*` + associations).
- **404 association** – contact/deal ID missing or app lacks association scope.
- **Email missing** – verify sender domain in Resend/SendGrid/SMTP.
- **OpenAI quota** – adjust `OPENAI_MODEL` or review usage limits.
- **Python 3.13 errors** – use 3.11/3.12 until dependencies ship wheels.

---

## Developer Notes
- `.gitignore` skips `.env`, `config.json`, `.venv`, bytecode, `uv.lock`.
- Quick check: `uv run --env-file .env python -m compileall ai_crm_automation`.
- Agents can be swapped by keeping tool signatures the same.

---

## License
MIT
