# AI CRM Automation (HubSpot + Email) with LangChain

This project is a complete, modular, AI-powered multi-agent system that automates HubSpot CRM workflows and sends confirmation emails using LangChain tool-calling.

## Features
- Global Orchestrator Agent interprets natural-language queries and delegates tasks
- HubSpot Agent performs CRM v3 operations (contacts and deals)
- Email Agent sends confirmations via SendGrid API or SMTP
- Async-first implementation (`aiohttp`, `aiosmtplib`)
- Strong error handling and structured logging
- Easily replace CRM or Email providers

## File Structure
```
/ai_crm_automation/
├── agents/
│   ├── orchestrator_agent.py
│   ├── hubspot_agent.py
│   ├── email_agent.py
├── utils/
│   ├── api_client.py
│   ├── error_handler.py
│   ├── logger.py
├── config.json
├── main.py
├── requirements.txt
├── README.md
```

## Prerequisites
- Python 3.10+
- API keys for: OpenAI, HubSpot, and Resend (or SendGrid / SMTP credentials)

## Setup (uv)
1. Ensure `uv` is installed (see [docs](https://docs.astral.sh/uv/)).
2. Provision a managed environment and install dependencies:
   ```bash
   uv python install 3.12
   uv venv
   .venv\Scripts\activate      # Windows
   # source .venv/bin/activate  # macOS/Linux
   uv sync
   ```
   This uses `pyproject.toml` / `uv.lock` to install into `.venv`.
   *Tip:* Stick to Python 3.11 or 3.12; some dependencies do not yet ship wheels for 3.13.
3. Configure secrets:
   - Copy `config.example.json` → `config.json` and fill in real values, **or**
   - Export environment variables matching `.env.example` (set `AI_CRM_CONFIG` if `config.json` lives elsewhere).
   - Supported email providers: `resend`, `sendgrid`, or `smtp`.
   - HubSpot auth can come from `hubspot.api_key` or the `HUBSPOT_ACCESS_TOKEN` environment variable.

`load_config` automatically falls back to environment variables when no config file is present.

### config.json
```json
{
  "openai": {
    "api_key": "YOUR_OPENAI_API_KEY",
    "model": "gpt-4o-mini"
  },
  "hubspot": {
    "api_key": "YOUR_HUBSPOT_API_KEY",
    "base_url": "https://api.hubapi.com"
  },
  "email": {
    "provider": "resend",
    "from_email": "no-reply@haseebarshad.me",
    "default_confirmation_recipient": "owner@haseebarshad.me",
    "sendgrid": {
      "api_key": "YOUR_SENDGRID_API_KEY"
    },
    "resend": {
      "api_key": "YOUR_RESEND_API_KEY"
    },
    "smtp": {
      "host": "smtp.gmail.com",
      "port": 587,
      "username": "YOUR_SMTP_USERNAME",
      "password": "YOUR_SMTP_PASSWORD",
      "use_tls": true
    }
  }
}
```

## Running
From the project root:
```bash
uv run python -m ai_crm_automation.main "Create a new contact named Jane Doe with email jane@haseebarshad.me and add a deal worth $5000"
```
You can also run without arguments for an interactive prompt.

## Example Queries
- "Create contact Jane Doe with email jane@x.com"
- "Update contact john@haseebarshad.me set phone to +1-555-1234"
- "Create a new deal for $5000 named Q4 Expansion and associate it to jane@x.com"

## Behavior
- The orchestrator interprets the request and calls the right tools
- On successful CRM actions, the orchestrator calls the email tool to send a summary
- If any step fails, an error message is returned with context

## Replace Providers
Agents are modular. To swap providers, implement the same public methods in a new class or adjust `utils/api_client.py` and update configurations.

## Troubleshooting
- Ensure API keys are valid and not rate-limited
- Confirm your HubSpot Private App has the required scopes
- For SMTP with Gmail, enable App Passwords when using 2FA

## License
MIT
