import pytest

from tools.code_interpreter import code_interpreter

pytestmark = pytest.mark.core


def test_code_interpreter_print():
    result = code_interpreter('print("hello world")')
    assert result["stdout"] == "hello world\n"
    assert result["stderr"] == ""
    assert result["returncode"] == 0


def test_code_interpreter_result_value():
    result = code_interpreter("1 + 1")
    assert result["result"] == 2
