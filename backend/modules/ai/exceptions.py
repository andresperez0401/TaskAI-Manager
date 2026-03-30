"""AI provider exceptions — independent from any vendor SDK."""


class AIProviderError(Exception):
    """Base exception for all AI provider errors."""

    def __init__(self, message: str = "AI provider error", *, provider: str = "unknown"):
        self.provider = provider
        super().__init__(message)


class AIAuthenticationError(AIProviderError):
    """Invalid or missing API key (401/403)."""


class AIRateLimitError(AIProviderError):
    """Rate limit exceeded (429)."""


class AITimeoutError(AIProviderError):
    """Request timed out."""


class AIModelNotFoundError(AIProviderError):
    """Requested model does not exist on provider."""


class AIProviderUnavailableError(AIProviderError):
    """Provider is unavailable (network, 500, etc.)."""


class AIConfigurationError(AIProviderError):
    """Provider config is incomplete (missing base URL, model, etc.)."""


class AIBillingError(AIProviderError):
    """Provider account has insufficient balance/credits (402)."""


class AIDisabledError(AIProviderError):
    """AI is explicitly disabled via configuration."""

    def __init__(self):
        super().__init__(
            "La IA está deshabilitada por configuración (AI_ENABLED=false).",
            provider="noop",
        )
