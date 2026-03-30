from collections import defaultdict
from dataclasses import dataclass, field

from modules.agent.schemas import AgentMessage


@dataclass
class ConversationState:
    previous_response_id: str | None = None
    history: list[AgentMessage] = field(default_factory=list)


class AgentMemoryStore:
    def __init__(self):
        self._store: dict[str, ConversationState] = defaultdict(ConversationState)

    def get(self, session_id: str) -> ConversationState:
        return self._store[session_id]

    def append(self, session_id: str, role: str, content: str) -> None:
        state = self._store[session_id]
        state.history.append(AgentMessage(role=role, content=content))

    def set_previous_response_id(self, session_id: str, response_id: str | None) -> None:
        state = self._store[session_id]
        state.previous_response_id = response_id

    def clear(self, session_id: str = "global") -> None:
        self._store[session_id] = ConversationState()


agent_memory = AgentMemoryStore()
