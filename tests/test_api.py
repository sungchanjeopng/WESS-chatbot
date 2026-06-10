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

    def test_question_length_limit(self):
        with patch.object(api, "init", return_value=FakeEngine()):
            res = self.client.post("/api/chat", json={"question": "a" * (api.MAX_QUESTION_CHARS + 1)})
        self.assertEqual(res.status_code, 400)

    def test_safe_model_rejects_unknown_models(self):
        self.assertEqual(api._safe_model("gpt-4o-expensive-custom"), api.DEFAULT_CHAT_MODEL)
        self.assertEqual(api._safe_model(None), api.DEFAULT_CHAT_MODEL)
        self.assertEqual(api._safe_model(api.DEFAULT_CHAT_MODEL), api.DEFAULT_CHAT_MODEL)

    def test_gpt55_chat_kwargs_use_temperature_one(self):
        kwargs = WessRagEngine._chat_kwargs("gpt-5.5", [{"role": "user", "content": "hi"}], 0.8)
        self.assertEqual(kwargs["temperature"], 1)

    def test_non_gpt55_chat_kwargs_keep_requested_temperature(self):
        kwargs = WessRagEngine._chat_kwargs("test-non-gpt55-model", [{"role": "user", "content": "hi"}], 0.8)
        self.assertEqual(kwargs["temperature"], 0.8)

    def test_default_answer_temperature_is_one(self):
        self.assertEqual(WessRagEngine.answer_once.__kwdefaults__["temperature"], 1.0)
        self.assertEqual(WessRagEngine.answer_once_with_images.__kwdefaults__["temperature"], 1.0)
        self.assertEqual(WessRagEngine.answer_stream.__kwdefaults__["temperature"], 1.0)

    def test_env120_image_instruction_defines_d_and_s_labels(self):
        self.assertIn("upper-left value as measurement range and Empty", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("upper-right value as Threshold/문턱전압", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("absolutely not the live measurement value", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("does not change", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("unless the Empty setting is intentionally changed", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("lower-left and lower-right label rule is fixed", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("label is D, interpret it as Distance/거리", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("label is S, interpret it as Sludge Level/슬러지 레벨", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("Do not confuse D with sludge level or S with distance", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("glare, reflection, blur, or poor image quality", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("Sludge Level = Empty - Distance", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("conditional guess", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("State the assumption clearly", IMAGE_ANALYSIS_INSTRUCTION)
        self.assertIn("needed numbers are not legible", IMAGE_ANALYSIS_INSTRUCTION)


if __name__ == "__main__":
    unittest.main()
