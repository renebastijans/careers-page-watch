import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common, scan, report

FX = Path(__file__).parent / "fixtures"
def load(n): return json.loads((FX / n).read_text())
CFG = dict(common.DEFAULTS, eligible_places=["Spain", "Madrid"], max_office_days=2)

class Parsers(unittest.TestCase):
    def test_ashby(self):
        jobs = scan.parse_ashby(load("ashby.json"))
        self.assertEqual(len(jobs), 3)
        self.assertTrue(jobs[1]["remote"])

    def test_greenhouse(self):
        self.assertEqual(scan.parse_greenhouse(load("greenhouse.json"))[0]["location"], "Remote - EMEA")

    def test_lever(self):
        jobs = scan.parse_lever(load("lever.json"))
        self.assertTrue(jobs[0]["remote"]); self.assertFalse(jobs[1]["remote"])

    def test_workable_keeps_description_and_all_locations(self):
        jobs = scan.parse_workable(load("workable.json"))
        self.assertEqual(jobs[0]["location"], "France")
        self.assertTrue(jobs[0]["remote"]); self.assertFalse(jobs[1]["remote"])
        self.assertEqual(jobs[1]["location"], "New York, United States")
        self.assertIn("remote options", jobs[0]["description"])

    def test_board_name_with_spaces_is_quoted(self):
        self.assertTrue(scan.board_url("ashby", "Superhuman Platform Inc").endswith("/Superhuman%20Platform%20Inc"))
        self.assertTrue(scan.board_url("ashby", "Superhuman%20Platform%20Inc").endswith("/Superhuman%20Platform%20Inc"))
        self.assertTrue(scan.board_url("greenhouse", "gitlab").endswith("/boards/gitlab/jobs"))

    def test_smartrecruiters(self):
        jobs = scan.parse_smartrecruiters(load("smartrecruiters.json"))
        self.assertEqual(jobs[0]["url"], "https://jobs.smartrecruiters.com/examplecorp/111000000000001")
        self.assertEqual(jobs[0]["location"], "Madrid, Spain")
        self.assertTrue(jobs[1]["remote"])

    def test_smartrecruiters_text_includes_the_office_line(self):
        import enrich
        t = enrich.sr_text(load("smartrecruiters_detail.json"))
        self.assertIn("Up to 2 days a week in the office.", t)
        self.assertIn("anywhere in the EU", t)

    def test_smartrecruiters_url_and_paging_params(self):
        u = scan.board_url("smartrecruiters", "lastminutecom")
        self.assertEqual(u, "https://api.smartrecruiters.com/v1/companies/lastminutecom/postings?limit=100")

    def test_teamtailor(self):
        jobs = scan.parse_teamtailor((FX / "teamtailor.xml").read_text(encoding="utf-8"))
        self.assertEqual([j["title"] for j in jobs], ["Senior Researcher", "Office Manager"])
        self.assertEqual(jobs[0]["location"], "Madrid, Spain")
        self.assertTrue(jobs[0]["remote"]); self.assertFalse(jobs[1]["remote"])
        self.assertIn("Fully remote within the EU", jobs[0]["description"])
        self.assertIsNone(jobs[1]["location"])

    def test_teamtailor_rejects_xml_entities(self):
        with self.assertRaises(ValueError):
            scan.parse_teamtailor('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><rss><channel/></rss>')

    def test_teamtailor_address_is_normalised(self):
        for slug in ("careers.example.com", "https://careers.example.com/jobs", "https://careers.example.com/"):
            self.assertEqual(scan.board_url("teamtailor", slug), "https://careers.example.com/jobs.rss")

    def test_new_systems_are_experimental(self):
        self.assertTrue({"smartrecruiters", "teamtailor"} <= scan.EXPERIMENTAL)
        self.assertFalse({"smartrecruiters", "teamtailor"} & scan.SCANNED)

    def test_workable_is_experimental_not_default(self):
        self.assertIn("workable", scan.EXPERIMENTAL)
        self.assertNotIn("workable", scan.SCANNED)

    def test_lever_error_object_raises(self):
        with self.assertRaises(ValueError):
            scan.parse_lever({"ok": False, "error": "Document not found"})

    def test_title_hits(self):
        hits = scan.title_hits(scan.parse_ashby(load("ashby.json")), CFG["title_regex"])
        self.assertEqual([h["title"] for h in hits], ["Senior Researcher", "Security Researcher"])

