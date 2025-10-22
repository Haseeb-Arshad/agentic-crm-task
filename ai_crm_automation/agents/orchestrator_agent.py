from __future__ import annotations

import json
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate

from .hubspot_agent import HubSpotAgent, CreateContactInput, UpdateContactInput, CreateDealInput, UpdateDealInput
from .email_agent import EmailAgent
from ..utils.logger import get_logger
from ..utils.error_handler import ApiError


logger = get_logger(__name__)


class OrchestratorConfig(BaseModel):
    openai_api_key: str
    openai_model: str


class OrchestratorAgent:
    def __init__(self, config: OrchestratorConfig, hubspot: HubSpotAgent, email: EmailAgent):
        self.hubspot = hubspot
        self.email = email
        self.llm = ChatOpenAI(model=config.openai_model, api_key=config.openai_api_key, temperature=0)
        self.agent_executor = self._build_agent()

    def _build_agent(self) -> AgentExecutor:
        # Define tools that wrap our async methods. LangChain tools can be async.
        @tool("create_contact", args_schema=CreateContactInput, return_direct=False)
        async def create_contact_tool(
            email: EmailStr,
            firstName: Optional[str] = None,
            lastName: Optional[str] = None,
            phone: Optional[str] = None,
        ) -> str:
            """Create a new HubSpot contact with the supplied fields."""
            payload = CreateContactInput(
                email=email,
                first_name=firstName,
                last_name=lastName,
                phone=phone,
            )
            res = await self.hubspot.create_contact(payload)
            return json.dumps({"action": "create_contact", "result": res})

        @tool("update_contact", args_schema=UpdateContactInput, return_direct=False)
        async def update_contact_tool(
            email: EmailStr,
            firstName: Optional[str] = None,
            lastName: Optional[str] = None,
            phone: Optional[str] = None,
        ) -> str:
            """Update an existing HubSpot contact identified by email."""
            payload = UpdateContactInput(
                email=email,
                first_name=firstName,
                last_name=lastName,
                phone=phone,
            )
            res = await self.hubspot.update_contact(payload)
            return json.dumps({"action": "update_contact", "result": res})

        @tool("create_deal", args_schema=CreateDealInput, return_direct=False)
        async def create_deal_tool(
            dealName: Optional[str] = None,
            amount: Optional[float] = None,
            stage: Optional[str] = None,
            pipeline: Optional[str] = None,
            associated_contact_email: Optional[EmailStr] = None,
        ) -> str:
            """Create a HubSpot deal and optionally associate it with a contact."""
            payload = CreateDealInput(
                name=dealName,
                amount=amount,
                stage=stage,
                pipeline=pipeline,
                associated_contact_email=associated_contact_email,
            )
            res = await self.hubspot.create_deal(payload)
            return json.dumps({"action": "create_deal", "result": res})

        @tool("update_deal", args_schema=UpdateDealInput, return_direct=False)
        async def update_deal_tool(
            deal_id: str,
            dealName: Optional[str] = None,
            amount: Optional[float] = None,
            stage: Optional[str] = None,
            pipeline: Optional[str] = None,
        ) -> str:
            """Update fields on an existing HubSpot deal."""
            payload = UpdateDealInput(
                deal_id=deal_id,
                name=dealName,
                amount=amount,
                stage=stage,
                pipeline=pipeline,
            )
            res = await self.hubspot.update_deal(payload)
            return json.dumps({"action": "update_deal", "result": res})

        @tool("send_confirmation_email")
        async def send_confirmation_email_tool(to: Optional[str], subject: Optional[str], html: str) -> str:
            """Send a confirmation email summarizing recent CRM actions."""
            res = await self.email.send_confirmation(to_email=to, subject=subject, summary_html=html)
            return json.dumps({"action": "send_email", "result": res})

        tools = [
            create_contact_tool,
            update_contact_tool,
            create_deal_tool,
            update_deal_tool,
            send_confirmation_email_tool,
        ]

        system = (
            "You are a helpful CRM assistant. Parse the user's request and call the appropriate tools. "
            "Prefer creating contacts or deals when the user asks; update when they request changes. "
            "After successful CRM actions, call send_confirmation_email summarizing what was done. "
            "Be concise and include key identifiers like emails or IDs in the summary."
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    async def run(self, user_input: str) -> str:
        try:
            result = await self.agent_executor.ainvoke({"input": user_input})
            # LangChain standard return has "output"
            return result.get("output", "Done")
        except ApiError as e:
            detail = e.details
            if isinstance(detail, (dict, list)):
                detail_str = json.dumps(detail)
            elif detail is not None:
                detail_str = str(detail)
            else:
                detail_str = e.message
            logger.error(
                "Orchestrator run failed due to upstream API error",
                extra={"status": e.status, "detail": detail_str},
            )
            return f"API error {e.status}: {detail_str}. Please verify your credentials and permissions."
        except Exception as e:
            logger.exception("Orchestrator run failed")
            return f"Sorry, something went wrong: {str(e)}"
