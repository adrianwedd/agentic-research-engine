"""Intent-based authorization utilities."""

from importlib import import_module


def __getattr__(name: str):
    if name in {"IntentAuthorizer", "IntentAuthZServer"}:
        return getattr(import_module(".intent_authorizer", __name__), name)
    raise AttributeError(name)


__all__ = ["IntentAuthorizer", "IntentAuthZServer"]
