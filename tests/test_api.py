import unittest
from unittest.mock import patch

import api


class FakeRetrieval:
    product = "ENV130"
    selected_product = "auto"
    detected_product = "ENV130"
    product_conflict = False
    low_evidence = False

    def public_sources(self, limit=6):
        return [{"product": "ENV130", "source": "measurement.md", "chunk_index": 0, "distance": 0.1}]


class FakeEngine:
    def health(self):
        return {"status": "ok", "products": {"ENV130": {"ready": True, "count": 1}}}

    def answer_once(self, *args, **kwargs):
        return "테스트 답변", FakeRetrieval()


class ApiTests(unittest.TestCase):
    def setUp(self):
        api.app.config.update(TESTING=True)
        self.client = api.app.test_client()

    def test_health(self):
        with patch.object(api, "init", return_value=FakeEngine()):
            res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ok")

    def test_chat_requires_question(self):
        with patch.object(api, "init", return_value=FakeEngine()):
            res = self.client.post("/api/chat", json={"question": ""})
        self.assertEqual(res.status_code, 400)

    def test_chat_response_shape(self):
        with patch.object(api, "init", return_value=FakeEngine()):
            res = self.client.post("/api/chat", json={"question": "ENV130 Threshold?", "product": "auto"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["answer"], "테스트 답변")
        self.assertEqual(data["product"], "ENV130")
        self.assertIn("sources", data)


if __name__ == "__main__":
    unittest.main()
