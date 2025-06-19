from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List


class MessageBus:
    """Abstract message bus interface."""

    async def connect(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def publish(self, subject: str, data: bytes) -> None:  # pragma: no cover
        raise NotImplementedError

    async def subscribe(
        self, subject: str, callback: Callable[[bytes], Awaitable[None]]
    ) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryMessageBus(MessageBus):
    """Simple in-memory pub/sub bus used for testing."""

    def __init__(self) -> None:
        self._subs: Dict[str, List[Callable[[bytes], Awaitable[None]]]] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def publish(self, subject: str, data: bytes) -> None:
        async with self._lock:
            callbacks = list(self._subs.get(subject, []))
        for cb in callbacks:
            await cb(data)

    async def subscribe(
        self, subject: str, callback: Callable[[bytes], Awaitable[None]]
    ) -> None:
        async with self._lock:
            self._subs.setdefault(subject, []).append(callback)


class NATSMessageBus(MessageBus):
    """NATS-based message bus."""

    def __init__(self, servers: str = "nats://127.0.0.1:4222") -> None:
        self.servers = servers
        self.nc: Any = None

    async def connect(self) -> None:
        from nats.aio.client import Client as NATS

        self.nc = NATS()
        await self.nc.connect(servers=[self.servers])

    async def close(self) -> None:
        if self.nc is not None:
            await self.nc.drain()
            await self.nc.close()

    async def publish(self, subject: str, data: bytes) -> None:
        if not self.nc:
            raise RuntimeError("NATS not connected")
        await self.nc.publish(subject, data)
        await self.nc.flush()

    async def subscribe(
        self, subject: str, callback: Callable[[bytes], Awaitable[None]]
    ) -> None:
        if not self.nc:
            raise RuntimeError("NATS not connected")

        async def handler(msg):
            await callback(msg.data)

        await self.nc.subscribe(subject, cb=handler)
