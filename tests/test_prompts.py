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

    def test_numeric_guardrail_for_wess_settings(self):
        prompt = build_system_prompt("ENV120", "문서 내용", "한국어")
        self.assertIn("Numeric guardrail", prompt)
        self.assertIn("voltage/current ranges", prompt)
        self.assertIn("do not repair or guess", prompt)
        self.assertIn("0.2~2.2V", prompt)

    def test_env120_prioritizes_echo_amp_before_threshold(self):
        prompt = build_system_prompt("ENV120", "문서 내용", "한국어")
        self.assertIn("prioritize Echo AMP/수신감도", prompt)
        self.assertIn("before Threshold/문턱전압", prompt)

    def test_env120_waveform_top_area_is_not_measurement_value(self):
        prompt = build_system_prompt("ENV120", "문서 내용", "한국어")
        self.assertIn("upper-left value is measurement range plus Empty", prompt)
        self.assertIn("upper-right value is Threshold/문턱전압", prompt)
        self.assertIn("not the live measurement value", prompt)
        self.assertIn("lower-left and lower-right label rule is fixed", prompt)
        self.assertIn("Distance/거리 from the sensor to the interface", prompt)
        self.assertIn("Sludge Level/슬러지 레벨, the sludge height", prompt)
        self.assertIn("glare, reflection, blur, or poor image quality", prompt)
        self.assertIn("label cannot be determined from the image", prompt)
        self.assertIn("never guess", prompt)
        self.assertIn("explain the upper-left value as the measured sludge level/distance", prompt)

    def test_conflict_message(self):
        msg = build_product_conflict_message("ENV130", "ENV200", "한국어")
        self.assertIn("ENV130", msg)
        self.assertIn("ENV200", msg)
        self.assertIn("어느 제품", msg)


if __name__ == "__main__":
    unittest.main()
