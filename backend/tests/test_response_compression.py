import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from orchestrator.response_compressor import response_compressor

class TestResponseCompression(unittest.TestCase):
    def test_greetings_shortened(self):
        # Greetings <= 2-4 words
        res = response_compressor.compress_response("Hello! How can I assist you today?", "hello")
        self.assertEqual(res, "Hello.")
        
        res2 = response_compressor.compress_response("Hey there, how are you?", "hey")
        self.assertEqual(res2, "Hey.")
        
    def test_calculator_numeric_only(self):
        # Calculator outputs numeric only
        res = response_compressor.compress_response("The calculation result is 60.", "5*12")
        self.assertEqual(res, "60")
        
        res2 = response_compressor.compress_response("I have calculated that 5 * 12 equals 60.", "calculate 5*12")
        self.assertEqual(res2, "60")
        
    def test_launcher_concise(self):
        # Launcher outputs concise
        res = response_compressor.compress_response("I have successfully launched visual studio code for you.", "open vscode")
        self.assertEqual(res, "Opening VSCode.")
        
        res2 = response_compressor.compress_response("Certainly, let me open chrome.", "open chrome")
        self.assertEqual(res2, "Opening Chrome.")
        
    def test_no_filler_phrases(self):
        # No filler phrases survive
        text = "within this context I can tell you that it is recognized and understood."
        res = response_compressor.compress_response(text, "what is this")
        self.assertNotIn("within this context", res.lower())
        self.assertNotIn("recognized and understood", res.lower())
        
        text2 = "at this moment, based on your request, no further action required."
        res2 = response_compressor.compress_response(text2, "status")
        self.assertNotIn("at this moment", res2.lower())
        self.assertNotIn("no further action required", res2.lower())
        self.assertNotIn("based on your request", res2.lower())

    def test_no_paragraphs_for_trivial(self):
        text = "I have checked the system clock. The current time is 14:05. Please let me know if you need anything else."
        res = response_compressor.compress_response(text, "what time is it")
        # Utility should return just the time, e.g. "2:05 PM"
        self.assertTrue(res.endswith("M") or ":" in res)
        self.assertTrue(len(res.split()) <= 4)
        
    def test_yes_no(self):
        res = response_compressor.compress_response("Yes, I can confirm that is the case.", "yes")
        self.assertEqual(res, "Yes.")
        
        res2 = response_compressor.compress_response("No, that is not possible.", "no")
        self.assertEqual(res2, "No.")

if __name__ == '__main__':
    unittest.main()
