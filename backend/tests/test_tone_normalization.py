import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from orchestrator.response_cleaner import response_cleaner
from orchestrator.response_style_validator import response_style_validator

class TestToneNormalization(unittest.TestCase):
    def test_cleaner_sci_fi_phrases(self):
        # Sci-fi / protocol phrases should be stripped
        bad_responses = [
            "Initiating protocols... Visual Studio Code is opening.",
            "greetings human! VSCode opened.",
            "Identity verification successful. Calculator opened.",
            "Executing cognitive remediation workflow. VSCode opened."
        ]
        for resp in bad_responses:
            cleaned = response_cleaner.clean(resp)
            self.assertNotIn("protocols", cleaned.lower())
            self.assertNotIn("greetings", cleaned.lower())
            self.assertNotIn("identity", cleaned.lower())
            self.assertNotIn("cognitive", cleaned.lower())
            self.assertIn(cleaned, ["VSCode opened.", "Calculator opened."])

    def test_validator_prohibited_patterns(self):
        # Prohibited phrases should fail style validation
        bad_phrases = [
            "Analyzing your request through layered cognition.",
            "Initiating protocols for backup.",
            "Greetings human user. System is online.",
            "Identity verification complete."
        ]
        for phrase in bad_phrases:
            self.assertFalse(response_style_validator.validate(phrase))

    def test_validator_good_patterns(self):
        # Calm, precise engineer phrases should pass style validation
        good_phrases = [
            "VSCode opened.",
            "Backend restarted.",
            "WebSocket connection restored.",
            "That error is coming from Vite.",
            "I found the issue."
        ]
        for phrase in good_phrases:
            self.assertTrue(response_style_validator.validate(phrase))

    def test_adaptive_verbosity(self):
        # Simple tasks should scale down to very concise replies
        res = response_cleaner.clean("I have successfully opened the Visual Studio Code application inside your workspace environment.")
        self.assertEqual(res, "VSCode opened.")

if __name__ == "__main__":
    unittest.main()
