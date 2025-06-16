"""Service utilities and clients."""


def __getattr__(name: str):
    if name in {
        "LLMClient",
        "OllamaClient",
        "OpenAICompatibleClient",
        "load_llm_client",
    }:
        from . import llm_client as _lc

        return getattr(_lc, name)
    raise AttributeError(name)


__all__ = [
    "LLMClient",
    "OllamaClient",
    "OpenAICompatibleClient",
    "load_llm_client",
]
