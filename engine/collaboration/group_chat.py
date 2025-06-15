# P3-01: Implement Dynamic Group Chat System
"""Utilities for multi-agent collaboration via group chat."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional


class DynamicGroupChat:
    """Simple in-memory group chat with a shared workspace."""

    def __init__(self, shared_workspace: Dict[str, Any]) -> None:
        """Initialize the collaborative environment."""
        self.shared_workspace = shared_workspace
        self.message_history: List[Dict[str, Any]] = []
        self.inboxes: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.turn_queue: List[str] = []
        self.roles: Dict[str, str] = {}

    def facilitate_team_collaboration(
        self, team_composition: List[Dict[str, str] | str], task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up collaboration environment for the team."""
        self.turn_queue = []
        self.roles = {}
        for member in team_composition:
            if isinstance(member, str):
                agent_id = member
                role = "member"
            else:
                agent_id = member.get("id")
                role = member.get("role", "member")
            if agent_id:
                self.turn_queue.append(agent_id)
                self.roles[agent_id] = role
        return {
            "team": self.turn_queue.copy(),
            "roles": self.roles.copy(),
            "task_context": task_context,
        }

    def post_message(
        self,
        sender: str,
        content: str,
        *,
        message_type: str = "message",
        recipient: Optional[str] = None,
    ) -> None:
        """Send a message to the chat."""
        msg = {
            "sender": sender,
            "content": content,
            "type": message_type,
            "recipient": recipient,
        }
        self.message_history.append(msg)
        if recipient:
            self.inboxes[recipient].append(msg)
        else:
            for agent in self.turn_queue:
                if agent != sender:
                    self.inboxes[agent].append(msg)

    def get_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Return and clear the pending messages for the agent."""
        msgs = self.inboxes.pop(agent_id, [])
        return msgs

    def update_workspace(self, agent_id: str, key: str, value: Any) -> None:
        """Update the shared workspace if permitted."""
        # Placeholder for role-based permissions; all agents may write for now.
        self.shared_workspace[key] = value

    def resolve_conflicts(self, key: str, value1: Any, value2: Any) -> Any:
        """Simple last-write-wins conflict resolution."""
        return value2
