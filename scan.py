#!/usr/bin/env python3
"""Read-only scan of public job-board APIs (Greenhouse, Ashby, Lever).
Reads data/companies.csv and data/search.json; writes candidates.json (title hits),
scan-state.json (every URL seen per board, for closed-ad detection) and scan-log.txt.
One scan a day is the intended use; requests are sequential and spaced out."""
import csv, importlib.util, json, re, sys
import xml.etree.ElementTree as ET
from urllib.parse import quote, unquote
import common, enrich

COLS = ["name", "sector", "size", "ats", "slug", "last_checked", "notes"]
SCANNED = {"ashby", "greenhouse", "lever"}      # documented APIs, covered by the live smoke test
EXPERIMENTAL = {"workable", "smartrecruiters", "teamtailor"}                      # opt-in: active only when a company row says so
NOT_SCANNED = {"skip", "unknown"}

def parse_ashby(d):
    return [{"title": j.get("title"), "location": j.get("location"), "remote": bool(j.get("isRemote")),
             "url": j.get("jobUrl"), "posted": j.get("publishedAt")} for j in d.get("jobs", [])]

def parse_greenhouse(d):
    return [{"title": j.get("title"), "location": (j.get("location") or {}).get("name"), "remote": None,
             "url": j.get("absolute_url"), "posted": j.get("updated_at")} for j in d.get("jobs", [])]

def parse_lever(d):
    if not isinstance(d, list):
        raise ValueError("unexpected Lever response (unknown slug?)")
    return [{"title": j.get("text"), "location": (j.get("categories") or {}).get("location"),
             "remote": j.get("workplaceType") == "remote", "url": j.get("hostedUrl"),
             "posted": j.get("createdAt")} for j in d]

def parse_workable(d):
    """Workable's public account endpoint. `country` is a single board field, not a policy: keep the
    locations list and the description so the ad's own text can decide. `workplace_type` is documented
    but absent from live responses, so only `telecommuting` is used."""
    jobs = []
    for j in d.get("jobs", []):
        places = [", ".join(x for x in (l.get("city"), l.get("country")) if x) for l in j.get("locations") or []]
        jobs.append({"title": j.get("title"), "location": "; ".join(p for p in places if p) or j.get("country"),
                     "remote": j.get("telecommuting"), "url": j.get("url") or j.get("shortlink"),
                     "posted": j.get("published_on"), "description": j.get("description")})
    return jobs

def parse_smartrecruiters(d):
    """SmartRecruiters public postings list. The ad text needs a second request (see enrich.py)."""
    jobs = []
    for j in d.get("content", []):
        loc = j.get("location") or {}
        co = (j.get("company") or {}).get("identifier", "")
        place = loc.get("fullLocation") or ", ".join(x for x in (loc.get("city"), loc.get("country")) if x)
        jobs.append({"title": j.get("name"), "location": place or None, "remote": bool(loc.get("remote")),
                     "url": f"https://jobs.smartrecruiters.com/{co}/{j['id']}" if co and j.get("id") else None,
                     "posted": j.get("releasedDate")})
    return jobs

def parse_teamtailor(xml_text):
    """Teamtailor's public jobs RSS feed. The ad text comes with the list."""
    if re.search(r"<!(DOCTYPE|ENTITY)", xml_text, re.I):
        raise ValueError("unexpected XML declaration in the feed")
    root = ET.fromstring(xml_text)
    jobs = []
    for it in root.iter("item"):
        def text(tag):
            e = it.find(tag)
            return (e.text or "").strip() if e is not None else ""
        places = []
        for el in it.iter():
            if el.tag.endswith("}location"):
                parts = [(c.text or "").strip() for c in el if c.tag.split("}")[-1] in ("city", "country") and (c.text or "").strip()]
                if parts:
                    places.append(", ".join(parts))
        jobs.append({"title": text("title"), "location": "; ".join(places) or None,
                     "remote": text("remoteStatus") == "fully", "url": text("link"),
                     "posted": text("pubDate"), "description": text("description")})
    return jobs

PARSERS = {"ashby": parse_ashby, "greenhouse": parse_greenhouse, "lever": parse_lever, "workable": parse_workable}

