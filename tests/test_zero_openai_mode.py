import os
import unittest
from unittest.mock import patch

from wessbot.rag import RetrievedChunk, WessRagEngine


class FakeRetriever:
    def health(self):
        return {"status": "ok", "products": {"ENV200": {"ready": True, "count": 1}}}

    def query(self, query, *, product_keys, n_results):
        return [
            RetrievedChunk(
                product="ENV200",
                collection="fts_env200",
                document="ENV200 EEA 보정은 메뉴에서 실행합니다.",
                source="manual.md",
                chunk_index=0,
                distance=None,
                keyword_score=2,
                combined_score=2.0,
            )
        ]


class FakeCodexClient:
    def __init__(self):
        self.messages = None

    def complete_chat(self, *, messages, model):
        self.messages = messages
        return "Codex OAuth answer"

    def stream_chat(self, *, messages, model):
        self.messages = messages
        yield type("Chunk", (), {"choices": [type("Choice", (), {"delta": type("Delta", (), {"content": "Codex stream"})()})()]})()


class ZeroOpenAiRagTests(unittest.TestCase):
    def test_codex_oauth_chat_and_fts_retrieval_do_not_require_openai_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            engine = WessRagEngine(
                retrieval_provider="fts",
                chat_provider="codex_oauth",
                retriever=FakeRetriever(),
            )
            fake_codex = FakeCodexClient()
            engine.codex_chat_client = fake_codex

            answer, retrieval = engine.answer_once("EEA 보정 방법?", product="ENV200")

        self.assertEqual(answer, "Codex OAuth answer")
        self.assertEqual(retrieval.product, "ENV200")
        self.assertIsNotNone(fake_codex.messages)
        self.assertTrue(any("EEA" in str(m["content"]) for m in fake_codex.messages))
        self.assertEqual(engine.health()["retrieval_provider"], "fts")
        self.assertFalse(engine.health()["openai_ready"])


if __name__ == "__main__":
    unittest.main()