class Classify(unittest.TestCase):
    def c(self, lines, title="Senior Researcher"):
        return {"title": title, "policy_lines": lines}

    def test_eligible_with_quote(self):
        v, code, q = report.classify(self.c(["Open to candidates in Spain, remote."]), CFG)
        self.assertEqual((v, code), ("eligible", None)); self.assertIn("Spain", q)

    def test_readme_example(self):
        cfg = dict(CFG, eligible_places=["Germany"])
        v, _, q = report.classify(self.c(["Open to candidates anywhere in the EU."]), cfg)
        self.assertEqual((v, q), ("eligible", "Open to candidates anywhere in the EU."))
        self.assertEqual(report.classify(self.c(["We are an office-first company."], "Lead Researcher"), cfg)[:2],
                         ("drop", "onsite-required"))

    def test_synonym_counts(self):
        self.assertEqual(report.classify(self.c(["Remote anywhere in Europe."]), CFG)[0], "eligible")

    def test_office_first_without_eligibility_is_dropped(self):
        v, code, q = report.classify(self.c(["We are an office-first company."]), CFG)
        self.assertEqual((v, code), ("drop", "onsite-required")); self.assertIn("office-first", q)

    def test_conflicting_signals_are_verify(self):
        lines = ["We are an office-first company.", "Open to candidates in Europe."]
        self.assertEqual(report.classify(self.c(lines), CFG)[0], "verify")

    def test_office_days_over_limit(self):
        v, code, _ = report.classify(self.c(["Hybrid: 3 days a week in our Berlin office."]), CFG)
        self.assertEqual((v, code), ("drop", "onsite-required"))

    def test_office_days_within_limit_not_dropped(self):
        self.assertNotEqual(report.classify(self.c(["Hybrid: 2 days a week in the office."]), CFG)[0], "drop")

    def test_office_days_unchecked_when_null(self):
        cfg = dict(CFG, max_office_days=None)
        self.assertNotEqual(report.classify(self.c(["Hybrid: 4 days a week in the office."]), cfg)[0], "drop")

    def test_no_text_is_verify(self):
        self.assertEqual(report.classify(self.c([]), CFG)[0], "verify")

    def test_title_exclusion(self):
        self.assertEqual(report.classify(self.c(["Remote."], "Security Researcher"), CFG)[:2], ("drop", "not-research"))

    def test_silent_ad_is_verify_not_dropped(self):
        self.assertEqual(report.classify(self.c(["Remote role, travel up to 10% a year."]), CFG)[0], "verify")

def cand(url, title="Senior Researcher", company="Acme", lines=("Open to candidates in Spain, remote.",), h="h1"):
    return {"url": url, "title": title, "company": company, "sector": "x", "policy_lines": list(lines), "policy_hash": h}

