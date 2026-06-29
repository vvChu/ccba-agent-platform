"""
Service modules providing business logic for ccba-agent-platform.
These services are shared between the CLI and the MCP server.
"""

from ccba_ai.services.plan import create_plan, get_plan_status, update_phase_status
from ccba_ai.services.team import add_task, claim_task, complete_task, load_tasks, save_tasks
from ccba_ai.services.seo import audit_file, audit_html, audit_markdown

__all__ = [
    "create_plan",
    "get_plan_status",
    "update_phase_status",
    "add_task",
    "claim_task",
    "complete_task",
    "load_tasks",
    "save_tasks",
    "audit_file",
    "audit_html",
    "audit_markdown",
]
