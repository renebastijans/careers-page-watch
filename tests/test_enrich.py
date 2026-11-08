import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import enrich as e, common

CFG = dict(common.DEFAULTS, eligible_places=["Spain", "Madrid"])
KEY = e.build_key(CFG); SIG = e.build_title_signal(CFG)
OFFICE_FIRST = ("This role is based out of our example office. We are an office-first company and value in-person "
                "collaboration; we do not offer remote-only roles.")   # synthetic

class PolicyLines(unittest.TestCase):
    def test_office_first_is_kept_whole(self):
        lines = e.extract_policy_lines(OFFICE_FIRST, KEY)
        self.assertEqual(len(lines), 2)
        self.assertIn("office-first", lines[1])

    def test_eligibility_is_kept(self):
        t = "We value curiosity and care. This role is open to candidates in Spain, France and Germany."
        self.assertEqual(e.extract_policy_lines(t, KEY), ["This role is open to candidates in Spain, France and Germany."])

    def test_places_come_from_config(self):
        t = "This role is open to candidates in Spain, France and Germany."
        other = e.build_key(dict(CFG, eligible_places=["Canada"], place_synonyms=[]))
        self.assertEqual(e.extract_policy_lines(t, other), [])
        self.assertEqual(len(e.extract_policy_lines("Open to candidates in Canada.", other)), 1)

    def test_unrelated_sentences_are_dropped(self):
        self.assertEqual(e.extract_policy_lines("We build tools that people love. You will own the roadmap.", KEY), [])

    def test_officer_is_not_office(self):
        self.assertEqual(e.extract_policy_lines("You will report to the Chief Executive Officer directly.", KEY), [])

    def test_length_bounds(self):
        self.assertEqual(e.extract_policy_lines("Remote.", KEY), [])
        self.assertEqual(e.extract_policy_lines("remote " * 80, KEY), [])

    def test_duplicates_removed_and_capped_at_12(self):
        self.assertEqual(len(e.extract_policy_lines("Fully remote across Europe.\n" * 3, KEY)), 1)
        many = "\n".join(f"Remote option number {i} applies to Europe." for i in range(30))
        self.assertEqual(len(e.extract_policy_lines(many, KEY)), 12)

    def test_empty_text_gives_no_lines(self):
        self.assertEqual(e.extract_policy_lines("", KEY), [])

class ShortCapitalWords(unittest.TestCase):
    """A US user's place words include "US": it must not match the ordinary word "us"."""
    US = dict(common.DEFAULTS, eligible_places=["San Francisco", "SF", "USA", "US"], place_synonyms=["Americas"])

    def test_us_does_not_match_the_word_us(self):
        key = e.build_key(self.US)
        self.assertEqual(e.extract_policy_lines("Join us and help us build tools that people love.", key), [])
        self.assertEqual(len(e.extract_policy_lines("This is a remote opportunity within the US.", key)), 1)

    def test_other_short_words_are_case_sensitive_too(self):
        cfg = dict(common.DEFAULTS, eligible_places=["SF", "UK"], place_synonyms=[])
        key = e.build_key(cfg)
        self.assertEqual(e.extract_policy_lines("Our UK office is open to everyone who likes sf stories.", key), ["Our UK office is open to everyone who likes sf stories."])
        self.assertEqual(e.extract_policy_lines("We care about sf stories in our newsletter, sorry.", key), [])

    def test_longer_words_stay_case_insensitive(self):
        cfg = dict(self.US, eligible_places=self.US["eligible_places"] + ["Bay Area"])
        self.assertEqual(len(e.extract_policy_lines("Hybrid in the bay area, with remote days.", e.build_key(cfg))), 1)

class TitleSignal(unittest.TestCase):
    def test_true_cases(self):
        for t in ["Senior Researcher (Remote, EU)", "Research Lead, EMEA", "Insights Lead - Madrid", "Senior Researcher, Spain"]:
            self.assertTrue(e.title_remote_signal(t, SIG), t)

    def test_false_cases(self):
        for t in ["Senior User Researcher", "Head of GTM, Research Services", "Principal Security Researcher"]:
            self.assertFalse(e.title_remote_signal(t, SIG), t)

    def test_none_and_empty(self):
        self.assertFalse(e.title_remote_signal(None, SIG))
        self.assertFalse(e.title_remote_signal("", SIG))

class Hash(unittest.TestCase):
    def test_stable_and_sensitive(self):
        a = e.policy_hash(["Remote in Spain."])
        self.assertEqual(a, e.policy_hash(["Remote in Spain."]))
        self.assertNotEqual(a, e.policy_hash(["Remote in France."]))
        self.assertEqual(len(a), 12)

class TextOf(unittest.TestCase):
    def test_strips_markup_script_and_entities(self):
        raw = "<p>Fully remote &amp; flexible</p><script>var x='remote';</script><ul><li>Madrid hub</li></ul>"
        t = e.text_of(raw)
        self.assertIn("Fully remote & flexible", t)
        self.assertIn("Madrid hub", t)
        self.assertNotIn("var x", t)
        self.assertNotIn("<", t)

class Enrich(unittest.TestCase):
    def test_adds_three_fields_and_keeps_others(self):
        c = e.enrich({"title": "Senior Researcher (Remote, EU)", "company": "X"}, OFFICE_FIRST, CFG)
        self.assertEqual(c["company"], "X")
        self.assertTrue(c["title_remote_signal"])
        self.assertEqual(len(c["policy_lines"]), 2)
        self.assertEqual(c["policy_hash"], e.policy_hash(c["policy_lines"]))

if __name__ == "__main__":
    unittest.main()
