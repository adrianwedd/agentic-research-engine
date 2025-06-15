import pytest

from src.example import hello

pytestmark = pytest.mark.core


def test_hello():
    assert hello("Codex") == "Hello, Codex!"
