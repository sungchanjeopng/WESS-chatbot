import unittest

from wessbot.rag import WessRagEngine


class FollowupQueryTests(unittest.TestCase):
    def test_short_question_without_signal_is_followup(self):
        self.assertTrue(WessRagEngine.is_followup_question("그건 어떻게 설정해?"))
        self.assertTrue(WessRagEngine.is_followup_question("좀 더 자세히 알려줘"))

    def test_question_with_product_signal_is_not_followup(self):
        self.assertFalse(WessRagEngine.is_followup_question("ENV130 Threshold 설정 방법"))
        self.assertFalse(WessRagEngine.is_followup_question("문턱전압은 어떻게 바꿔?"))

    def test_long_question_is_not_followup(self):
        q = "설치 환경이 옥외이고 배관 외경이 200mm인 경우에 측정이 잘 되려면 어떤 조건이 필요한가요?"
        self.assertFalse(WessRagEngine.is_followup_question(q))

    def test_build_search_query_appends_recent_user_turns(self):
        history = [
            {"role": "assistant", "content": "안녕하세요."},
            {"role": "user", "content": "ENV120 수신감도 조정 방법 알려줘"},
            {"role": "assistant", "content": "Echo AMP는 ..."},
        ]
        query = WessRagEngine.build_search_query("그건 언제 조정해?", history)
        self.assertIn("ENV120 수신감도 조정 방법 알려줘", query)
        self.assertIn("그건 언제 조정해?", query)

    def test_build_search_query_keeps_standalone_question(self):
        history = [{"role": "user", "content": "ENV120 수신감도 조정 방법"}]
        question = "ENV200 EEA 보정 방법 알려줘"
        self.assertEqual(WessRagEngine.build_search_query(question, history), question)

    def test_build_search_query_without_history(self):
        question = "그건 어떻게 설정해?"
        self.assertEqual(WessRagEngine.build_search_query(question, None), question)
        self.assertEqual(WessRagEngine.build_search_query(question, []), question)

    def test_build_search_query_ignores_duplicate_current_question(self):
        history = [{"role": "user", "content": "그건 어떻게 설정해?"}]
        question = "그건 어떻게 설정해?"
        self.assertEqual(WessRagEngine.build_search_query(question, history), question)


if __name__ == "__main__":
    unittest.main()
