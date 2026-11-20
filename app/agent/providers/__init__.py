from app.agent.providers.base import BaseLLMProvider
from app.agent.providers.mock_driver import MockLLMProvider
from app.agent.providers.openai_driver import OpenAILLMProvider
from app.config import settings


def get_llm_provider(mode: str = None, provider: str = None) -> BaseLLMProvider:
    selected_mode = mode or settings.llm_mode
    selected_provider = provider or settings.llm_provider

    if selected_mode == "mock":
        return MockLLMProvider()

    if selected_provider == "grok":
        return OpenAILLMProvider(provider="grok")

    return OpenAILLMProvider(provider="openai")


__all__ = ["BaseLLMProvider", "MockLLMProvider", "OpenAILLMProvider", "get_llm_provider"]
