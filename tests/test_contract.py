"""Regression guard for the instructions the Claude layer follows (and for the claims the docs make).

These tests cannot check what a model does at run time. They stop the instructions themselves from
drifting: a question reworded, a rule dropped, a step renamed. Changing a question on purpose means
updating tests/interview_contract.json in the same commit, then re-running tests/INTERVIEW-CHECKLIST.md."""
import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(p): return (ROOT / p).read_text(encoding="utf-8")

QUESTION = re.compile(r'^(\d+b?)\. \*\*(.+?)\.\*\* [^"\n]*?"(.+?)"', re.M)

class InterviewQuestions(unittest.TestCase):
    def setUp(self):
        self.found = {m.group(1): {"label": m.group(2), "text": m.group(3)} for m in QUESTION.finditer(read("AGENTS.md"))}
        self.gold = json.loads(read("tests/interview_contract.json"))

    def test_questions_match_the_agreed_wording(self):
        self.assertEqual(self.found, self.gold)

    def test_ten_questions_in_order_with_3b_after_3(self):
        self.assertEqual(list(self.found), ["1", "2", "3", "3b", "4", "5", "6", "7", "8", "9", "10"])

    def test_every_question_has_text_and_a_label(self):
        for k, v in self.found.items():
            self.assertTrue(v["label"].strip() and v["text"].strip(), k)

class RequiredRules(unittest.TestCase):
    NEEDLES = {
        "AGENTS.md": [
            "**Question 3 of 10: Sectors.**", "**Question 3b of 10: Exclusions.**", "Never skip the number",
            "never merge two questions", "never offer preset answer buttons",
            "do not offer suggested times as buttons", "never mention internal task names or ids",
            "; true", "Job ad report backup", "email_when_quiet", "data/applied.csv", "docs/uninstall.md",
            "exactly the names in `companies.csv`", "Never assume the starter list is included",
            "Do **not** use `./run.sh`", "report.py --dry-run", "Closing message (always)",
            "never combined with it", "find_board.py", "put its country in `eligible_places` too", "United States, US, USA, North America and Americas",
        ],
        "AGENT.md": [
            "Backup run", "applied.csv", "never `sed -i`", "exactly the subject", "full `https://` address",
            "5b.", "(check this)", "Probably not open to you", "**Board says:**", "email_when_quiet",
            "Never run `./run.sh` or `report.py` without `--dry-run`", "find_board.py", "Strong needs the ad's own words", "board and ad agree", "do not write your own shell loops",
        ],
        "README.md": [
            "Download ZIP", "careers-page-watch-main", "**Code** tab", "This computer", "Choose folder", '"set me up"', "docs/uninstall.md",
            "Python 3", "data/applied.csv", "Probably not open to you", "SECURITY.md", "It reads English-language ads", "not affiliated with or endorsed by", "tested on macOS",
        ],
        "docs/scheduling.md": ["BACKUP run", "already exists in data/reports", "email only the address in search.json", "Auto mode"],
        "docs/uninstall.md": ["three dots", "Delete", "backup task", "Scheduled", "~/.claude/scheduled-tasks", "Leave any folder you do not recognise"],
        "docs/mac-guide.md": ["Type this in the **Terminal window** you opened in step 2", "not something to type in Terminal", "Type this in the **Terminal window** from step 4", "Type this in the **Terminal window** (the same one", "python3 find_board.py", "This is typed in the **Terminal window**", "Make Rich Text", "Smart Quotes", "careers-page-watch-main", "Choose folder", "set me up", "python.org", "Install Certificates.command", "Open Anyway", "applied.csv"],
        "SECURITY.md": ["Report a vulnerability", "Security contact", "Auto mode", "untrusted"],
    }

    def test_each_file_keeps_its_key_rules(self):
        for path, needles in self.NEEDLES.items():
            text = read(path)
            for n in needles:
                self.assertIn(n, text, f"{path} lost: {n!r}")

class DocsAgreeWithTheCode(unittest.TestCase):
    def test_every_experimental_board_is_documented(self):
        import scan
        readme = read("README.md")
        for ats in scan.EXPERIMENTAL:
            self.assertIn(f"`ats` = `{ats}`", readme, ats)

    def test_every_supported_board_is_documented(self):
        import scan
        readme = read("README.md")
        for ats in scan.SCANNED:
            self.assertIn(ats, readme.lower(), ats)

    def test_every_setting_is_in_the_readme_table_or_example(self):
        import common
        example = json.loads(read("templates/search.example.json"))
        for key in common.DEFAULTS:
            if key in ("user_agent", "pay_floor", "pay_currency"):
                continue
            self.assertIn(key, example, key)

    def test_no_limits_file_remains(self):
        self.assertFalse((ROOT / "templates" / "limits.md").exists())
        self.assertNotIn("limits.md", read("AGENT.md") + read("AGENTS.md"))

if __name__ == "__main__":
    unittest.main()
