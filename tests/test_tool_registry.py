import pytest

from services.tool_registry.registry import AccessDeniedError, ToolRegistry


def test_tool_permissions(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text("permissions:\n  WebResearcher:\n    - web_search\n")
    registry = ToolRegistry(str(config))

    def web_search():
        return "results"

    def code_interpreter():
        return "code"

    registry.register_tool("web_search", web_search)
    registry.register_tool("code_interpreter", code_interpreter)

    tool = registry.get_tool("WebResearcher", "web_search")
    assert callable(tool)
    assert tool() == "results"
    with pytest.raises(AccessDeniedError):
        registry.get_tool("WebResearcher", "code_interpreter")
