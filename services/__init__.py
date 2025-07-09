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
    if name in {"MessageBus", "InMemoryMessageBus", "NATSMessageBus"}:
        from . import message_bus as _mb

        return getattr(_mb, name)
    if name in {
        "AuctionMechanism",
        "AuctionConfig",
        "Workload",
        "select_auction_mechanism",
    }:
        from . import auction as _auc

        return getattr(_auc, name)
    raise AttributeError(name)


__all__ = [
    "LLMClient",
    "OllamaClient",
    "OpenAICompatibleClient",
    "load_llm_client",
    "MessageBus",
    "InMemoryMessageBus",
    "NATSMessageBus",
    "AuctionMechanism",
    "AuctionConfig",
    "Workload",
    "select_auction_mechanism",
]
