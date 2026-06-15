import unittest
from unittest.mock import patch

from wessbot.codex_oauth import (
    DEFAULT_CODEX_REASONING_EFFORT,
    DEFAULT_CODEX_FALLBACK_MODELS,
    CodexOAuthError,
    CodexOAuthChatClient,
    messages_to_codex_payload,
)


class CodexOAuthTests(unittest.TestCase):
    def test_messages_to_codex_payload_extracts_system_as_instructions(self):
        instructions, input_items = messages_to_codex_payload(
            [
                {"role": "system", "content": "rules"},
                {"role": "user", "content": "question"},
                {"role": "assistant", "content": "answer"},
            ]
        )
        self.assertEqual(instructions, "rules")
        self.assertEqual(input_items, [{"role": "user", "content": "question"}, {"role": "assistant", "content": "answer"}])

    def test_messages_to_codex_payload_rejects_images(self):
        with self.assertRaises(CodexOAuthError):
            messages_to_codex_payload(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "look"},
                            {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}},
                        ],
                    }
                ]
            )

    def test_default_reasoning_effort_is_xhigh(self):
        self.assertEqual(DEFAULT_CODEX_REASONING_EFFORT, "xhigh")
        self.assertEqual(CodexOAuthChatClient().reasoning_effort, "xhigh")

    def test_default_codex_fallback_is_gpt54(self):
        self.assertEqual(DEFAULT_CODEX_FALLBACK_MODELS, ("gpt-5.4",))
        self.assertEqual(CodexOAuthChatClient()._candidate_models("gpt-5.5"), ("gpt-5.5", "gpt-5.4"))

    def test_complete_chat_collects_stream_deltas(self):
        client = CodexOAuthChatClient()
        with patch.object(
            client,
            "stream_chat",
            return_value=[
                type("Chunk", (), {"choices": [type("Choice", (), {"delta": type("Delta", (), {"content": "O"})()})()]})(),
                type("Chunk", (), {"choices": [type("Choice", (), {"delta": type("Delta", (), {"content": "K"})()})()]})(),
            ],
        ):
            self.assertEqual(client.complete_chat(model="gpt-5.5", messages=[{"role": "user", "content": "x"}]), "OK")


if __name__ == "__main__":
    unittest.main()
