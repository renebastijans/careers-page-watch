import csv, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "templates"
ATS = {"ashby", "greenhouse", "lever", "workable", "smartrecruiters", "teamtailor", "skip", "browser", "unknown"}
COLS = ["name", "sector", "size", "ats", "slug", "last_checked", "notes"]

def rows():
    with open(T / "companies.starter.csv", newline="") as f:
        return list(csv.DictReader(f))

class StarterList(unittest.TestCase):
    def test_header(self):
        with open(T / "companies.starter.csv", newline="") as f:
            self.assertEqual(next(csv.reader(f)), COLS)

    def test_alphabetical_case_insensitive(self):
        names = [r["name"] for r in rows()]
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_no_duplicates(self):
        names = [r["name"].lower() for r in rows()]
        self.assertEqual(len(names), len(set(names)))

    def test_known_ats_and_slug(self):
        for r in rows():
            self.assertIn(r["ats"], ATS, r["name"])
            if r["ats"] in {"ashby", "greenhouse", "lever"}:
                self.assertTrue(r["slug"], r["name"])

    def test_no_notes_or_dates_in_starter(self):
        for r in rows():
            self.assertEqual((r["notes"], r["last_checked"]), ("", ""), r["name"])

class Templates(unittest.TestCase):
    def test_example_config_keys_are_known(self):
        import common
        cfg = json.loads((T / "search.example.json").read_text())
        self.assertFalse(set(cfg) - set(common.DEFAULTS))

    def test_applied_template_has_header_only(self):
        self.assertEqual((T / "applied.csv").read_text().strip(), "company,title,url,date,notes")

    def test_seen_template_is_empty(self):
        self.assertEqual(json.loads((T / "seen.json").read_text()), {})

class SeenFormat(unittest.TestCase):
    CODES = {"not-research", "wrong-level", "onsite-required", "region-excluded", "commercial-role",
             "usability-led", "below-floor", "excluded-company", "already-applied", "other"}

    def test_codes_match_docs(self):
        doc = (ROOT / "docs" / "rejection-reasons.md").read_text()
        for c in self.CODES:
            self.assertIn(f"`{c}`", doc)

if __name__ == "__main__":
    unittest.main()
