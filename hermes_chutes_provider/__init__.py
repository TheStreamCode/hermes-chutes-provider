"""Chutes model-provider profile for Hermes Agent."""

import json
import logging
import urllib.request

from providers import register_provider
from providers.base import ProviderProfile


__version__ = "0.1.3"
logger = logging.getLogger(__name__)


class ChutesProviderProfile(ProviderProfile):
    """Provider profile backed by Chutes' agent-capable live catalog."""

    # Newer Hermes versions use this opt-in to trust /models context metadata.
    # Older versions safely ignore unknown class attributes.
    use_live_model_metadata = True

    def fetch_model_metadata(
        self,
        api_key: str = "",
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> list[dict[str, object]] | None:
        try:
            effective_base = base_url or self.base_url
            url = (self.models_url or "").strip()
            if not url:
                if not effective_base:
                    return None
                url = effective_base.rstrip("/") + "/models"

            from hermes_cli.urllib_security import open_credentialed_url

            request = urllib.request.Request(url)
            if api_key:
                request.add_header("Authorization", f"Bearer {api_key}")
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", f"hermes-chutes-provider/{__version__}")
            for key, value in self.default_headers.items():
                request.add_header(key, value)

            with open_credentialed_url(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode())
            items = payload if isinstance(payload, list) else payload.get("data", [])
            models = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                model_id = item.get("id")
                if not isinstance(model_id, str) or not model_id.strip():
                    continue
                features = item.get("supported_features")
                if not isinstance(features, (list, tuple, set)):
                    continue
                if "tools" in {str(feature).lower() for feature in features}:
                    models.append(item)
            return models
        except Exception as exc:
            logger.debug("fetch_model_metadata(chutes): %s", exc)
            return None

    def fetch_models(
        self,
        api_key: str = "",
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        metadata = self.fetch_model_metadata(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        if metadata is None:
            return None
        return [item["id"] for item in metadata if isinstance(item.get("id"), str)]


chutes = ChutesProviderProfile(
    name="chutes",
    api_mode="chat_completions",
    aliases=("chutes-ai", "chutesai"),
    display_name="Chutes",
    description="Chutes - OpenAI-compatible decentralized inference",
    signup_url="https://chutes.ai/app/api",
    env_vars=("CHUTES_API_KEY", "CHUTES_BASE_URL"),
    base_url="https://llm.chutes.ai/v1",
    auth_type="api_key",
    fallback_models=("default:latency", "default:throughput"),
)
chutes.use_live_model_metadata = True


def register() -> None:
    """Register the Chutes profile with the host Hermes process."""

    register_provider(chutes)


__all__ = ("ChutesProviderProfile", "__version__", "chutes", "register")
