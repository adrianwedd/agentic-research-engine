# P3-01: Implement Dynamic Group Chat System
"""Utilities for multi-agent collaboration via group chat."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, DefaultDict, Dict, List, Optional

from ..state import State
from .message_protocol import ChatMessage


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
        msg = ChatMessage(
            sender=sender,
            content=content,
            type=message_type,
            recipient=recipient,
        ).model_dump()
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
        return [ChatMessage.model_validate(m).model_dump() for m in msgs]

    def update_workspace(self, agent_id: str, key: str, value: Any) -> None:
        """Update the shared workspace if permitted."""
        # Placeholder for role-based permissions; all agents may write for now.
        self.shared_workspace[key] = value

    def resolve_conflicts(self, key: str, value1: Any, value2: Any) -> Any:
        """Simple last-write-wins conflict resolution."""
        return value2


class GroupChatManager:
    """Manage a collaborative conversation among multiple agents."""

    def __init__(
        self,
        agents: Dict[
            str,
            Callable[
                [List[Dict[str, Any]], "State"], Awaitable[str] | str | Dict[str, Any]
            ],
        ],
        *,
        max_turns: int = 10,
        shared_workspace: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.agents = agents
        self.max_turns = max_turns
        self.chat = DynamicGroupChat(shared_workspace or {})
        self.turn_order = list(agents)

    async def run(self, state: "State") -> "State":
        """Execute a simple round-robin chat session."""

        self.chat.facilitate_team_collaboration(self.turn_order, state.data)
        turns = 0
        idx = 0
        while turns < self.max_turns:
            agent_id = self.turn_order[idx]
            agent_fn = self.agents[agent_id]
            incoming = self.chat.get_messages(agent_id)
            if asyncio.iscoroutinefunction(agent_fn):
                result = await agent_fn(incoming, state)
            else:
                result = agent_fn(incoming, state)

            if result:
                if isinstance(result, dict):
                    content = result.get("content", "")
                    msg_type = result.get("type", "message")
                    recipient = result.get("recipient")
                else:
                    content = str(result)
                    msg_type = "message"
                    recipient = None
                self.chat.post_message(
                    agent_id, content, message_type=msg_type, recipient=recipient
                )
                state.add_message(
                    {
                        "sender": agent_id,
                        "content": content,
                        "type": msg_type,
                        "recipient": recipient,
                    }
                )
                if msg_type == "finish" or content.strip().upper() == "FINISH":
                    break

            turns += 1
            if result and isinstance(result, dict) and result.get("recipient"):
                try:
                    idx = self.turn_order.index(result["recipient"])
                except ValueError:
                    idx = (idx + 1) % len(self.turn_order)
            else:
                idx = (idx + 1) % len(self.turn_order)

        state.update({"conversation": self.chat.message_history})
        return state
