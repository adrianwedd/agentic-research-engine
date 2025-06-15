from __future__ import annotations

"""Simple in-memory Tool Registry with RBAC controls."""

from typing import Callable, Dict, Iterable, Optional

import yaml


class AccessDeniedError(Exception):
    """Raised when a role tries to access an unauthorized tool."""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., object]] = {}
        self._permissions: Dict[str, set[str]] = {}

    def register_tool(
        self,
        name: str,
        tool: Callable[..., object],
        *,
        allowed_roles: Optional[Iterable[str]] = None,
    ) -> None:
        """Register a tool and its allowed roles."""
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
        return self._tools[name]

    def load_permissions(self, path: str) -> None:
        """Load role permissions from a YAML config."""
        data = yaml.safe_load(open(path)) or {}
        perms = data.get("permissions", {})
        self._permissions = {tool: set(roles or []) for tool, roles in perms.items()}
