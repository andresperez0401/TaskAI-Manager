from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import get_settings
from modules.ai.exceptions import (
    AIAuthenticationError,
    AIBillingError,
    AIConfigurationError,
    AIModelNotFoundError,
    AIProviderError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AITimeoutError,
)
from modules.ai.factory import get_ai_provider

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AiConfig:
    provider: str
    api_key_present: bool
    base_url_present: bool
    model: str
    enabled: bool
    timeout_seconds: int
    allow_fallback: bool


@dataclass(slots=True)
class AiHealthResult:
    ai_enabled: bool
    provider: str
    model: str
    configured: bool
    provider_available: bool
    can_chat: bool
    allow_fallback: bool
    error: dict | None = None


class AiProviderClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = get_ai_provider()

    async def test_chat(self, message: str = "health check") -> str:
        response = await self.provider.chat_with_tools(
            model=self.settings.ai_model,
            system_prompt="You are a concise assistant.",
            user_message=message,
            tools=[],
        )
        return response.text or "ok"


class AiService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = get_ai_provider()

    def get_config(self) -> AiConfig:
        provider_key = self.settings.ai_provider.lower().strip()
        return AiConfig(
            provider=provider_key,
            api_key_present=bool(self.settings.ai_api_key),
            base_url_present=bool(self.settings.ai_base_url),
            model=self.settings.ai_model,
            enabled=self.settings.ai_enabled,
            timeout_seconds=self.settings.ai_timeout_seconds,
            allow_fallback=self.settings.ai_allow_fallback,
        )

    def _is_configured(self, cfg: AiConfig) -> bool:
        if not cfg.enabled:
            return False
        if cfg.provider in {"mock", "noop"}:
            return True
        if cfg.provider == "openai":
            return cfg.api_key_present and bool(cfg.model)
        if cfg.provider in {"deepseek", "generic", "generic_openai_compatible"}:
            return cfg.api_key_present and cfg.base_url_present and bool(cfg.model)
        return False

    @staticmethod
    def classify_error(exc: Exception) -> dict:
        if isinstance(exc, AIAuthenticationError):
            return {
                "code": "AI_AUTH_ERROR",
                "message": "Error autenticando con el proveedor IA. Revisa AI_API_KEY.",
            }
        if isinstance(exc, AIBillingError):
            return {
                "code": "AI_BILLING_ERROR",
                "message": "El proveedor IA rechazó la solicitud por saldo/créditos insuficientes.",
            }
        if isinstance(exc, AIModelNotFoundError):
            return {
                "code": "AI_MODEL_NOT_FOUND",
                "message": "El modelo configurado no existe en el proveedor IA.",
            }
        if isinstance(exc, AIRateLimitError):
            return {
                "code": "AI_RATE_LIMIT",
                "message": "El proveedor IA alcanzó el límite de requests. Intenta nuevamente.",
            }
        if isinstance(exc, AITimeoutError):
            return {
                "code": "AI_TIMEOUT",
                "message": "Timeout de conexión con el proveedor IA.",
            }
        if isinstance(exc, AIConfigurationError):
            return {
                "code": "AI_CONFIG_ERROR",
                "message": "La configuración del proveedor IA es inválida o incompleta.",
            }
        if isinstance(exc, AIProviderUnavailableError):
            return {
                "code": "AI_PROVIDER_UNAVAILABLE",
                "message": "El proveedor IA no está disponible temporalmente.",
            }
        if isinstance(exc, AIProviderError):
            return {
                "code": "AI_PROVIDER_ERROR",
                "message": "Error general del proveedor IA.",
            }
        return {
            "code": "INTERNAL_ERROR",
            "message": "Error inesperado en la integración IA.",
        }

    async def health(self, probe: bool = True) -> AiHealthResult:
        cfg = self.get_config()
        configured = self._is_configured(cfg)

        result = AiHealthResult(
            ai_enabled=cfg.enabled,
            provider=self.provider.provider_name,
            model=cfg.model,
            configured=configured,
            provider_available=self.provider.is_available,
            can_chat=False,
            allow_fallback=cfg.allow_fallback,
            error=None,
        )

        if not cfg.enabled:
            result.error = {
                "code": "AI_DISABLED",
                "message": "La IA está deshabilitada por configuración.",
            }
            return result

        if not configured:
            result.error = {
                "code": "AI_CONFIG_ERROR",
                "message": "Faltan variables de configuración del proveedor IA.",
            }
            return result

        if not probe:
            result.can_chat = result.provider_available
            return result

        client = AiProviderClient()
        try:
            await client.test_chat("responde con ok")
            result.can_chat = True
            return result
        except Exception as exc:  # noqa: BLE001
            mapped = self.classify_error(exc)
            logger.warning("AI health probe failed (%s): %s", mapped["code"], exc)
            result.can_chat = False
            result.error = mapped
            return result

    async def test_provider_chat(self, message: str) -> dict:
        client = AiProviderClient()
        try:
            answer = await client.test_chat(message)
            logger.info("AI provider test chat succeeded")
            return {
                "ok": True,
                "provider": self.provider.provider_name,
                "model": self.settings.ai_model,
                "answer": answer,
            }
        except Exception as exc:  # noqa: BLE001
            mapped = self.classify_error(exc)
            logger.warning("AI provider test chat failed (%s): %s", mapped["code"], exc)
            return {
                "ok": False,
                "provider": self.provider.provider_name,
                "model": self.settings.ai_model,
                "error": mapped,
            }
