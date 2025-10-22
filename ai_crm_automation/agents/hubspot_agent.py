from __future__ import annotations

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field

from ..utils.api_client import AsyncApiClient
from ..utils.error_handler import ApiError, ValidationError, require
from ..utils.logger import get_logger


logger = get_logger(__name__)


class CreateContactInput(BaseModel):
    email: EmailStr
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None


class UpdateContactInput(BaseModel):
    email: EmailStr
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None


class CreateDealInput(BaseModel):
    name: Optional[str] = Field(default=None, alias="dealName")
    amount: Optional[float] = None
    stage: Optional[str] = None
    pipeline: Optional[str] = None
    associated_contact_email: Optional[EmailStr] = None


class UpdateDealInput(BaseModel):
    deal_id: str
    name: Optional[str] = Field(default=None, alias="dealName")
    amount: Optional[float] = None
    stage: Optional[str] = None
    pipeline: Optional[str] = None


class HubSpotAgent:
    def __init__(self, api_key: Optional[str], base_url: str):
        token = api_key or os.getenv("HUBSPOT_ACCESS_TOKEN")
        require(bool(token), "HubSpot access token is required. Set HUBSPOT_ACCESS_TOKEN or provide api_key.")
        headers = {
            "Authorization": f"Bearer {token}",
        }
        self.client = AsyncApiClient(base_url=base_url, default_headers=headers)

    async def _get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "EQ", "value": email}
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "phone"],
            "limit": 1,
        }
        res = await self.client.post("/crm/v3/objects/contacts/search", json=query)
        if not isinstance(res, dict):
            return None
        results = res.get("results", [])
        if not results:
            return None
        return results[0]

    async def _find_contact_id_by_email(self, email: str) -> Optional[str]:
        contact = await self._get_contact_by_email(email)
        if not contact:
            return None
        return contact.get("id")

    async def create_contact(self, payload: CreateContactInput) -> Dict[str, Any]:
        properties: Dict[str, Any] = {"email": str(payload.email)}
        if payload.first_name:
            properties["firstname"] = payload.first_name
        if payload.last_name:
            properties["lastname"] = payload.last_name
        if payload.phone:
            properties["phone"] = payload.phone
        try:
            res = await self.client.post("/crm/v3/objects/contacts", json={"properties": properties})
        except ApiError as err:
            if err.status == 409:
                existing = await self._get_contact_by_email(str(payload.email))
                if existing:
                    contact_id = existing.get("id")
                    logger.info(
                        "Contact already existed",
                        extra={"email": str(payload.email), "contact_id": contact_id},
                    )
                    return {
                        "id": contact_id,
                        "properties": existing.get("properties", {}),
                        "status": "existing",
                    }
                logger.warning(
                    "Contact conflict reported but existing record not found",
                    extra={"email": str(payload.email)},
                )
            raise
        contact_id = res.get("id") if isinstance(res, dict) else None
        logger.info(
            "New contact created",
            extra={"email": str(payload.email), "contact_id": contact_id},
        )
        return res

    async def update_contact(self, payload: UpdateContactInput) -> Dict[str, Any]:
        contact_id = await self._find_contact_id_by_email(str(payload.email))
        require(contact_id is not None, f"Contact not found for email {payload.email}")
        properties: Dict[str, Any] = {}
        if payload.first_name is not None:
            properties["firstname"] = payload.first_name
        if payload.last_name is not None:
            properties["lastname"] = payload.last_name
        if payload.phone is not None:
            properties["phone"] = payload.phone
        res = await self.client.patch(f"/crm/v3/objects/contacts/{contact_id}", json={"properties": properties})
        return res

    async def create_deal(self, payload: CreateDealInput) -> Dict[str, Any]:
        deal_name = payload.name
        if not deal_name:
            if payload.associated_contact_email:
                deal_name = f"Deal for {payload.associated_contact_email}"
            elif payload.amount is not None:
                deal_name = f"Deal {payload.amount:g}"
            else:
                deal_name = "Untitled Deal"

        properties: Dict[str, Any] = {"dealname": deal_name}
        if payload.amount is not None:
            properties["amount"] = payload.amount
        if payload.stage:
            properties["dealstage"] = payload.stage
        if payload.pipeline:
            properties["pipeline"] = payload.pipeline

        create_resp = await self.client.post("/crm/v3/objects/deals", json={"properties": properties})
        deal_id = create_resp.get("id")

        # Associate to contact if provided
        if payload.associated_contact_email:
            contact_id = await self._find_contact_id_by_email(str(payload.associated_contact_email))
            require(contact_id is not None, f"Contact not found for email {payload.associated_contact_email}")
            # Use v3 associations API with name-based association type to avoid v4's ID requirement
            await self.client.put(
                f"/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/deal_to_contact",
            )
        return create_resp

    async def update_deal(self, payload: UpdateDealInput) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}
        if payload.name is not None:
            properties["dealname"] = payload.name
        if payload.amount is not None:
            properties["amount"] = payload.amount
        if payload.stage is not None:
            properties["dealstage"] = payload.stage
        if payload.pipeline is not None:
            properties["pipeline"] = payload.pipeline

        res = await self.client.patch(f"/crm/v3/objects/deals/{payload.deal_id}", json={"properties": properties})
        return res

    async def aclose(self) -> None:
        await self.client.close()
