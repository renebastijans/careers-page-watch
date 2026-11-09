import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common, scan

CSV = "name,sector,size,ats,slug,last_checked,notes\nAcme,x,,special,acme,,\nBeta,x,,skip,,,\n"
MOD = '''
def fetch(name, slug, cfg):
    return [{"title": "Senior Researcher", "location": "Remote", "remote": True,
             "url": "https://example.com/" + slug, "posted": None,
             "description": "This role is fully remote and open to people based in Spain."}]
BOARDS = {"special": fetch}
'''

class CustomBoards(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.d = Path(self.t.name)
        (self.d / "companies.csv").write_text(CSV)
        (self.d / "search.json").write_text(json.dumps({"title_regex": "research"}))
    def tearDown(self): self.t.cleanup()

    def test_absent_file_gives_nothing(self):
        self.assertEqual(scan.load_custom_boards(self.d), {})

    def test_loads_boards(self):
        (self.d / "custom_boards.py").write_text(MOD)
        self.assertEqual(list(scan.load_custom_boards(self.d)), ["special"])

    def test_cannot_replace_built_in(self):
        (self.d / "custom_boards.py").write_text("BOARDS = {'lever': lambda n, s, c: []}")
        with self.assertRaises(common.ConfigError):
            scan.load_custom_boards(self.d)

    def test_bad_shape_is_plain_error(self):
        (self.d / "custom_boards.py").write_text("BOARDS = [1]")
        with self.assertRaises(common.ConfigError):
            scan.load_custom_boards(self.d)

    def test_scan_uses_handler_and_logs_it(self):
        (self.d / "custom_boards.py").write_text(MOD)
        with mock.patch.dict(os.environ, {"CPW_DATA": str(self.d)}):
            scan.main()
        c = json.loads((self.d / "candidates.json").read_text())
        self.assertEqual(len(c), 1); self.assertEqual(c[0]["company"], "Acme")
        self.assertIn("fully remote", " ".join(c[0]["policy_lines"]))
        self.assertIn("Acme: 1 roles, 1 title hits (custom)", (self.d / "scan-log.txt").read_text())

    def test_without_file_row_is_unsupported(self):
        with mock.patch.dict(os.environ, {"CPW_DATA": str(self.d)}):
            scan.main()
        self.assertIn("Acme: SKIPPED (ats=special is not supported)", (self.d / "scan-log.txt").read_text())

    def test_handler_failure_is_logged_not_fatal(self):
        (self.d / "custom_boards.py").write_text("def f(n, s, c): raise RuntimeError('boom')\nBOARDS = {'special': f}")
        with mock.patch.dict(os.environ, {"CPW_DATA": str(self.d)}):
            scan.main()
        self.assertIn("Acme: FAILED (RuntimeError: boom)", (self.d / "scan-log.txt").read_text())

if __name__ == "__main__":
    unittest.main()
