import unittest

from wessbot.prompts import build_system_prompt, build_product_conflict_message


class PromptTests(unittest.TestCase):
    def test_prompt_contains_product_specific_forbidden_terms(self):
        prompt = build_system_prompt("ENV200", "문서 내용", "한국어")
        self.assertIn("ENV200", prompt)
        self.assertIn("EEA", prompt)
        self.assertIn("Threshold/문턱전압", prompt)
        self.assertIn("반드시 한국어", prompt)

    def test_env130_prompt_mentions_channel(self):
        prompt = build_system_prompt("ENV130", "문서 내용", "English")
        self.assertIn("CH1", prompt)
        self.assertIn("CH2", prompt)
        self.assertIn("Answer only in English", prompt)

    def test_conflict_message(self):
        msg = build_product_conflict_message("ENV130", "ENV200", "한국어")
        self.assertIn("ENV130", msg)
        self.assertIn("ENV200", msg)
        self.assertIn("어느 제품", msg)


if __name__ == "__main__":
    unittest.main()