class Build(unittest.TestCase):
    def test_new_changed_closed_dropped(self):
        seen = {"https://a/1": {"status": "reported", "company": "Acme", "title": "Old", "policy_hash": "old"},
                "https://a/gone": {"status": "reported", "company": "Acme", "title": "Gone"},
                "https://a/d": {"status": "dropped", "code": "wrong-level", "reason": "r", "company": "Acme", "title": "Lead Researcher"}}
        cands = [cand("https://a/1", "Old", h="new"), cand("https://a/2"),
                 cand("https://a/3", lines=("We are an office-first company.",)),
                 cand("https://a/4", "Lead Researcher")]
        state = {"Acme": ["https://a/1", "https://a/2", "https://a/3", "https://a/4"]}
        new, changed, dropped, closed = report.build(cands, seen, state, CFG, "2026-01-05")
        self.assertEqual([c["url"] for c in new], ["https://a/2"])
        self.assertEqual([c["url"] for c, _ in changed][:1], ["https://a/1"])
        self.assertIn("repost of an ad dropped for wrong-level", changed[1][1])
        self.assertEqual([c["url"] for c in dropped], ["https://a/3"])
        self.assertEqual([u for u, _ in closed], ["https://a/gone"])

    def test_failed_board_never_closes_ads(self):
        seen = {"https://a/gone": {"status": "reported", "company": "Acme", "title": "Gone"}}
        self.assertEqual(report.build([], seen, {}, CFG, "d")[3], [])

    def test_quiet_day_is_one_line_plus_footer(self):
        text = report.render([], [], [], [], ["Acme: 3 roles, 0 title hits"], "2026-01-05")
        self.assertIn("No new matches today", text)
        self.assertNotIn("## New", text)

    def test_all_boards_failed_is_not_a_quiet_day(self):
        text = report.render([], [], [], [], ["A: FAILED (x)", "B: FAILED (y)", "C: SKIPPED (ats=skip)"], "d")
        self.assertIn("Scan failed for all 2 boards", text)
        self.assertNotIn("No new matches", text)

    def test_placeholder_places_trigger_a_notice(self):
        self.assertTrue(report.settings_notices(dict(common.DEFAULTS)))
        self.assertTrue(report.settings_notices(dict(common.DEFAULTS, eligible_places=["YourCountry", "YourCity"])))
        self.assertEqual(report.settings_notices(dict(common.DEFAULTS, eligible_places=["Germany"])), [])

    def test_notice_and_legend_and_board_column_are_rendered(self):
        a = cand("https://a/2"); a.update(_v="verify", _code=None, _quote="q", location="Remote - US")
        text = report.render([a], [], [], [], [], "d", report.settings_notices(dict(common.DEFAULTS)))
        self.assertIn("no real places yet", text)
        self.assertIn("| Remote - US |", text)
        self.assertIn("How to read this", text)
        quiet = report.render([], [], [], [], [], "d", report.settings_notices(dict(common.DEFAULTS)))
        self.assertIn("no real places yet", quiet)

    def test_exclusion_quote_is_explained(self):
        q = report.classify({"title": "Security Researcher", "policy_lines": []}, CFG)[2]
        self.assertIn("exclude words", q)

    def test_check_by_hand_is_listed_with_its_address_not_as_a_scan(self):
        log = ["A: 3 roles, 0 title hits", "Last Minute: CHECK BY HAND (https://corporate.example.com/careers/)"]
        text = report.render([], [], [], [], log, "d")
        self.assertIn("Check by hand (not scanned automatically):", text)
        self.assertIn("- Last Minute: https://corporate.example.com/careers/", text)
        self.assertIn("Boards with problems or skipped: 0", text)

    def test_only_check_by_hand_rows_is_not_an_all_failed_scan(self):
        text = report.render([], [], [], [], ["A: CHECK BY HAND (https://x.example/)"], "d")
        self.assertNotIn("Scan failed", text)

    def test_update_seen_marks_everything(self):
        seen = {"https://a/gone": {"status": "reported", "company": "Acme", "title": "Gone"}}
        a = cand("https://a/2"); a.update(_v="eligible", _code=None, _quote="q")
        b = cand("https://a/3"); b.update(_v="drop", _code="onsite-required", _quote="office-first")
        out = report.update_seen(seen, [a], [b], [], [("https://a/gone", seen["https://a/gone"])], "2026-01-05")
        self.assertEqual(out["https://a/2"]["status"], "reported")
        self.assertEqual(out["https://a/3"]["code"], "onsite-required")
        self.assertEqual(out["https://a/gone"]["closed"], "2026-01-05")
        # a second run must not re-report any of them
        new, *_ = report.build([a, b], out, {"Acme": ["https://a/2", "https://a/3"]}, CFG, "2026-01-06")
        self.assertEqual(new, [])

