from __future__ import annotations

"""Lightweight tool adapter interface."""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]


def _load(name: str) -> Callable[..., Any]:
    module_name, func_name = name.rsplit(".", 1)
    module = import_module(f"tools.{module_name}")
    return getattr(module, func_name)


_REGISTRY: dict[str, Callable[..., Any]] = {
    "web.search": _load("web_search.web_search"),
    "pdf.reader": _load("pdf_reader.pdf_extract"),
    "python.exec": _load("code_interpreter.code_interpreter"),
}


def execute(call: ToolCall) -> Any:
    func = _REGISTRY.get(call.name)
    if func is None:
        raise ValueError(f"Unknown tool {call.name}")
    return func(**call.args)
