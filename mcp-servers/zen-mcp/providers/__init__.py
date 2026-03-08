"""Model provider abstractions for supporting multiple AI providers."""

from importlib import import_module

from .base import ModelCapabilities, ModelProvider, ModelResponse
from .registry import ModelProviderRegistry

__all__ = [
    "ModelProvider",
    "ModelResponse",
    "ModelCapabilities",
    "ModelProviderRegistry",
    "GeminiModelProvider",
    "OpenAIModelProvider",
    "OpenAICompatibleProvider",
    "OpenRouterProvider",
]

_PROVIDER_EXPORTS = {
    "GeminiModelProvider": (".gemini", "GeminiModelProvider"),
    "OpenAIModelProvider": (".openai_provider", "OpenAIModelProvider"),
    "OpenAICompatibleProvider": (".openai_compatible", "OpenAICompatibleProvider"),
    "OpenRouterProvider": (".openrouter", "OpenRouterProvider"),
}


def __getattr__(name: str):
    """Lazily import provider classes only when accessed."""
    if name in _PROVIDER_EXPORTS:
        module_name, attribute_name = _PROVIDER_EXPORTS[name]
        module = import_module(module_name, package=__name__)
        return getattr(module, attribute_name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
