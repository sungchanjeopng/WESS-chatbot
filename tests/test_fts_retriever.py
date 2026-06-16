import tempfile
import unittest
from pathlib import Path

from wessbot.fts_retriever import FtsRetriever
from wessbot.ingest import SourceGroup


class FtsRetrieverTests(unittest.TestCase):
    def test_builds_index_from_markdown_without_openai_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "env200.md"
            doc.write_text("ENV200 EEA 보정 절차\n4-20mA 출력 설정과 릴레이 알람 설명", encoding="utf-8")
            groups = [SourceGroup("ENV200", "test_env200", (root,))]

            retriever = FtsRetriever(source_groups=groups)
            health = retriever.health()

            self.assertEqual(health["products"]["ENV200"]["count"], 1)
            chunks = retriever.query("EEA 보정 방법", product_keys=["ENV200"], n_results=3)
            self.assertTrue(chunks)
            self.assertEqual(chunks[0].product, "ENV200")
            self.assertIn("EEA", chunks[0].document)


if __name__ == "__main__":
    unittest.main()
