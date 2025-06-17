from __future__ import annotations

"""Simple in-memory Tool Registry with RBAC controls."""

import datetime
import json
import logging
import os
from typing import Callable, Dict, Iterable, Optional

import yaml
from opentelemetry import context, trace
from opentelemetry.trace import NonRecordingSpan, SpanContext

from services.tracing.tracing_schema import ToolCallTrace
from tools import (
    PostgresQueryTool,
    SqliteQueryTool,
    add_skill,
    code_interpreter,
    consolidate_memory,
    fact_check_claim,
    github_search,
    html_scraper,
    knowledge_graph_search,
    pdf_extract,
    propagate_subgraph,
    publish_reputation_event,
    retrieve_memory,
    semantic_consolidate,
    skill_metadata_query,
    skill_vector_query,
    summarize_text,
    web_search,
)
from tools.validation import validate_path_or_url

logger = logging.getLogger(__name__)


class AccessDeniedError(Exception):
    """Raised when a role tries to access an unauthorized tool."""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., object]] = {}
        self._permissions: Dict[str, set[str]] = {}
        self._init_contexts: Dict[str, SpanContext] = {}

    def register_tool(
        self,
        name: str,
        tool: Callable[..., object],
        *,
        allowed_roles: Optional[Iterable[str]] = None,
    ) -> None:
        """Register a tool and its allowed roles."""
        tracer = trace.get_tracer(__name__)
        parent_span = trace.get_current_span()
        parent_id = (
            parent_span.get_span_context().span_id
            if parent_span.get_span_context().is_valid
            else 0
        )
        with tracer.start_as_current_span(
            "tool.init",
            attributes={
                "tool.name": name,
                "init.timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "parent.span_id": hex(parent_id),
            },
        ) as span:
            self._init_contexts[name] = span.get_span_context()
        self._tools[name] = tool
        if allowed_roles is not None:
            self._permissions[name] = set(allowed_roles)
        else:
            self._permissions[name] = set()

    def get_tool(self, role: str, name: str) -> Callable[..., object]:
        """Retrieve a tool for a role if permitted."""
        if name not in self._tools:
            raise KeyError(name)
        allowed = self._permissions.get(name)
        if allowed and role not in allowed:
            raise AccessDeniedError(f"Role '{role}' cannot access tool '{name}'")
        tool = self._tools[name]
        init_ctx = self._init_contexts.get(name)

        if init_ctx is None:
            return tool

        def wrapped(*args: object, **kwargs: object) -> object:
            ctx = trace.set_span_in_context(NonRecordingSpan(init_ctx))
            token = context.attach(ctx)
            try:
                return tool(*args, **kwargs)
            finally:
                context.detach(token)

        return wrapped

    def invoke(
        self,
        role: str,
        name: str,
        *args: object,
        intent: str | None = None,
        **kwargs: object,
    ) -> object:
        """Invoke a tool via the registry enforcing RBAC."""

        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        try:
            tool = self.get_tool(role, name)
        except AccessDeniedError:
            logger.info(
                json.dumps(
                    {
                        "timestamp": timestamp,
                        "agent_id": role,
                        "action": name,
                        "intent": intent or "",
                        "outcome": "blocked",
                    }
                )
            )
            ToolCallTrace(
                agent_id=role,
                agent_role=role,
                tool_name=name,
                tool_input={"args": args, "kwargs": kwargs},
                unauthorized_call=True,
                intent=intent,
            ).record()
            raise

        result = tool(*args, **kwargs)
        logger.info(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "agent_id": role,
                    "action": name,
                    "intent": intent or "",
                    "outcome": "success",
                }
            )
        )
        ToolCallTrace(
            agent_id=role,
            agent_role=role,
            tool_name=name,
            tool_input={"args": args, "kwargs": kwargs},
            tool_output=result,
            intent=intent,
        ).record()
        return result

    def load_permissions(self, path: str) -> None:
        """Load role permissions from a YAML config."""
        sanitized = validate_path_or_url(path, allowed_schemes={"file"})
        data = yaml.safe_load(open(sanitized)) or {}
        perms = data.get("permissions", {})
        self._permissions = {tool: set(roles or []) for tool, roles in perms.items()}


DEFAULT_TOOLS: Dict[str, Callable[..., object]] = {
    "web_search": web_search.web_search
    if hasattr(web_search, "web_search")
    else web_search,
    "pdf_extract": pdf_extract,
    "html_scraper": html_scraper,
    "consolidate_memory": consolidate_memory,
    "retrieve_memory": retrieve_memory,
    "semantic_consolidate": semantic_consolidate,
    "add_skill": add_skill,
    "skill_vector_query": skill_vector_query,
    "skill_metadata_query": skill_metadata_query,
    "propagate_subgraph": propagate_subgraph,
    "summarize": summarize_text,
    "fact_check": fact_check_claim,
    "code_interpreter": code_interpreter,
    "knowledge_graph_search": knowledge_graph_search,
    "github_search": github_search,
    "sqlite_query": SqliteQueryTool,
    "postgres_query": PostgresQueryTool,
    "reputation_event": publish_reputation_event,
}


def create_default_registry(config_path: str | None = None) -> ToolRegistry:
    """Create a ToolRegistry with all built-in tools registered."""

    registry = ToolRegistry()

    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yml")

    if os.path.exists(config_path):
        sanitized = validate_path_or_url(config_path, allowed_schemes={"file"})
        data = yaml.safe_load(open(sanitized)) or {}
        perms = data.get("permissions", {})
    else:
        perms = {}

    for name, func in DEFAULT_TOOLS.items():
        allowed = perms.get(name)
        registry.register_tool(name, func, allowed_roles=allowed)

    return registry


__all__ = ["AccessDeniedError", "ToolRegistry", "create_default_registry"]
