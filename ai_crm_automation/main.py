from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .agents.hubspot_agent import HubSpotAgent
from .agents.email_agent import EmailAgent
from .agents.orchestrator_agent import OrchestratorAgent, OrchestratorConfig
from .utils.logger import get_logger


logger = get_logger(__name__)


def _config_from_env() -> Optional[Dict[str, Any]]:
    openai_key = os.getenv("OPENAI_API_KEY")
    hubspot_key = os.getenv("HUBSPOT_API_KEY")
    email_provider = os.getenv("EMAIL_PROVIDER", "sendgrid").lower()
    from_email = os.getenv("EMAIL_FROM_EMAIL")

    if not openai_key or not hubspot_key or not from_email:
        return None

    config: Dict[str, Any] = {
        "openai": {
            "api_key": openai_key,
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        },
        "hubspot": {
            "api_key": hubspot_key,
            "base_url": os.getenv("HUBSPOT_BASE_URL", "https://api.hubapi.com"),
        },
        "email": {
            "provider": email_provider,
            "from_email": from_email,
            "default_confirmation_recipient": os.getenv("EMAIL_DEFAULT_CONFIRMATION_RECIPIENT"),
            "sendgrid": {},
            "resend": {},
            "smtp": {
                "host": os.getenv("SMTP_HOST"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME"),
                "password": os.getenv("SMTP_PASSWORD"),
                "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"},
            },
        },
    }

    if email_provider == "sendgrid":
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        if not sendgrid_key:
            return None
        config["email"]["sendgrid"]["api_key"] = sendgrid_key
    elif email_provider == "resend":
        resend_key = os.getenv("RESEND_API_KEY")
        if not resend_key:
            return None
        config["email"]["resend"]["api_key"] = resend_key
    elif email_provider == "smtp":
        smtp = config["email"]["smtp"]
        if not smtp["host"]:
            return None
    else:
        return None

    return config


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json. If the file is missing, raise a
    descriptive error so users can copy config.example.json.
    """
    config_path_env = os.getenv("AI_CRM_CONFIG")
    if config_path_env:
        config_path = Path(config_path_env)
    else:
        config_path = Path(__file__).parent / "config.json"

    if not config_path.exists():
        env_config = _config_from_env()
        if env_config:
            return env_config
        example_path = Path(__file__).parent / "config.example.json"
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            f"Create it (for example by copying {example_path}) and provide your API keys."
        )

    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def async_main(user_query: Optional[str]) -> int:
    config = load_config()

    openai_key = config["openai"]["api_key"]
    openai_model = config["openai"].get("model", "gpt-4o-mini")

    hs_cfg = config.get("hubspot", {})
    hs_key = hs_cfg.get("api_key") or os.getenv("HUBSPOT_ACCESS_TOKEN")
    hs_base = config["hubspot"].get("base_url", "https://api.hubapi.com")

    email_cfg = config["email"]

    hubspot_agent = HubSpotAgent(api_key=hs_key, base_url=hs_base)
    email_agent = EmailAgent(config=email_cfg)

    orchestrator = OrchestratorAgent(
        config=OrchestratorConfig(openai_api_key=openai_key, openai_model=openai_model),
        hubspot=hubspot_agent,
        email=email_agent,
    )

    query = user_query
    if not query:
        query = input("Enter your CRM request: ")

    try:
        output = await orchestrator.run(query)
        print(output)
        return 0
    finally:
        await asyncio.gather(
            hubspot_agent.aclose(),
            email_agent.aclose(),
            return_exceptions=True,
        )


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        asyncio.run(async_main(arg))
    except KeyboardInterrupt:
        print("Interrupted")


if __name__ == "__main__":
    main()
