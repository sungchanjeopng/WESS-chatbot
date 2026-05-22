import unittest
from unittest.mock import patch

import api
from wessbot.rag import IMAGE_ANALYSIS_INSTRUCTION, WessRagEngine


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

    def answer_once_with_images(self, *args, **kwargs):
        return "이미지 테스트 답변", FakeRetrieval()


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

    def test_chat_accepts_image_data_urls(self):
        payload = {
            "question": "파형 분석해줘",
            "product": "ENV120",
            "image_data_urls": ["data:image/png;base64,iVBORw0KGgo="],
        }
        with patch.object(api, "init", return_value=FakeEngine()):
            res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["answer"], "이미지 테스트 답변")

    def test_gpt55_chat_kwargs_use_temperature_one(self):
        kwargs = WessRagEngine._chat_kwargs("gpt-5.5", [{"role": "user", "content": "hi"}], 0.8)
        self.assertEqual(kwargs["temperature"], 1)

    def test_other_chat_kwargs_keep_temperature(self):
        kwargs = WessRagEngine._chat_kwargs("gpt-5.4", [{"role": "user", "content": "hi"}], 0.8)
        self.assertEqual(kwargs["temperature"], 0.8)

    def test_default_answer_temperature_is_point_two(self):
        self.assertEqual(WessRagEngine.answer_once.__kwdefaults__["temperature"], 0.2)
        self.assertEqual(WessRagEngine.answer_once_with_images.__kwdefaults__["temperature"], 0.2)
        self.assertEqual(WessRagEngine.answer_stream.__kwdefaults__["temperature"], 0.2)

    def test_env120_image_instruction_defines_d_and_s_labels(self):
        self.assertIn("top area/scale as Empty and the measurement range", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("does not change", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("unless the Empty setting is intentionally changed", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("D = Distance/거리", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("S = Sludge Level/슬러지 레벨", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("Do not confuse D with sludge level or S with distance", IMAGE_ANALYSIS_INSTRUCTION)


if __name__ == "__main__":
    unittest.main()
