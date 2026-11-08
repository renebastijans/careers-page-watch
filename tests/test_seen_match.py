import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from seen_match import find_seen, squash

SEEN = {
    "https://jobs.ashbyhq.com/acme/aaa": {"status": "dropped", "code": "onsite-required", "reason": "x",
                                         "company": "Acme", "title": "Senior User Researcher"},
    "https://jobs.ashbyhq.com/globex/bbb": {"status": "dropped", "code": "not-research", "reason": "x",
                                           "company": "Globex", "title": "[not recorded]"},
}

class Match(unittest.TestCase):
    def test_same_url(self):
        self.assertEqual(find_seen("https://jobs.ashbyhq.com/acme/aaa", "Acme", "x", SEEN)[0], "same-url")

    def test_repost_new_url_same_title(self):
        k, u, e = find_seen("https://jobs.ashbyhq.com/acme/zzz", "ACME", "senior user researcher", SEEN)
        self.assertEqual((k, u, e["code"]), ("repost", "https://jobs.ashbyhq.com/acme/aaa", "onsite-required"))

    def test_retitled_ad_is_new(self):
        self.assertIsNone(find_seen("https://jobs.ashbyhq.com/acme/zzz", "Acme", "Senior Researcher", SEEN))

    def test_new_company(self):
        self.assertIsNone(find_seen("https://x.example/1", "Initech", "Senior User Researcher", SEEN))

    def test_unrecorded_title_never_matches(self):
        self.assertIsNone(find_seen("https://jobs.ashbyhq.com/globex/new", "Globex", "[not recorded]", SEEN))

    def test_blank_fields_never_match(self):
        self.assertIsNone(find_seen("https://x.example/2", "", "", SEEN))

    def test_squash(self):
        self.assertEqual(squash("Head of GTM, Research & Services"), "headofgtmresearchandservices")

if __name__ == "__main__":
    unittest.main()
