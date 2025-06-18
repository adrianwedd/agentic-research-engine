from src.example import hello


def test_hello_returns_greeting():
    assert hello("Codex") == "Hello, Codex!"
