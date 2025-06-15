import pytest

from services.tool_registry import AccessDeniedError, ToolRegistry


def dummy_tool():
    return "ok"


def test_registry_authorization():
    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool, allowed_roles=["WebResearcher"])

    tool = registry.get_tool("WebResearcher", "dummy")
    assert tool() == "ok"

    with pytest.raises(AccessDeniedError):
        registry.get_tool("Supervisor", "dummy")
