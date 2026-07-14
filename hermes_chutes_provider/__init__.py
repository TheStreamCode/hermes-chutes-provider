"""Chutes model-provider profile for Hermes Agent."""

from providers import register_provider
from providers.base import ProviderProfile


__version__ = "0.1.0"

chutes = ProviderProfile(
    name="chutes",
    api_mode="chat_completions",
    aliases=("chutes-ai", "chutesai"),
    display_name="Chutes",
    description="Chutes - OpenAI-compatible decentralized inference",
    signup_url="https://chutes.ai/app/api",
    env_vars=("CHUTES_API_KEY", "CHUTES_BASE_URL"),
    base_url="https://llm.chutes.ai/v1",
    auth_type="api_key",
    fallback_models=(),
)


def register() -> None:
    """Register the Chutes profile with the host Hermes process."""

    register_provider(chutes)


__all__ = ("__version__", "chutes", "register")
