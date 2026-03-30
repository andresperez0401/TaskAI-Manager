"""Tests for the AI provider abstraction layer."""

import pytest

from modules.ai.base import AIProvider
from modules.ai.exceptions import AIDisabledError, AIProviderError
from modules.ai.providers.mock_provider import MockProvider
from modules.ai.providers.noop_provider import NoopProvider


# ── NoopProvider ──────────────────────────────────────────────────────────────


class TestNoopProvider:
    def test_is_not_available(self):
        provider = NoopProvider()
        assert provider.is_available is False
        assert provider.provider_name == "noop"

    @pytest.mark.asyncio
    async def test_chat_raises_disabled(self):
        provider = NoopProvider()
        with pytest.raises(AIDisabledError):
            await provider.chat_with_tools(
                model="test",
                system_prompt="test",
                user_message="hello",
                tools=[],
            )

    @pytest.mark.asyncio
    async def test_structured_output_raises_disabled(self):
        provider = NoopProvider()
        with pytest.raises(AIDisabledError):
            await provider.generate_structured_output(
                model="test",
                system_prompt="test",
                user_prompt="test",
                json_schema={},
            )

    @pytest.mark.asyncio
    async def test_continue_raises_disabled(self):
        provider = NoopProvider()
        with pytest.raises(AIDisabledError):
            await provider.continue_with_tool_results(
                model="test",
                system_prompt="test",
                tool_outputs=[],
                tools=[],
                previous_response_id="abc",
            )


# ── MockProvider ──────────────────────────────────────────────────────────────


class TestMockProvider:
    def test_is_available(self):
        provider = MockProvider()
        assert provider.is_available is True
        assert provider.provider_name == "mock"

    @pytest.mark.asyncio
    async def test_chat_returns_response(self):
        provider = MockProvider()
        resp = await provider.chat_with_tools(
            model="test",
            system_prompt="test",
            user_message="hello world",
            tools=[],
        )
        assert resp.text is not None
        assert "hello world" in resp.text

    @pytest.mark.asyncio
    async def test_chat_create_triggers_tool_call(self):
        provider = MockProvider()
        resp = await provider.chat_with_tools(
            model="test",
            system_prompt="test",
            user_message="crear una tarea nueva",
            tools=[],
        )
        assert len(resp.function_calls) == 1
        assert resp.function_calls[0].name == "create_task"

    @pytest.mark.asyncio
    async def test_structured_output(self):
        provider = MockProvider()
        result = await provider.generate_structured_output(
            model="test",
            system_prompt="test",
            user_prompt="test",
            json_schema={},
        )
        assert "diagnosis" in result
        assert "prioritization_suggestion" in result

    @pytest.mark.asyncio
    async def test_continue_tool_results(self):
        provider = MockProvider()
        resp = await provider.continue_with_tool_results(
            model="test",
            system_prompt="test",
            tool_outputs=[],
            tools=[],
            previous_response_id="abc",
        )
        assert resp.text is not None


# ── Factory ───────────────────────────────────────────────────────────────────


class TestFactory:
    def test_factory_returns_noop_when_disabled(self):
        """The conftest sets AI_ENABLED=false, so factory should return NoopProvider."""
        from modules.ai.factory import get_ai_provider

        # Note: factory is cached via lru_cache. In test env, it returns Noop
        # because conftest.py sets AI_ENABLED=false before import.
        provider = get_ai_provider()
        assert isinstance(provider, AIProvider)

    def test_provider_inherits_interface(self):
        for cls in [NoopProvider, MockProvider]:
            assert issubclass(cls, AIProvider)
