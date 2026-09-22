import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from qualify_openrouter import final_content


class ProviderProbeTests(unittest.TestCase):
    def test_reasoning_only_is_not_a_final_response(self):
        self.assertEqual(final_content({"content": None, "reasoning_content": "thinking"}), "")

    def test_final_content_is_preserved(self):
        self.assertEqual(final_content({"content": "C3R_OK", "reasoning_content": "thinking"}), "C3R_OK")


if __name__ == "__main__":
    unittest.main()
