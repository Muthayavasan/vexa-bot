"""
test_bot.py - Unit tests for ChatbotEngine and Session Management
"""

import unittest
from bot_core import ChatbotEngine


class TestChatbotEngine(unittest.TestCase):
    def setUp(self):
        self.bot = ChatbotEngine(provider="offline")

    def test_greeting_offline(self):
        reply = self.bot.chat("Hello there!")
        self.assertIn("Hello", reply)
        self.assertEqual(len(self.bot.history), 2)  # 1 user + 1 assistant

    def test_math_calculation(self):
        reply = self.bot.chat("Calculate 25 * 4 + 50")
        self.assertIn("150", reply)

    def test_context_memory_retention(self):
        self.bot.chat("First message")
        self.bot.chat("Second message")
        history = self.bot.get_history()
        self.assertEqual(len(history), 4)  # 2 user + 2 assistant
        self.assertEqual(history[0]["content"], "First message")
        self.assertEqual(history[2]["content"], "Second message")

    def test_clear_history(self):
        self.bot.chat("Hello")
        self.assertEqual(len(self.bot.history), 2)
        self.bot.clear_history()
        self.assertEqual(len(self.bot.history), 0)

    def test_set_history(self):
        custom_history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
        ]
        self.bot.set_history(custom_history)
        self.assertEqual(self.bot.get_history(), custom_history)

    def test_streaming(self):
        chunks = list(self.bot.chat_stream("Hello"))
        combined = "".join(chunks)
        self.assertTrue(len(chunks) > 1)
        self.assertIn("Hello", combined)

    def test_persona_configuration(self):
        for name, prompt in ChatbotEngine.PERSONAS.items():
            engine = ChatbotEngine(provider="offline", system_prompt=prompt)
            self.assertEqual(engine.system_prompt, prompt)

    def test_gemini_missing_key_error(self):
        gemini_bot = ChatbotEngine(provider="gemini", api_key="")
        response = gemini_bot.chat("Hello Gemini")
        self.assertIn("Gemini API key is missing", response)


if __name__ == "__main__":
    unittest.main()
