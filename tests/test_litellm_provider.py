"""Regression tests for LiteLLM/Bedrock compatibility handling."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.llm_providers import litellm_provider as litellm_module
from src.services.llm_providers.litellm_provider import LiteLLMProvider
from src.services.models.llm_models import (
    ChatMessage,
    ChatRequest,
    MessageRole,
    ToolCall,
)
from src.services.settings_service import SettingsService


def make_provider(model="bedrock.openai.gpt-5.6-sol", reasoning_effort="none"):
    """Create a provider without constructing a real OpenAI client."""
    provider = object.__new__(LiteLLMProvider)
    provider.model = model
    provider.model_family = provider._detect_model_family()
    provider.is_bedrock = provider._is_bedrock_model()
    provider.config = {"reasoning_effort": reasoning_effort}
    provider.max_tokens = 4096
    return provider


class FakeBadRequestError(Exception):
    pass


class RecordingCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            raise FakeBadRequestError(
                "This model doesn't support the temperature field."
            )
        return "ok"


class LiteLLMCompatibilityTests(unittest.TestCase):
    def test_dotted_bedrock_model_group_is_detected(self):
        provider = make_provider()

        self.assertTrue(provider.is_bedrock)
        self.assertEqual(provider.model_family, "openai")
        settings = object.__new__(SettingsService)
        self.assertTrue(settings._is_bedrock_model("BEDROCK.openai.gpt-5.6-sol"))

    def test_dotted_bedrock_gpt_reasoning_model_omits_temperature(self):
        provider = make_provider()
        request = ChatRequest(
            messages=[ChatMessage(MessageRole.USER, "test")],
            model=provider.model,
            temperature=0.7,
        )

        kwargs = provider._prepare_completion_kwargs(request)

        self.assertIn("max_completion_tokens", kwargs)
        self.assertNotIn("max_tokens", kwargs)
        self.assertNotIn("temperature", kwargs)

    def test_thinking_metadata_is_not_forwarded_to_openai_family(self):
        provider = make_provider(reasoning_effort="high")
        message = ChatMessage(
            MessageRole.ASSISTANT,
            "answer",
            native_content={
                "thinking_blocks": [{"type": "thinking", "thinking": "hidden"}],
                "reasoning_content": "hidden",
            },
        )

        prepared = provider._prepare_messages([message])

        self.assertNotIn("thinking_blocks", prepared[0])
        self.assertNotIn("reasoning_content", prepared[0])

    def test_tool_history_keeps_one_result_per_adjacent_call(self):
        provider = make_provider("bedrock.anthropic.claude-opus-4-6")
        messages = [
            ChatMessage(
                MessageRole.ASSISTANT,
                "",
                tool_calls=[
                    ToolCall("call-a", "lookup", {"name": "a"}),
                    ToolCall("call-b", "lookup", {"name": "b"}),
                ],
            ),
            ChatMessage(MessageRole.TOOL, "first", tool_call_id="call-a", name="lookup"),
            ChatMessage(MessageRole.TOOL, "duplicate", tool_call_id="call-a", name="lookup"),
            ChatMessage(MessageRole.TOOL, "orphan", tool_call_id="call-c", name="lookup"),
        ]

        prepared = provider._prepare_messages(messages)

        self.assertEqual(len(prepared), 2)
        self.assertEqual(
            [call["id"] for call in prepared[0]["tool_calls"]],
            ["call-a"],
        )
        self.assertEqual(prepared[1]["tool_call_id"], "call-a")
        self.assertEqual(prepared[1]["content"], "first")

    def test_orphan_named_tool_result_gets_matching_synthetic_call(self):
        provider = make_provider("bedrock.anthropic.claude-opus-4-6")
        result = ChatMessage(
            MessageRole.TOOL,
            "result",
            tool_call_id="call-a",
            name="lookup",
        )

        prepared = provider._prepare_messages([result])

        self.assertEqual(len(prepared), 2)
        self.assertEqual(prepared[0]["tool_calls"][0]["id"], "call-a")
        self.assertEqual(prepared[1]["tool_call_id"], "call-a")

    def test_thinking_rejection_removes_reasoning_and_stored_metadata(self):
        kwargs = {
            "model": "bedrock.openai.gpt-5.6-sol",
            "reasoning_effort": "high",
            "extra_body": {"thinking": {"type": "enabled"}, "trace": True},
            "messages": [{
                "role": "assistant",
                "content": "answer",
                "thinking_blocks": [{"type": "thinking"}],
                "reasoning_content": "hidden",
            }],
        }

        retry, removed = LiteLLMProvider._compatibility_retry_kwargs(
            kwargs, "Unknown parameter: 'thinking'"
        )

        self.assertIn("reasoning_effort", removed)
        self.assertIn("extra_body.thinking", removed)
        self.assertNotIn("reasoning_effort", retry)
        self.assertEqual(retry["extra_body"], {"trace": True})
        self.assertNotIn("thinking_blocks", retry["messages"][0])
        self.assertNotIn("reasoning_content", retry["messages"][0])

    def test_bad_request_retries_once_without_temperature(self):
        provider = make_provider()
        completions = RecordingCompletions()
        provider._client = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )

        with patch.object(litellm_module.openai, "BadRequestError", FakeBadRequestError):
            result = provider._create_completion_with_compatibility({
                "model": provider.model,
                "messages": [{"role": "user", "content": "test"}],
                "temperature": 0.7,
            })

        self.assertEqual(result, "ok")
        self.assertEqual(len(completions.calls), 2)
        self.assertIn("temperature", completions.calls[0])
        self.assertNotIn("temperature", completions.calls[1])


if __name__ == "__main__":
    unittest.main()
