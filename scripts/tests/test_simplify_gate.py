import unittest
import sys
import os
from pathlib import Path

from scripts.hooks.simplify_gate import (
    matched_severity,
    main
)


class TestSimplifyGate(unittest.TestCase):

    def test_matched_severity(self):
        # 1. Hard verbs matching
        sev, verb = matched_severity("please ship these changes")
        self.assertEqual(sev, "hard")
        self.assertEqual(verb.lower(), "ship")
        
        sev, verb = matched_severity("time to deploy to production")
        self.assertEqual(sev, "hard")
        self.assertEqual(verb.lower(), "deploy")
        
        sev, verb = matched_severity("please pr this branch")
        self.assertEqual(sev, "hard")
        self.assertEqual(verb.lower(), "pr")

        # 2. Soft verbs matching
        sev, verb = matched_severity("commit the files now")
        self.assertEqual(sev, "soft")
        self.assertEqual(verb.lower(), "commit")
        
        sev, verb = matched_severity("ready to release version 1.0")
        self.assertEqual(sev, "soft")
        self.assertEqual(verb.lower(), "release")

        # 3. Negations & Exclusions (no match)
        sev, verb = matched_severity("do not ship these files")
        self.assertEqual(sev, "")
        self.assertEqual(verb, "")
        
        sev, verb = matched_severity("ship on wednesday")
        self.assertEqual(sev, "")
        self.assertEqual(verb, "")

    def test_main_hook_bypass_and_no_match(self):
        # Empty args should bypass
        payload = {"args": ""}
        self.assertEqual(main("pre-tool", payload), 0)

        # No match should bypass
        payload = {"args": "just run unit tests"}
        self.assertEqual(main("pre-tool", payload), 0)
        
        # APPROVED prefix bypass
        payload = {"args": "APPROVED: ship changes immediately"}
        self.assertEqual(main("pre-tool", payload), 0)

        # CK_SIMPLIFY_DISABLED env bypass
        os.environ["CK_SIMPLIFY_DISABLED"] = "1"
        payload = {"args": "ship changes immediately"}
        self.assertEqual(main("pre-tool", payload), 0)
        del os.environ["CK_SIMPLIFY_DISABLED"]


if __name__ == "__main__":
    unittest.main()
