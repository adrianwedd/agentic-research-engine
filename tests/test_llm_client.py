import importlib
import types

llm_module = importlib.import_module("services.llm_client")


class DummyResponse:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - simple stub
        pass

    def json(self):
        return self._data


def test_ollama_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL_NAME", "llama3")

    calls = {}

    def fake_post(url: str, json: dict, timeout: int):
        calls["url"] = url
        calls["json"] = json
        return DummyResponse({"message": {"content": "hi"}})

    monkeypatch.setattr(llm_module.requests, "post", fake_post)

    client = llm_module.load_llm_client()
    result = client.invoke([{"role": "user", "content": "hello"}])

    assert result == "hi"
    assert calls["url"].endswith("/api/chat")
    assert calls["json"]["model"] == "llama3"


def test_openai_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_MODEL_NAME", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "key")
    monkeypatch.setenv("LLM_API_BASE_URL", "http://cloud")

    called = {}

    class DummyOpenAI:
        def __init__(self, *args, **kwargs):
            called["api_key"] = kwargs.get("api_key")
            called["base_url"] = kwargs.get("base_url")
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, model: str, messages):
            called["model"] = model
            called["messages"] = messages
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))
                ]
            )

    monkeypatch.setattr("openai.OpenAI", DummyOpenAI)
    importlib.reload(llm_module)
    client = llm_module.load_llm_client()
    result = client.invoke([{"role": "user", "content": "hi"}])

    assert result == "ok"
    assert called["api_key"] == "key"
    assert called["base_url"] == "http://cloud"
    assert called["model"] == "test-model"
    assert called["messages"][0]["content"] == "hi"
