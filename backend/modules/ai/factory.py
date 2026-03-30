"""AI provider factory — creates the right provider based on configuration."""

from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings
from modules.ai.base import AIProvider
from modules.ai.providers.mock_provider import MockProvider
from modules.ai.providers.noop_provider import NoopProvider

logger = logging.getLogger(__name__)


def _build_provider() -> AIProvider:
    """Instantiate the provider that matches the current settings."""
    settings = get_settings()

    if not settings.ai_enabled:
        logger.info("AI is disabled (AI_ENABLED=false) → using NoopProvider")
        return NoopProvider()

    provider_key = settings.ai_provider.lower().strip()
    api_key = settings.ai_api_key or ""
    model = settings.ai_model
    timeout = settings.ai_timeout_seconds

    if provider_key == "noop":
        logger.info("AI_PROVIDER=noop → using NoopProvider")
        return NoopProvider()

    if provider_key == "mock":
        logger.info("AI_PROVIDER=mock → using MockProvider")
        return MockProvider()

    if provider_key == "openai":
        from modules.ai.providers.openai_provider import OpenAIProvider

        if not api_key:
            logger.warning("AI_PROVIDER=openai but AI_API_KEY is empty → falling back to NoopProvider")
            return NoopProvider()
        logger.info("AI_PROVIDER=openai → using OpenAIProvider (model=%s)", model)
        return OpenAIProvider(api_key=api_key, model=model, timeout=timeout)

    if provider_key in ("generic_openai_compatible", "generic", "deepseek"):
        from modules.ai.providers.generic_openai_compatible_provider import (
            GenericOpenAICompatibleProvider,
        )

        base_url = settings.ai_base_url
        if provider_key == "deepseek" and not base_url:
            base_url = "https://api.deepseek.com"
        if not base_url:
            logger.warning("AI_PROVIDER=generic but AI_BASE_URL is empty → NoopProvider")
            return NoopProvider()
        if not api_key:
            logger.warning("AI_PROVIDER=generic but AI_API_KEY is empty → NoopProvider")
            return NoopProvider()
        logger.info(
            "AI_PROVIDER=generic_openai_compatible → base_url=%s model=%s",
            base_url,
            model,
        )
        return GenericOpenAICompatibleProvider(
            api_key=api_key, base_url=base_url, model=model, timeout=timeout
        )

    logger.warning("Unknown AI_PROVIDER=%s → using NoopProvider", provider_key)
    return NoopProvider()


@lru_cache
def get_ai_provider() -> AIProvider:
    """Singleton factory — cached for the process lifetime."""
    return _build_provider()