def board_url(ats, slug):
    if ats == "teamtailor":                 # slug = the careers site address, for example careers.example.com
        slug = re.sub(r"^https?://", "", slug.strip()).split("/")[0]
    slug = quote(unquote(slug), safe="")     # a board name may contain spaces
    return {"ashby": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
            "greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
            "lever": f"https://api.lever.co/v0/postings/{slug}?mode=json",
            # documented path; it redirects to apply.workable.com/api/v1/widget/accounts/{slug}
            "workable": f"https://www.workable.com/api/accounts/{slug}?details=true",
            "smartrecruiters": f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100",
            "teamtailor": f"https://{slug}/jobs.rss"}[ats]

def fetch_jobs(ats, slug, cfg):
    if ats == "smartrecruiters":
        jobs, offset = [], 0
        while True:
            d = json.loads(common.get(board_url(ats, slug) + f"&offset={offset}", cfg))
            page = d.get("content", [])
            jobs += parse_smartrecruiters(d)
            offset += len(page)
            if not page or offset >= d.get("totalFound", 0) or offset >= 1000:
                return jobs
    if ats == "teamtailor":
        return parse_teamtailor(common.get(board_url(ats, slug), cfg))
    return PARSERS[ats](json.loads(common.get(board_url(ats, slug), cfg)))

def load_custom_boards(data):
    """Optional user code: data/custom_boards.py with BOARDS = {"<ats value>": fetch(name, slug, cfg) -> [job dicts]}.
    Job dicts have the same keys as the built-in parsers (title, location, remote, url, posted; optional description).
    Built-in boards cannot be replaced. Returns {} when the file is absent."""
    f = data / "custom_boards.py"
    if not f.exists():
        return {}
    spec = importlib.util.spec_from_file_location("custom_boards", f)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    boards = getattr(mod, "BOARDS", None)
    if not isinstance(boards, dict) or not all(callable(v) for v in boards.values()):
        raise common.ConfigError("custom_boards.py must define BOARDS = {'<ats value>': function(name, slug, cfg)}")
    clash = set(boards) & (SCANNED | EXPERIMENTAL | NOT_SCANNED | {"browser"})
    if clash:
        raise common.ConfigError(f"custom_boards.py cannot replace built-in board types: {', '.join(sorted(clash))}")
    return boards

def title_hits(jobs, title_re):
    rx = re.compile(title_re, re.I)
    return [j for j in jobs if j.get("title") and j.get("url") and rx.search(j["title"])]

def read_companies(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    data = common.data_dir(); cfg = common.load_config()
    rows = read_companies(data / "companies.csv")
    custom = load_custom_boards(data)
    cands, state, log = [], {}, []
    for r in rows:
        name, ats, slug = r["name"], r["ats"], r["slug"]
        if ats == "browser":     # the careers page address lives in the slug column
            log.append(f"{name}: CHECK BY HAND ({slug or 'no address saved'})"); continue
        if ats in NOT_SCANNED:
            log.append(f"{name}: SKIPPED (ats={ats})"); continue
        if ats not in SCANNED | EXPERIMENTAL | set(custom):
            log.append(f"{name}: SKIPPED (ats={ats} is not supported)"); continue
        try:
            jobs = custom[ats](name, slug, cfg) if ats in custom else fetch_jobs(ats, slug, cfg)
        except Exception as e:
            log.append(f"{name}: FAILED ({type(e).__name__}: {e})"); continue
        hits = title_hits(jobs, cfg["title_regex"])
        state[name] = [j["url"] for j in jobs if j.get("url")]
        cands += [dict(j, company=name, sector=r["sector"], ats=ats, slug=slug) for j in hits]
        log.append(f"{name}: {len(jobs)} roles, {len(hits)} title hits" + (" (experimental)" if ats in EXPERIMENTAL else " (custom)" if ats in custom else "")
                   + (" (0 roles: check the company identifier, a wrong one also returns 0)" if ats == "smartrecruiters" and not jobs else ""))
    (data / "candidates.json").write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    (data / "scan-state.json").write_text(json.dumps(state), encoding="utf-8")
    (data / "scan-log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"scan done: {len(cands)} candidates; see {data / 'scan-log.txt'}")
    enrich.run(data, cfg)

if __name__ == "__main__":
    sys.exit(common.run_main(main))
