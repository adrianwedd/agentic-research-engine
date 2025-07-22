from __future__ import annotations

"""Asynchronous HTTP client for the Tool Registry servers."""

from typing import Any, Dict, Optional

import httpx


class ToolRegistryAsyncClient:
    """HTTP client using :class:`httpx.AsyncClient` to access the registry."""

    def __init__(
        self, base_url: str, *, client: Optional[httpx.AsyncClient] = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient()

    async def close(self) -> None:
        await self._client.aclose()

    async def get_tool(self, role: str, name: str) -> str:
        from . import AccessDeniedError

        resp = await self._client.get(
            f"{self.base_url}/tool", params={"agent": role, "name": name}
        )
        if resp.status_code == 404:
            raise KeyError(name)
        if resp.status_code == 403:
            raise AccessDeniedError(resp.json().get("error", "forbidden"))
        resp.raise_for_status()
        data = resp.json()
        return data.get("tool", "")

    async def invoke(
        self,
        role: str,
        tool: str,
        *args: Any,
        intent: str | None = None,
        **kwargs: Any,
    ) -> Any:
        payload: Dict[str, Any] = {
            "agent": role,
            "tool": tool,
            "args": list(args),
            "kwargs": kwargs,
            "intent": intent or "",
        }
        from . import AccessDeniedError

        resp = await self._client.post(f"{self.base_url}/invoke", json=payload)
        if resp.status_code == 404:
            raise KeyError(tool)
        if resp.status_code == 403:
            raise AccessDeniedError(resp.json().get("error", "forbidden"))
        resp.raise_for_status()
        return resp.json().get("result")

    async def __aenter__(self) -> "ToolRegistryAsyncClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.__aexit__(*exc_info)
