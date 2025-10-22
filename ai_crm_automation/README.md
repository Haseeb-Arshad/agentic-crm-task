# AI CRM Automation with LangChain

AI-powered assistants that turn natural-language requests into HubSpot CRM actions and follow up with branded confirmation emails. The system is agent-based, async, and fully scriptable for operations teams that want reliable automation without building bespoke workflows for every request.

---

## What You Get
- **Intent-aware orchestrator** that understands plain English requests and calls the right tools in sequence.
- **HubSpot agent** for contacts, deals, and associations. Contact creation is idempotent: if the email already exists, the agent reuses the stored record.
- **Email agent** that delivers HTML summaries via Resend by default, with SendGrid or SMTP as drop-in options.
- **Shared utilities**: httpx client with retry logic, Pydantic models, and JSON logging for observability.

```
ai_crm_automation/
├─ agents/
│  ├─ orchestrator_agent.py     # LangChain tool-calling agent
│  ├─ hubspot_agent.py          # Contacts, deals, idempotent create
│  └─ email_agent.py            # Resend/SendGrid/SMTP transport
├─ utils/
│  ├─ api_client.py             # httpx AsyncClient + retries
│  ├─ error_handler.py          # Domain-specific exceptions
│  └─ logger.py                 # JSON logging configuration
├─ config.example.json          # Copy → config.json for local secrets
├─ main.py                      # CLI entry point (async bootstrap)
└─ README.md                    # You are here
```

---

## Required APIs & Credentials
| Service | Purpose | Mandatory Values |
|---------|---------|------------------|
| **OpenAI** | Large language model (prompt parsing + tool selection) | `OPENAI_API_KEY`, optional `OPENAI_MODEL` (default `gpt-4o-mini`) |
| **HubSpot** | CRM contacts and deals | `HUBSPOT_ACCESS_TOKEN` (Private App token with contact/deal scopes) |
| **Resend** | Confirmation emails (default) | `RESEND_API_KEY`, verified sender e.g. `no-reply@haseebarshad.me` |
| **SendGrid** *(optional)* | Alternative email provider | `SENDGRID_API_KEY` |
| **SMTP** *(optional)* | Traditional SMTP relay | host, port, username, password, TLS flag |

> Keep production secrets in `.env` (ignored by git) or a secret manager. Only share `.env.example` and `config.example.json` with teammates.

---

## Prerequisites
- Python 3.11 or 3.12 (many dependencies do not yet publish wheels for 3.13)
- [`uv`](https://docs.astral.sh/uv/) package manager
- Accounts for OpenAI, HubSpot, and your chosen email provider

---

## Setup Guide
1. **Install runtime and dependencies**
   ```bash
   uv python install 3.12
   uv venv
   .venv\Scripts\activate      # Windows
   # source .venv/bin/activate  # macOS/Linux
   uv sync
   ```
   *Tip:* use `uv python install 3.11` if you prefer Python 3.11.

2. **Configure secrets**
   - Copy `ai_crm_automation/config.example.json` → `ai_crm_automation/config.json` and fill in real credentials, **or**
   - Populate an `.env` based on `.env.example` and optionally set `AI_CRM_CONFIG` to point to a custom config file.
   - Minimum environment for the default Resend + HubSpot path:
     ```env
     OPENAI_API_KEY=sk-...
     HUBSPOT_ACCESS_TOKEN=pat-...
     EMAIL_PROVIDER=resend
     EMAIL_FROM_EMAIL=no-reply@haseebarshad.me
     RESEND_API_KEY=re_...
     ```

3. **Run commands**
   ```bash
   uv run --env-file .env python -m ai_crm_automation.main \
     "Create contact Jane Doe with email jane@haseebarshad.me and add a deal worth 5000 dollars"
   ```
   - Omit the argument to receive an interactive prompt.
   - The CLI prints a user-facing summary. Structured logs (JSON) show upstream HTTP statuses.

4. **Verify results**
   - HubSpot UI should show the contact and deal. If the contact already existed, logs include `Contact already existed` with the reused ID.
   - Resend dashboard (or SendGrid/SMTP logs) should show the confirmation email.

---

## Configuration Cheatsheet
- **OpenAI**
  - `OPENAI_API_KEY` – required.
  - `OPENAI_MODEL` – override (any Chat Completions-capable model).
- **HubSpot**
  - `HUBSPOT_ACCESS_TOKEN` – bearer token from a Private App with `crm.objects.contacts.read/write`, `crm.objects.deals.read/write`, and association permissions.
  - `hubspot.api_key` in `config.json` is accepted but the env var takes precedence.
- **Email Providers**
  - Set `email.provider` to `resend`, `sendgrid`, or `smtp`.
  - Resend: supply `RESEND_API_KEY` and a verified `email.from_email` (for example `no-reply@haseebarshad.me`).
  - SendGrid: only `sendgrid.api_key` is required once the sender identity is verified.
  - SMTP: configure `email.smtp` block (`host`, `port`, `username`, `password`, `use_tls`).
- If both file-based config and environment variables are present, environment values win.

---

## Example Prompts
- “Create contact Jane Doe with email jane@haseebarshad.me.”
- “Update contact john@example.com set phone to +1-555-1234.”
- “Create a Q4 Expansion deal for 5000 USD and link it to jane@example.com.”
- “Change the stage of deal 123456 to closedwon.”

The orchestrator may ask follow-up questions if critical details (like amount) are missing. Responses are streamed back once the task completes.

---

## Execution Flow
1. The orchestrator (LangChain + OpenAI) interprets the request and selects tools.
2. The HubSpot agent executes contact/deal operations. Contact creation handles 409 conflicts by pulling the existing record via `/crm/v3/objects/contacts/search` and reusing the ID.
3. If the workflow succeeds, the email agent generates a short HTML summary and sends it through the configured provider.
4. Logs are emitted in JSON with level, component, and message for easy ingestion into observability tooling.

---

## Troubleshooting
- **401 Unauthorized (HubSpot)** – Token missing scopes or expired. Regenerate the Private App token with the required CRM scopes.
- **404 when associating deals** – Usually indicates missing association scopes or deleted objects. Ensure the deal/contact IDs exist and your app has `crm.objects.contacts.write` and `crm.objects.deals.write` scopes.
- **Email not delivered** – Verify the sender domain (Resend/SendGrid), check spam folders, and confirm recipients are allowed.
- **Quota / rate issues** – Review provider dashboards for usage limits. The retry policy handles transient 429s but not hard limits.
- **Python 3.13 builds fail** – Use Python 3.11/3.12 until dependency wheels are published.

---

## Developer Notes
- `.gitignore` already excludes `.env`, `config.json`, `.venv`, compiled files, and `uv.lock` so you can publish safely.
- Run a fast syntax check with `uv run --env-file .env python -m compileall ai_crm_automation`.
- Extend or swap providers by keeping the agent interfaces the same—the orchestrator only depends on tool signatures.

---

## License
MIT
