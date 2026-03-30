from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    app_name: str = "task-ai-manager"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_cors_allow_all_dev: bool = True
    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:8000"
    )

    # ── Database ───────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/task_manager_ai"
    )
    direct_database_url: str | None = None

    # ── AI Provider (decoupled) ────────────────────────────────────────────
    ai_enabled: bool = True
    ai_provider: str = "openai"  # openai | generic_openai_compatible | mock | noop
    ai_model: str = "gpt-4.1-mini"
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_timeout_seconds: int = 30
    ai_allow_fallback: bool = True

    # ── Legacy aliases (kept for backward compat with existing .env) ──────
    openai_api_key: str | None = None
    openai_model: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None
    anthropic_base_url: str | None = None

    def model_post_init(self, __context: object) -> None:
        """Migrate legacy OPENAI_* vars into the new AI_* namespace."""
        if not self.ai_api_key and self.openai_api_key:
            self.ai_api_key = self.openai_api_key
        if self.openai_model and self.ai_model == "gpt-4.1-mini":
            self.ai_model = self.openai_model

        # Optional compatibility with Anthropic-style env names.
        if not self.ai_api_key and self.anthropic_api_key:
            self.ai_api_key = self.anthropic_api_key
        if self.anthropic_model and self.ai_model == "gpt-4.1-mini":
            self.ai_model = self.anthropic_model
        if not self.ai_base_url and self.anthropic_base_url:
            self.ai_base_url = self.anthropic_base_url

        # DeepSeek default URL when provider is selected and base URL is omitted.
        if self.ai_provider.lower().strip() == "deepseek" and not self.ai_base_url:
            self.ai_base_url = "https://api.deepseek.com"

    # ── Properties ─────────────────────────────────────────────────────────
    @property
    def backend_cors_origins_list(self) -> list[str]:
        return [x.strip() for x in self.backend_cors_origins.split(",") if x.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local"}

    @property
    def async_database_url(self) -> str:
        return self._normalize_database_url(self.database_url)

    @property
    def migration_database_url(self) -> str:
        return self._normalize_database_url(self.direct_database_url or self.database_url)

    @staticmethod
    def _normalize_database_url(url: str) -> str:
        raw = url
        # Only normalize PostgreSQL URLs; keep other SQLAlchemy URLs as-is (e.g. sqlite).
        if not raw.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+asyncpg://")):
            return raw

        if raw.startswith("postgresql://"):
            raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)

        if raw.startswith("postgresql+psycopg://"):
            raw = raw.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)

        parsed = urlsplit(raw)
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        normalized: list[tuple[str, str]] = []
        for key, value in query_items:
            if key in ("channel_binding", "sslmode", "ssl"):
                continue
            normalized.append((key, value))

        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(normalized), parsed.fragment)
        )

    @property
    def database_requires_ssl(self) -> bool:
        """True if the original DATABASE_URL contained sslmode=require."""
        return "sslmode=require" in self.database_url or "ssl=require" in self.database_url

    @property
    def migration_database_requires_ssl(self) -> bool:
        src = self.direct_database_url or self.database_url
        return "sslmode=require" in src or "ssl=require" in src

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
