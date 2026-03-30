from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    request_id: str | None = None


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorBody


class AIHealthData(BaseModel):
    ai_enabled: bool
    provider: str
    model: str
    configured: bool
    provider_available: bool
    can_chat: bool
    allow_fallback: bool
    error: dict | None = None


class AIHealthResponse(BaseModel):
    data: AIHealthData
    meta: ApiMeta = Field(default_factory=ApiMeta)


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = "global"


class AIChatResponseData(BaseModel):
    success: bool
    provider_available: bool
    fallback_mode: bool
    answer: str
    actions: list[dict] = Field(default_factory=list)
    tasks_changed: list[dict] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)
    error: dict | None = None


class AIChatResponse(BaseModel):
    data: AIChatResponseData
    meta: ApiMeta = Field(default_factory=ApiMeta)


class AIProviderTestRequest(BaseModel):
    message: str = Field(default="Responde con OK")


class AIProviderTestResponse(BaseModel):
    data: dict
    meta: ApiMeta = Field(default_factory=ApiMeta)
