#!/usr/bin/env python3
"""Find which job board system a company uses, and the board name to put in companies.csv.

  python3 find_board.py https://example.com/careers      # a careers page address (best)
  python3 find_board.py "Example Co"                     # a company name (guesses board names)

For an address it reads the page, then (if needed) the page's own script files and a few linked careers
pages, looking for Greenhouse, Ashby, Lever, SmartRecruiters, Workable and Teamtailor. Every candidate is
checked against the board's public list and shown with its first job titles, so you can see whether it
really is that company's board. Read-only; a short pause between requests."""
import re, sys
from urllib.parse import urljoin, urlparse, unquote
import common, scan

# (system, regex with one capture group for the board name)
PATTERNS = [
    ("ashby", r"jobs\.ashbyhq\.com/([A-Za-z0-9%._-]+)"),
    ("ashby", r"api\.ashbyhq\.com/posting-api/job-board/([A-Za-z0-9%._-]+)"),
    ("ashby", r"ashbyhq\.com/[\"']?\)?\.concat\(encodeURIComponent\([\"']([^\"']+)[\"']\)"),   # board name in a script
    ("greenhouse", r"job_board\?for=([A-Za-z0-9_-]+)"),
    ("greenhouse", r"(?:boards|job-boards)(?:-api)?\.greenhouse\.io/(?:v1/boards/)?(?!embed)([A-Za-z0-9_-]+)"),
    ("lever", r"jobs\.lever\.co/([A-Za-z0-9_-]+)"),
    ("lever", r"api\.lever\.co/v0/postings/([A-Za-z0-9_-]+)"),
    ("smartrecruiters", r"(?:careers|jobs)\.smartrecruiters\.com/([A-Za-z0-9_-]+)"),
    ("smartrecruiters", r"api\.smartrecruiters\.com/v1/companies/([A-Za-z0-9_-]+)"),
    ("workable", r"apply\.workable\.com/(?:api/v1/widget/accounts/)?([A-Za-z0-9_-]+)"),
    ("teamtailor", r"([A-Za-z0-9-]+\.teamtailor\.com)"),
]
NOT_BOARDS = {"embed", "v1", "api", "boards", "static", "assets", "jobs", "j"}

def detect(text):
    """Pure: every (system, board name) found in a page or script, without duplicates."""
    found = []
    for ats, rx in PATTERNS:
        for m in re.finditer(rx, text):
            slug = unquote(m.group(1)).strip().strip(".")
            if slug and slug.lower() not in NOT_BOARDS and (ats, slug) not in found:
                found.append((ats, slug))
    return found

def _stem(host):
    parts = host.lower().split(".")
    return parts[-2] if len(parts) >= 2 else parts[0]

def script_urls(html, base, limit=40):
    """The page's own script files: same host, or a host that carries the site's name (for example a static host).
    Third-party analytics and consent scripts are left alone."""
    host = urlparse(base).netloc
    stem = _stem(host)
    out = []
    for s in re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", html):
        u = urljoin(base, s)
        h = urlparse(u).netloc
        if (h == host or stem in h.lower()) and u not in out:
            out.append(u)
    return out[:limit]

def career_links(html, base, limit=4):
    host = urlparse(base).netloc
    out = []
    for h in re.findall(r"href=[\"']([^\"'#]+)[\"']", html):
        u = urljoin(base, h).split("?")[0]
        if urlparse(u).netloc == host and re.search(r"career|jobs|openings", u, re.I) and u != base.split("?")[0] and u not in out:
            out.append(u)
    return out[:limit]

def name_guesses(name):
    base = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    cands = {base.replace(" ", ""), base.replace(" ", "-"), base.replace(" ", "_")}
    return sorted(c for c in cands if c)

def check(ats, slug, cfg):
    """Returns (job count, first three titles) or None if the board does not answer."""
    try:
        jobs = scan.fetch_jobs(ats, slug, cfg)
    except Exception:
        return None
    return len(jobs), [j["title"] for j in jobs[:3] if j.get("title")]

def working(results):
    return any(r and r[0] for r in results.values())

def find_for_address(url, cfg):
    """Look at the page, then its own scripts, then a few linked careers pages, stopping once a board answers.
    Returns {(system, board name): check result}."""
    results = {}
    def consider(cands):
        for c in cands:
            if c not in results:
                results[c] = check(c[0], c[1], cfg)
    def look(page_url):
        html = common.get(page_url, cfg)
        consider(detect(html))
        if working(results):
            return html
        for s in script_urls(html, page_url):          # the board name may live in the page's own scripts
            try:
                body = common.get(s, cfg)
            except Exception:
                continue
            if re.search(r"ashby|greenhouse|lever|smartrecruiters|workable|teamtailor", body, re.I):
                consider(detect(body))
                if working(results):
                    break
        return html
    consider(detect(url))
    html = look(url)
    if not working(results):
        for link in career_links(html, url):
            try:
                look(link)
            except Exception:
                continue
            if working(results):
                break
    return results

def main(argv):
    if not argv:
        print(__doc__); return 2
    cfg = common.load_config()
    for target in argv:
        print(f"\n== {target}")
        results = []
        if re.match(r"https?://", target):
            results = [(a, sl, r) for (a, sl), r in find_for_address(target, cfg).items()]
        else:
            for slug in name_guesses(target):
                for ats in ("greenhouse", "ashby", "lever", "workable"):
                    r = check(ats, slug, cfg)
                    if r and r[0]:
                        results.append((ats, slug, r))
        good = [r for r in results if r[2] and r[2][0]]
        for ats, slug, r in results:
            status = f"{r[0]} jobs, for example: {'; '.join(r[1])}" if r else "no answer"
            print(f"  {ats:16} {slug:28} {status}")
        if good:
            ats, slug, _ = good[0]
            print(f"  -> companies.csv row: <Name>,<sector>,,{ats},{slug},,")
            print("     Check that the job titles belong to this company: a board name can belong to another one.")
        else:
            print("  Nothing usable found. Find the company's careers page address and run this again with it;"
                  " otherwise add it as ats=browser with that address in the slug column.")
    return 0

if __name__ == "__main__":
    sys.exit(common.run_main(lambda: main(sys.argv[1:])))
