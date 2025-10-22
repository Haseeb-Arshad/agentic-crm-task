from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .main import init_agents, load_config


class RunRequest(BaseModel):
    prompt: str


class RunResponse(BaseModel):
    output: str


app = FastAPI(title="AI CRM Automation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    config = load_config()
    hubspot_agent, email_agent, orchestrator = init_agents(config)
    app.state.config = config
    app.state.hubspot = hubspot_agent
    app.state.email = email_agent
    app.state.orchestrator = orchestrator


@app.on_event("shutdown")
async def shutdown_event() -> None:
    hubspot_agent = getattr(app.state, "hubspot", None)
    email_agent = getattr(app.state, "email", None)
    closers = []
    if hubspot_agent:
        closers.append(hubspot_agent.aclose())
    if email_agent:
        closers.append(email_agent.aclose())
    if closers:
        await asyncio.gather(*closers, return_exceptions=True)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, Any]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse, tags=["orchestration"])
async def run_query(request: RunRequest) -> RunResponse:
    orchestrator = getattr(app.state, "orchestrator", None)
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    try:
        output = await orchestrator.run(request.prompt)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RunResponse(output=output)
