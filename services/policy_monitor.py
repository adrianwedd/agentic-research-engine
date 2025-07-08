from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PolicyViolation(Exception):
    """Raised when an action violates the policy."""


class PolicyMonitor:
    def __init__(self, policy: Dict[str, List[str]] | None = None) -> None:
        self.policy = policy or {"blocked_tools": [], "blocked_keywords": []}
        self.events: List[Dict[str, Any]] = []

    def check_tool(self, role: str, name: str) -> None:
        allowed = name not in self.policy.get("blocked_tools", [])
        event = {"type": "tool", "role": role, "tool": name, "allowed": allowed}
        self.events.append(event)
        if not allowed:
            logger.warning("Policy blocked tool %s for role %s", name, role)
            raise PolicyViolation(f"tool {name} blocked")

    def check_message(self, sender: str, content: str) -> None:
        blocked = False
        for word in self.policy.get("blocked_keywords", []):
            if word.lower() in content.lower():
                blocked = True
                reason = word
                break
        event = {
            "type": "message",
            "sender": sender,
            "content": content,
            "allowed": not blocked,
        }
        self.events.append(event)
        if blocked:
            logger.warning("Policy blocked message from %s", sender)
            raise PolicyViolation(f"message contains banned term '{reason}'")


_MONITOR: PolicyMonitor | None = None


def set_monitor(monitor: PolicyMonitor | None) -> None:
    global _MONITOR
    _MONITOR = monitor


def get_monitor() -> PolicyMonitor | None:
    return _MONITOR
