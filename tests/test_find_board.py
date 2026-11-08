import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import find_board as f

class Detect(unittest.TestCase):
    def test_script_with_a_built_board_name(self):
        js = 'let h="https://jobs.ashbyhq.com/".concat(encodeURIComponent("Example Platform Inc"),"/embed?version=2");'
        self.assertEqual(f.detect(js), [("ashby", "Example Platform Inc")])

    def test_plain_links(self):
        html = ('<a href="https://jobs.ashbyhq.com/exampleco/abc">a</a> <a href="https://boards.greenhouse.io/examplegh/jobs/1">b</a>'
                ' <a href="https://jobs.lever.co/examplelv/xyz">c</a> <a href="https://careers.smartrecruiters.com/ExampleSR">d</a>'
                ' <a href="https://apply.workable.com/examplewk/">e</a> <a href="https://acme.teamtailor.com/jobs">f</a>')
        self.assertEqual(f.detect(html), [("ashby", "exampleco"), ("greenhouse", "examplegh"), ("lever", "examplelv"),
                                          ("smartrecruiters", "ExampleSR"), ("workable", "examplewk"), ("teamtailor", "acme.teamtailor.com")])

    def test_greenhouse_embed_and_api_forms(self):
        self.assertEqual(f.detect("https://boards.greenhouse.io/embed/job_board?for=embedco"), [("greenhouse", "embedco")])
        self.assertEqual(f.detect("https://boards-api.greenhouse.io/v1/boards/apico/jobs"), [("greenhouse", "apico")])

    def test_nothing_found(self):
        self.assertEqual(f.detect("<html><p>No jobs board here</p></html>"), [])

    def test_no_duplicates(self):
        self.assertEqual(len(f.detect("jobs.lever.co/x jobs.lever.co/x jobs.lever.co/x")), 1)

class Pages(unittest.TestCase):
    HTML = ('<script src="https://thirdparty-analytics.com/a.js"></script>'
            '<script src="/static/app.js"></script>'
            '<script src="https://examplestatic.com/chunks/1.js"></script>'
            '<a href="/company/careers/jobs?x=1">Jobs</a><a href="/about">About</a><a href="https://other.com/careers">Other</a>')

    def test_own_scripts_only(self):
        urls = f.script_urls(self.HTML, "https://example.com/careers")
        self.assertEqual(urls, ["https://example.com/static/app.js", "https://examplestatic.com/chunks/1.js"])

    def test_script_limit(self):
        many = "".join(f'<script src="/s{i}.js"></script>' for i in range(60))
        self.assertEqual(len(f.script_urls(many, "https://example.com/")), 40)

    def test_career_links_stay_on_the_site(self):
        self.assertEqual(f.career_links(self.HTML, "https://example.com/careers"), ["https://example.com/company/careers/jobs"])

class Names(unittest.TestCase):
    def test_guesses(self):
        self.assertEqual(f.name_guesses("Great Question"), ["great-question", "great_question", "greatquestion"])
        self.assertEqual(f.name_guesses("GitLab"), ["gitlab"])
        self.assertEqual(f.name_guesses("1Password!"), ["1password"])

if __name__ == "__main__":
    unittest.main()
