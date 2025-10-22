"""
AI CRM Automation package.

This module exposes a convenience entrypoint for programmatic usage by
re-exporting the orchestrator components.
"""

from .agents.orchestrator_agent import OrchestratorAgent, OrchestratorConfig

__all__ = ["OrchestratorAgent", "OrchestratorConfig"]
