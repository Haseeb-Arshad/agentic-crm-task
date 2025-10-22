# AI CRM Automation Backend

Automate HubSpot CRM tasks with natural language and send confirmation emails without wiring every workflow by hand. This project wraps a LangChain orchestrator, HubSpot contact/deal tools, and email providers behind both a CLI and a FastAPI backend so frontends can drive the automation over HTTP.

---

## Architecture at a Glance
- **LangChain orchestrator**: interprets free text, picks the right CRM and email tools, and sequences them safely.
- **HubSpot agent**: wraps CRM v3 APIs for contacts, deals, and associations. Contact creation is idempotent; existing contacts are reused after a 409 conflict.
- **Email agent**: delivers confirmation emails through Resend by default, with SendGrid or SMTP as alternatives.
- **Async utilities**: shared httpx client with retry logic, structured logging, and simple error helpers.

Project layout:
```
ai_crm_automation/
├─ agents/
│  ├─ orchestrator_agent.py   # LangChain tool definitions and executor
│  ├─ hubspot_agent.py        # CRM helpers, idempotent contact creation
│  └─ email_agent.py          # Resend / SendGrid / SMTP transport
├─ utils/
│  ├─ api_client.py           # httpx AsyncClient with retries
│  ├─ error_handler.py        # Custom exceptions
│  └─ logger.py               # JSON logger configuration
├─ main.py                    # CLI entry point
├─ server.py                  # FastAPI app for long-running backend
├─ config.example.json        # Template for file-based config
└─ README.md
```

---

## External Services & Required Keys
| Service  | Purpose                                | Required environment or config keys                             |
|----------|----------------------------------------|------------------------------------------------------------------|
| OpenAI   | LLM for intent parsing                 | `OPENAI_API_KEY` (optional `OPENAI_MODEL`, default `gpt-4o-mini`) |
| HubSpot  | Contacts, deals, associations          | `HUBSPOT_ACCESS_TOKEN` (Private App token) or `hubspot.api_key` |
| Resend   | Default confirmation emails            | `RESEND_API_KEY` and `email.from_email` verified on Resend       |
| SendGrid | Optional email provider                | `SENDGRID_API_KEY`                                              |
| SMTP     | Optional SMTP fallback                 | Host, port, username, password, `use_tls`                       |

> Keep production secrets in `.env` (already gitignored) or a vault. Ship only `.env.example` and `config.example.json`.

---

## Prerequisites
- Python 3.11 or 3.12 (3.13 is not yet supported by several dependencies)
- [`uv`](https://docs.astral.sh/uv/) for virtualenv and dependency management
- Accounts and API tokens for the providers you intend to use

---

## Setup
1. **Install a managed Python and dependencies**
   ```bash
   uv python install 3.12
   uv venv
   .venv\Scripts\activate      # Windows
   # source .venv/bin/activate  # macOS / Linux
   uv sync
   ```
   (Use `uv python install 3.11` if you prefer Python 3.11.)

2. **Configure secrets**
   - Copy `ai_crm_automation/config.example.json` to `ai_crm_automation/config.json` and fill in real values, **or**
   - Populate an `.env` based on `.env.example` and optionally set `AI_CRM_CONFIG=/path/to/config.json`.
   - Minimum environment expected for the default Resend + HubSpot flow:
     ```env
     OPENAI_API_KEY=sk-...
     HUBSPOT_ACCESS_TOKEN=pat-...
     EMAIL_PROVIDER=resend
     EMAIL_FROM_EMAIL=no-reply@haseebarshad.me
     RESEND_API_KEY=re_...
     ```

---

## Running the CLI
Execute one-off commands directly from the terminal:
```bash
uv run --env-file .env python -m ai_crm_automation.main \
  "Create contact Jane Doe with email jane@haseebarshad.me and add a deal worth 5000 dollars"
```
- Leave out the argument for interactive mode.
- The CLI prints a human-readable summary; JSON logs contain full context, including upstream HTTP responses.

---

## Running the HTTP Backend (port 8000)
Start the FastAPI service so a frontend or Postman collection can drive automation:
```bash
uv run --env-file .env uvicorn ai_crm_automation.server:app --host 0.0.0.0 --port 8000
```
- `GET /health` returns `{ "status": "ok" }`.
- `POST /run` with body `{ "prompt": "Create contact ..." }` runs the orchestrator and returns `{ "output": "..." }`.
- Agents are initialized once at startup and disposed cleanly on shutdown, so you can leave the server running and issue multiple requests.

---

## Configuration Reference
- **OpenAI**
  - `OPENAI_API_KEY` (required)
  - `OPENAI_MODEL` to override the default
- **HubSpot**
  - Prefer `HUBSPOT_ACCESS_TOKEN` from a Private App with `crm.objects.contacts.*`, `crm.objects.deals.*`, and association scopes.
  - A `hubspot.api_key` entry in config.json also works; the environment variable takes precedence.
- **Email providers**
  - `email.provider`: `resend`, `sendgrid`, or `smtp`
  - Resend: set `RESEND_API_KEY` and ensure `email.from_email` is a verified sender (for example `no-reply@haseebarshad.me`)
  - SendGrid: provide `SENDGRID_API_KEY` and a verified sender identity
  - SMTP: configure the `email.smtp` block (`host`, `port`, `username`, `password`, `use_tls`)
- When both config file and environment variables define a value, the environment wins.

---

## Example Prompts
- `Create contact Jane Doe with email jane@haseebarshad.me.`
- `Update contact john@example.com set phone to +1-555-1234.`
- `Create a $5000 deal named Q4 Expansion and associate it to jane@example.com.`
- `Update deal 123456 set stage to closedwon.`

The orchestrator may ask for missing parameters (for example, a deal amount) before completing the workflow.

---

## Request Flow
1. The orchestrator receives a prompt, calls LangChain tool selection, and plans the CRM/email steps.
2. The HubSpot agent performs contact/deal mutations. Contact creation handles 409 conflicts by calling the search endpoint and reusing the existing record.
3. The email agent formats a summary and delivers it through the configured provider.
4. Logs are emitted in JSON with level, component, and message; feed them into your preferred log pipeline.

---

## Troubleshooting
- **401 from HubSpot**: token missing scopes or expired. Regenerate the Private App token with deal/contact read/write scopes.
- **404 when associating deals**: contact or deal ID not found, or associations scope missing. Confirm both objects exist and the app has `crm.objects.*.write`.
- **Email never arrives**: verify sender domain and recipient permissions in your email provider; check spam folders.
- **OpenAI quota errors**: watch usage limits or switch to a cheaper model via `OPENAI_MODEL`.
- **Dependency build failures on Python 3.13**: use Python 3.11 or 3.12 until upstream wheels are available.

---

## Developer Tips
- `.gitignore` already skips `.env`, `config.json`, `.venv`, compiled bytecode, and `uv.lock` so you can push to GitHub safely.
- Quick syntax check: `uv run --env-file .env python -m compileall ai_crm_automation`.
- Extend or replace providers by keeping the agent method signatures the same; the orchestrator only cares about the tool interface.

---

## License
MIT
