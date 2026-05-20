"""Tests for Bedrock Query-tab message formatting support."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.message_format_service import MessageFormatService
from src.services.models.llm_models import ChatMessage, MessageRole, ToolCall
from src.services.models.provider_types import ProviderType


class TestBedrockMessageFormat(unittest.TestCase):
    """Bedrock is supported by the native message format service."""

    def setUp(self):
        self.service = MessageFormatService()

    def test_bedrock_adapter_registered(self):
        """Query native-message flow can resolve Bedrock providers."""
        self.assertIn(ProviderType.BEDROCK, self.service.get_supported_providers())
        adapter = self.service.get_adapter(ProviderType.BEDROCK)
        self.assertEqual(adapter.get_provider_type(), ProviderType.BEDROCK)

    def test_bedrock_user_message_uses_normalized_storage_shape(self):
        """Bedrock user history can be created for Query tab requests."""
        message = self.service.create_user_message("Analyze main", ProviderType.BEDROCK)
        self.assertEqual(message, {"role": "user", "content": "Analyze main"})

    def test_bedrock_tool_call_uses_openai_compatible_shape(self):
        """Stored Bedrock tool calls can be parsed by Query continuation code."""
        native = self.service.to_native_format(
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="",
                tool_calls=[
                    ToolCall(id="tool-1", name="lookup_symbol", arguments={"name": "main"})
                ],
            ),
            ProviderType.BEDROCK,
        )

        self.assertEqual(native["role"], "assistant")
        self.assertEqual(native["tool_calls"][0]["type"], "function")
        self.assertEqual(native["tool_calls"][0]["function"]["name"], "lookup_symbol")
        self.assertEqual(native["tool_calls"][0]["function"]["arguments"], '{"name": "main"}')


if __name__ == '__main__':
    unittest.main()