class Applied(unittest.TestCase):
    ROW = {"company": "Acme", "title": "Senior Researcher", "url": "https://a/applied", "date": "2026-11-05", "notes": ""}

    def test_applied_ad_is_never_listed_as_new_or_dropped(self):
        c = cand("https://a/applied")
        new, changed, dropped, closed = report.build([c], {}, {"Acme": ["https://a/applied"]}, CFG, "d", [self.ROW])
        self.assertEqual((new, changed, dropped, closed), ([], [], [], []))

    def test_row_without_link_still_suppresses(self):
        row = dict(self.ROW, url="")
        new, *_ = report.build([cand("https://a/other")], {}, {"Acme": ["https://a/other"]}, CFG, "d", [row])
        self.assertEqual(new, [])

    def test_changed_text_mentions_the_application(self):
        seen = {"https://a/applied": {"status": "reported", "company": "Acme", "title": "Senior Researcher", "policy_hash": "old"}}
        _, changed, *_ = report.build([cand("https://a/applied", h="new")], seen, {}, CFG, "d", [self.ROW])
        self.assertIn("you applied on 2026-11-05", changed[0][1])

    def test_repost_of_applied_ad(self):
        _, changed, *_ = report.build([cand("https://a/repost")], {}, {"Acme": ["https://a/repost"]}, CFG, "d", [self.ROW])
        self.assertIn("repost of the ad you applied for on 2026-11-05", changed[0][1])

    def test_closed_since_applied_is_reported_once(self):
        state = {"Acme": ["https://a/other"]}
        _, _, _, closed = report.build([], {}, state, CFG, "d", [self.ROW])
        self.assertEqual([u for u, _ in closed], ["https://a/applied"])
        self.assertIn("you applied on 2026-11-05", report.render([], [], [], closed, [], "d"))
        seen = report.update_seen({}, [], [], [], closed, "2026-11-08", [self.ROW], [])
        self.assertEqual(seen["https://a/applied"]["closed"], "2026-11-08")
        _, _, _, again = report.build([], seen, state, CFG, "d", [self.ROW])
        self.assertEqual(again, [])

    def test_failed_board_never_closes_applied(self):
        self.assertEqual(report.build([], {}, {}, CFG, "d", [self.ROW])[3], [])

    def test_load_applied(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "applied.csv"
            self.assertEqual(report.load_applied(p), [])
            p.write_text("company,title,url,date,notes\nAcme,Senior Researcher,https://a/x,2026-11-05,\n,,,,\n")
            self.assertEqual(len(report.load_applied(p)), 1)

class ShortPlaceWords(unittest.TestCase):
    US = dict(CFG, eligible_places=["San Francisco", "SF", "USA", "US"], place_synonyms=["Americas"], max_office_days=5)

    def test_the_word_us_is_not_a_place(self):
        v = report.classify({"title": "Senior Product Marketing Manager", "policy_lines": ["This role lets us work remotely."]}, self.US)
        self.assertEqual(v[0], "verify")

    def test_us_in_capitals_is_a_place(self):
        v = report.classify({"title": "Senior Product Marketing Manager", "policy_lines": ["This is a remote opportunity within the US."]}, self.US)
        self.assertEqual(v[0], "eligible")

class BoardGroup(unittest.TestCase):
    CFG2 = dict(CFG, eligible_places=["Spain", "Madrid"])

    def test_groups(self):
        for loc, want in [("Remote, US", "likely-not"), ("Remote, Canada/US", "likely-not"), ("San Francisco", "likely-not"),
                          ("Remote", "check"), ("Remote or hybrid", "check"), ("Remote, US or Canada", "likely-not"), ("Remote - Global", "check"), ("Remote, EMEA", "check"),
                          ("Remote (Europe)", "check"), ("Madrid, Spain", "check"), ("", "check"), (None, "check")]:
            self.assertEqual(report.board_group({"location": loc}, self.CFG2), want, loc)

    def test_title_signal_keeps_it_in_check(self):
        self.assertEqual(report.board_group({"location": "Paris, France", "title_remote_signal": True}, self.CFG2), "check")

    def test_render_splits_and_never_hides(self):
        a = cand("https://a/1", "PM One"); a.update(_v="verify", _code=None, _quote="q", location="Remote, US", _g="likely-not")
        b = cand("https://a/2", "PM Two"); b.update(_v="verify", _code=None, _quote="q", location="Remote - Global", _g="check")
        text = report.render([a, b], [], [], [], [], "d")
        self.assertIn("**1 worth a look** · 1 probably not open to you", text)
        self.assertIn("## Probably not open to you", text)
        self.assertIn("[PM One](https://a/1)", text)           # still listed, with its link
        main = text.split("## Probably not open to you")[0]
        self.assertIn("PM Two", main); self.assertNotIn("PM One", main)

class ReportPath(unittest.TestCase):
    def test_never_overwrites(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p, w = report.report_path(d, "2026-01-05", quiet=False)
            self.assertEqual((p.name, w), ("report-2026-01-05.md", True)); p.write_text("first")
            p, w = report.report_path(d, "2026-01-05", quiet=True)         # quiet rerun: leave it alone
            self.assertEqual((p.name, w), ("report-2026-01-05.md", False))
            p, w = report.report_path(d, "2026-01-05", quiet=False)        # rerun with news: new file
            self.assertEqual((p.name, w), ("report-2026-01-05-2.md", True)); p.write_text("second")
            self.assertEqual(report.report_path(d, "2026-01-05", False)[0].name, "report-2026-01-05-3.md")
            self.assertEqual((d / "report-2026-01-05.md").read_text(), "first")

class Config(unittest.TestCase):
    def test_unknown_key_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "search.json").write_text('{"nope": 1}')
            with self.assertRaises(ValueError):
                common.load_config(d)

    def write(self, text):
        import tempfile
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        (Path(d.name) / "search.json").write_text(text, encoding="utf-8")
        return d.name

    def test_typo_gives_line_and_plain_advice(self):
        with self.assertRaises(common.ConfigError) as cm:
            common.load_config(self.write('{\n  "max_office_days": 2\n  "pay_floor": null\n}'))
        msg = str(cm.exception)
        self.assertIn("line 3", msg); self.assertIn("missing comma", msg); self.assertIn("init_data.py", msg)

    def test_curly_quotes_are_explained(self):
        with self.assertRaises(common.ConfigError) as cm:
            common.load_config(self.write('{\u201celigible_places\u201d: []}'))
        self.assertIn("curly quotes", str(cm.exception))

    def test_wrong_types_are_named(self):
        for text, key in [('{"eligible_places": "Germany"}', "eligible_places"),
                          ('{"max_office_days": "two"}', "max_office_days"),
                          ('{"max_office_days": -1}', "max_office_days"),
                          ('{"title_regex": "research("}', "title_regex"),
                          ('{"request_delay_seconds": "fast"}', "request_delay_seconds"),
                          ('{"report_email_to": "nobody"}', "report_email_to")]:
            with self.assertRaises(common.ConfigError, msg=text) as cm:
                common.load_config(self.write(text))
            self.assertIn(f'"{key}"', str(cm.exception))

    def test_quiet_email_flag_must_be_boolean(self):
        with self.assertRaises(common.ConfigError):
            common.load_config(self.write('{"email_when_quiet": "yes"}'))
        self.assertTrue(common.load_config(self.write('{}'))["email_when_quiet"])
        self.assertFalse(common.load_config(self.write('{"email_when_quiet": false}'))["email_when_quiet"])

    def test_not_an_object(self):
        with self.assertRaises(common.ConfigError):
            common.load_config(self.write("[1, 2]"))

    def test_example_config_is_valid(self):
        common.load_config(Path(__file__).resolve().parents[1] / "templates")  # no search.json there: defaults ok
        d = Path(__file__).resolve().parents[1] / "templates" / "search.example.json"
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as t:
            shutil.copy(d, Path(t) / "search.json"); common.load_config(t)

    def test_run_main_prints_no_traceback(self):
        import io, contextlib
        def boom(): raise common.ConfigError("Your settings file x has a problem")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(common.run_main(boom), 1)
        self.assertIn("Problem: Your settings file", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_missing_file_gives_defaults(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(common.load_config(d), common.DEFAULTS)

if __name__ == "__main__":
    unittest.main()
