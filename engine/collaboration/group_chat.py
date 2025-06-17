# P3-01: Implement Dynamic Group Chat System
"""Utilities for multi-agent collaboration via group chat."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from threading import Lock
from typing import Any, Awaitable, Callable, DefaultDict, Dict, List, Optional

from ..state import State
from .message_protocol import ChatMessage


class DynamicGroupChat:
    """Simple in-memory group chat with a shared workspace and scratchpad."""

    def __init__(
        self, shared_workspace: Dict[str, Any], *, enable_lock: bool = False
    ) -> None:
        """Initialize the collaborative environment."""
        self.shared_workspace = shared_workspace
        self.message_history: List[Dict[str, Any]] = []
        self.inboxes: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.turn_queue: List[str] = []
        self.roles: Dict[str, str] = {}
        self.scratchpad: Dict[str, Any] = {}
        self._state: State | None = None
        self._lock: Lock | None = Lock() if enable_lock else None

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

    def bind_state(self, state: State) -> None:
        """Attach a State instance and share its scratchpad."""
        self._state = state
        self.scratchpad = state.scratchpad

    def write_scratchpad(self, key: str, value: Any) -> None:
        """Write a value to the shared scratchpad and State."""
        if self._lock:
            with self._lock:
                self.scratchpad[key] = value
                if self._state is not None:
                    self._state.scratchpad[key] = value
        else:
            self.scratchpad[key] = value
            if self._state is not None:
                self._state.scratchpad[key] = value

    def read_scratchpad(self, key: str) -> Any | None:
        """Return an entry from the shared scratchpad."""
        if self._lock:
            with self._lock:
                return self.scratchpad.get(key)
        return self.scratchpad.get(key)

    def update_scratchpad(
        self, key: str, update_fn: Callable[[Any | None], Any]
    ) -> Any:
        """Atomically update a scratchpad entry using ``update_fn``."""
        if self._lock:
            with self._lock:
                new_value = update_fn(self.scratchpad.get(key))
                self.scratchpad[key] = new_value
                if self._state is not None:
                    self._state.scratchpad[key] = new_value
                return new_value
        new_value = update_fn(self.scratchpad.get(key))
        self.scratchpad[key] = new_value
        if self._state is not None:
            self._state.scratchpad[key] = new_value
        return new_value

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
        if self._lock:
            with self._lock:
                self.message_history.append(msg)
                if recipient:
                    self.inboxes[recipient].append(msg)
                else:
                    for agent in self.turn_queue:
                        if agent != sender:
                            self.inboxes[agent].append(msg)
        else:
            self.message_history.append(msg)
            if recipient:
                self.inboxes[recipient].append(msg)
            else:
                for agent in self.turn_queue:
                    if agent != sender:
                        self.inboxes[agent].append(msg)

    def get_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Return and clear the pending messages for the agent."""
        if self._lock:
            with self._lock:
                msgs = self.inboxes.pop(agent_id, [])
        else:
            msgs = self.inboxes.pop(agent_id, [])
        return [ChatMessage.model_validate(m).model_dump() for m in msgs]

    def update_workspace(self, agent_id: str, key: str, value: Any) -> None:
        """Update the shared workspace if permitted."""
        # Placeholder for role-based permissions; all agents may write for now.
        if self._lock:
            with self._lock:
                self.shared_workspace[key] = value
        else:
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
                [List[Dict[str, Any]], "State", Dict[str, Any]],
                Awaitable[str] | str | Dict[str, Any],
            ],
        ],
        *,
        max_turns: int = 10,
        shared_workspace: Optional[Dict[str, Any]] = None,
        enable_lock: bool = False,
    ) -> None:
        self.agents = agents
        self.max_turns = max_turns
        self.chat = DynamicGroupChat(shared_workspace or {}, enable_lock=enable_lock)
        self.turn_order = list(agents)

    async def run(self, state: "State") -> "State":
        """Execute a simple round-robin chat session."""

        self.chat.bind_state(state)
        self.chat.facilitate_team_collaboration(self.turn_order, state.data)
        turns = 0
        idx = 0
        while turns < self.max_turns:
            agent_id = self.turn_order[idx]
            agent_fn = self.agents[agent_id]
            incoming = self.chat.get_messages(agent_id)
            if asyncio.iscoroutinefunction(agent_fn):
                result = await agent_fn(incoming, state, state.scratchpad)
            else:
                result = agent_fn(incoming, state, state.scratchpad)

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
