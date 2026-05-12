import unittest

from wessbot.ingest import chunk_text


class ChunkingTests(unittest.TestCase):
    def test_chunk_text_preserves_short_text(self):
        self.assertEqual(chunk_text("A\nB", chunk_size=100), ["A\nB"])

    def test_chunk_text_splits_long_text(self):
        text = "\n".join([f"line {i} " + "x" * 40 for i in range(20)])
        chunks = chunk_text(text, chunk_size=180, overlap=50)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
