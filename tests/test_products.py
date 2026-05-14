import unittest

from wessbot.products import detect_product, normalize_product, question_needs_context


class ProductDetectionTests(unittest.TestCase):
    def test_legacy_api_keys_normalize(self):
        self.assertEqual(normalize_product("density"), "ENV200")
        self.assertEqual(normalize_product("interface"), "ENV130")
        self.assertEqual(normalize_product("interface_120"), "ENV120")
        self.assertEqual(normalize_product("auto"), "auto")

    def test_detect_explicit_product(self):
        product, conflict, scores = detect_product("ENV130 Threshold 설정 방법 알려줘", "auto")
        self.assertEqual(product, "ENV130")
        self.assertFalse(conflict)
        self.assertGreater(scores["ENV130"], scores["ENV200"])

    def test_detect_selected_conflict(self):
        product, conflict, _ = detect_product("ENV200 EEA 보정 방법", "interface")
        self.assertEqual(product, "ENV200")
        self.assertTrue(conflict)

    def test_context_question_detection(self):
        self.assertTrue(question_needs_context("측정값이 계속 튀어요"))
        self.assertFalse(question_needs_context("ENV200 제품 소개해줘"))


if __name__ == "__main__":
    unittest.main()
