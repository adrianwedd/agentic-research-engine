from __future__ import annotations

"""Lightweight tool adapter interface."""

import logging
from dataclasses import dataclass
from importlib import import_module, metadata
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

PLUGIN_ENTRYPOINT_GROUP = "agentic_research_engine.tools"


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]


def _load(name: str) -> Callable[..., Any]:
    module_name, func_name = name.rsplit(".", 1)
    module = import_module(f"tools.{module_name}")
    return getattr(module, func_name)


def _discover_plugins() -> Dict[str, Callable[..., Any]]:
    """Return callables exposed via the plugin entry point group."""
    try:
        eps = metadata.entry_points(group=PLUGIN_ENTRYPOINT_GROUP)
    except TypeError:  # pragma: no cover - py < 3.10
        eps = metadata.entry_points().get(PLUGIN_ENTRYPOINT_GROUP, [])  # type: ignore[attr-defined]

    plugins: Dict[str, Callable[..., Any]] = {}
    for ep in eps:
        try:
            plugins[ep.name] = ep.load()
        except Exception:  # pragma: no cover - defensive
            logger.warning("Failed to load plugin %s", ep.name, exc_info=True)
    return plugins


_REGISTRY: dict[str, Callable[..., Any]] = {
    "web.search": _load("web_search.web_search"),
    "pdf.reader": _load("pdf_reader.pdf_extract"),
    "python.exec": _load("code_interpreter.code_interpreter"),
}

_REGISTRY.update(_discover_plugins())


def execute(call: ToolCall) -> Any:
    func = _REGISTRY.get(call.name)
    if func is None:
        raise ValueError(f"Unknown tool {call.name}")
    return func(**call.args)
