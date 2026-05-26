import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from orchestrator.response_style_validator import sanitize_and_validate_output, StreamFilter

class TestStreamSanitization(unittest.TestCase):
    def test_single_final_output_gate_valid(self):
        # A perfectly clean response should remain unchanged
        text = "VSCode opened."
        self.assertEqual(sanitize_and_validate_output(text), "VSCode opened.")

    def test_single_final_output_gate_fallback(self):
        # Prohibited theatrical strings should be intercepted and clean fallback returned
        violation1 = "Initiating protocols... Greetings human!"
        violation2 = "Identity verification complete. Here is your calculator."
        
        self.assertEqual(sanitize_and_validate_output(violation1), "Hello.")
        self.assertEqual(sanitize_and_validate_output(violation2), "Calculator opened.")

    def test_stream_filter_lookahead_holds_prefix(self):
        sf = StreamFilter()
        # Feed partial prohibited pattern in chunks
        chunk1 = "Init"
        chunk2 = "iating"
        
        # Should hold back prefix (returns empty)
        self.assertEqual(sf.feed_and_filter(chunk1), "")
        self.assertEqual(sf.feed_and_filter(chunk2), "")

    def test_stream_filter_converts_prohibited_stream(self):
        sf = StreamFilter()
        
        # Stream a whole bad greeting phrase chunk-by-chunk
        # "Greetings human"
        self.assertEqual(sf.feed_and_filter("Greet"), "")
        self.assertEqual(sf.feed_and_filter("ings "), "")
        self.assertEqual(sf.feed_and_filter("hum"), "")
        
        # When completed, the filter identifies the pattern and returns the clean fallback delta/value
        final_delta = sf.feed_and_filter("an.")
        self.assertEqual(final_delta, "Hello.")

    def test_stream_filter_normal_flow_emits_directly(self):
        sf = StreamFilter()
        # Non-prohibited words should emit immediately
        self.assertEqual(sf.feed_and_filter("The"), "The")
        self.assertEqual(sf.feed_and_filter(" port"), " port")
        self.assertEqual(sf.feed_and_filter(" is"), " is")
        self.assertEqual(sf.feed_and_filter(" active."), " active.")

    def test_stream_filter_releases_on_safe_completion(self):
        sf = StreamFilter()
        
        # If we feed something that matches a prohibited prefix but then branches to something safe,
        # it should release the buffer immediately
        self.assertEqual(sf.feed_and_filter("advanced"), "")
        self.assertEqual(sf.feed_and_filter(" config"), "advanced config")

if __name__ == "__main__":
    unittest.main()
