"""Chutes model-provider profile for Hermes Agent."""

import hashlib
import json
import logging
import threading
import time
import urllib.request

from providers import register_provider
from providers.base import ProviderProfile


__version__ = "0.1.6"
logger = logging.getLogger(__name__)
_MAX_CATALOG_RESPONSE_BYTES = 8 * 1024 * 1024
_LIVE_CONTEXT_TTL = 300.0
_LIVE_CONTEXT_LOCK = threading.Lock()


class ChutesProviderProfile(ProviderProfile):
    """Provider profile backed by Chutes' agent-capable live catalog."""

    # Forward-compatible opt-in for a host that trusts provider-supplied
    # /models context metadata instead of its aggregator catalog. No released
    # Hermes version reads this flag today, and hosts that do not know it
    # ignore unknown class attributes, so declaring it is inert until support
    # lands upstream.
    use_live_model_metadata = True

    def live_context_length(
        self, model: str, *, api_key: str = "", base_url: str = ""
    ) -> int | None:
        """Return an exact catalog window without persisting fallback guesses."""

        catalog_identity = json.dumps(
            [
                (base_url or self.base_url).rstrip("/"),
                getattr(self, "models_url", "") or "",
                getattr(self, "default_headers", None) or {},
                api_key,
            ],
            sort_keys=True,
        )
        cache_key = hashlib.sha256(catalog_identity.encode("utf-8")).hexdigest()
        # Serialize refreshes so overlapping context lookups share one bounded
        # probe. Include the caller's endpoint even when models_url is set:
        # an overridden fetch hook may route those endpoints independently.
        with _LIVE_CONTEXT_LOCK:
            cache = self.__dict__.setdefault("_live_context_cache", {})
            cached = cache.get(cache_key)
            if cached is not None and time.monotonic() - cached[0] < _LIVE_CONTEXT_TTL:
                entries = cached[1]
            else:
                entries = self.fetch_model_metadata(api_key=api_key, base_url=base_url or None)
                if entries is None:
                    entries = cached[1] if cached else []
                cache[cache_key] = (time.monotonic(), entries)
        for entry in entries:
            if entry.get("id") == model:
                window = entry.get("context_length")
                return window if type(window) is int and window > 0 else None
        return None

    def fetch_model_metadata(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> list[dict[str, object]] | None:
        try:
            effective_base = base_url or self.base_url
            # models_url and default_headers are optional on ProviderProfile:
            # read them defensively so older hosts that predate either field
            # still get a working catalog probe instead of a swallowed
            # AttributeError.
            url = (getattr(self, "models_url", "") or "").strip()
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
            for key, value in (getattr(self, "default_headers", None) or {}).items():
                request.add_header(key, value)

            with open_credentialed_url(request, timeout=timeout) as response:
                body = response.read(_MAX_CATALOG_RESPONSE_BYTES + 1)
            if len(body) > _MAX_CATALOG_RESPONSE_BYTES:
                return None

            payload = json.loads(body.decode("utf-8"))
            if isinstance(payload, list):
                items = payload
            elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
                items = payload["data"]
            else:
                return None

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
        api_key: str | None = None,
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
# ProviderProfile is a dataclass, so mirror the class-level opt-in onto the
# instance as well: hosts that inspect vars()/asdict() rather than the class
# still see it.
chutes.use_live_model_metadata = True


def register() -> None:
    """Register the Chutes profile with the host Hermes process."""

    register_provider(chutes)


__all__ = ("ChutesProviderProfile", "__version__", "chutes", "register")
