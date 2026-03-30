from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = "global"


class AgentAction(BaseModel):
    tool_name: str
    arguments: dict
    result: dict


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentChatResponse(BaseModel):
    """Extended response with resilience fields."""

    success: bool = True
    provider_available: bool = True
    fallback_mode: bool = False
    answer: str
    message: str | None = None
    actions: list[AgentAction] = Field(default_factory=list)
    history: list[AgentMessage] = Field(default_factory=list)
    data: dict | None = None
    error: dict | None = None
