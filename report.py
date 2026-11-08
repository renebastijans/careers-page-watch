#!/usr/bin/env python3
"""Standalone report (no AI). Reads enriched candidates.json, applies the config's location rules to
each ad's own text, compares with seen.json and writes reports/report-YYYY-MM-DD.md.

Design rule: it only drops an ad on location when the ad explicitly says so and nothing in the ad
suggests you are eligible. Everything else is kept and marked [verify]. Pay is not read here."""
import argparse, csv, datetime, json, re, sys
import common, enrich
from seen_match import find_seen, squash

NEGATIVE = re.compile(
    r"office-first|on-?site (only|role|position|based)|no remote|not (offer|support|available|possible).{0,30}remote|"
    r"remote.{0,20}not (available|possible|an option|offered)|must (be )?(based|located|work) (in|from) (the |our )?office|"
    r"in-person (only|required)|(required|expected) to (be|work) (in|from) (the |our )?office", re.I)
OFFICE_DAYS = re.compile(r"(\d)\s*(?:-|to)?\s*(?:\d\s*)?days?\s*(?:a|per|each|/)\s*week", re.I)
OFFICE_CONTEXT = re.compile(r"office|on-?site|hub|in-person|in person", re.I)
ELIGIBLE_CONTEXT = re.compile(r"remote|hybrid|open to|eligible|based in|located|countries|work from|anywhere|relocat", re.I)

def place_regex(cfg):
    w = enrich.place_words(cfg)
    return re.compile(r"\b(" + "|".join(enrich.place_pattern(x) for x in w) + r")\b", re.I) if w else None

def classify(c, cfg):
    """Returns (verdict, code, quote): verdict 'eligible' | 'verify' | 'drop'."""
    if re.search(cfg["title_exclude_regex"], c.get("title") or "", re.I):
        return ("drop", "not-research", f"the title matches your exclude words ({cfg['title_exclude_regex']})")
    lines = c.get("policy_lines") or []
    if not lines:
        return ("verify", None, "no readable policy text in the ad")
    pr = place_regex(cfg)
    eligible = next((l for l in lines if pr and pr.search(l) and ELIGIBLE_CONTEXT.search(l)), None)
    negative = next((l for l in lines if NEGATIVE.search(l)), None)
    over = None
    mx = cfg.get("max_office_days")
    if mx is not None:
        for l in lines:
            m = OFFICE_DAYS.search(l)
            if m and OFFICE_CONTEXT.search(l) and int(m.group(1)) > mx:
                over = l; break
    if (negative or over) and not eligible:
        return ("drop", "onsite-required", negative or over)
    if eligible and not negative and not over:
        return ("eligible", None, eligible)
    return ("verify", None, negative or over or eligible or "the ad text names none of your places")

GENERIC = re.compile(r"\b(remote|hybrid|on-?site|in-?office|anywhere|global|worldwide|flexible|wfh|office|based|home|first|only|or|and)\b", re.I)

def board_group(c, cfg):
    """'likely-not' when the board's location names only places that are not yours; else 'check'.
    A hint to keep long lists readable. It never drops anything: those ads are still listed."""
    loc = (c.get("location") or "").strip()
    if not loc or c.get("title_remote_signal"):
        return "check"
    pr = place_regex(cfg)
    if pr and pr.search(loc):
        return "check"
    leftover = re.sub(r"[^\w]+", " ", GENERIC.sub(" ", loc)).strip()
    return "likely-not" if leftover else "check"

def load_applied(path):
    """data/applied.csv (company,title,url,date,notes): roles you applied for. Optional; edited by you."""
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]

def applied_match(c, applied):
    co, ti = squash(c["company"]), squash(c["title"])
    for a in applied:
        if (a.get("url") or "").strip() == c["url"]:
            return a
        if co and ti and squash(a.get("company")) == co and squash(a.get("title")) == ti:
            return a
    return None

def with_applied(seen, applied):
    """A copy of seen.json with every applied role that has a link marked status 'applied'."""
    view = {u: dict(e) for u, e in seen.items()}
    for a in applied:
        u = (a.get("url") or "").strip()
        if u:
            e = view.setdefault(u, {})
            e.update(status="applied", applied=(a.get("date") or "").strip() or "date not given",
                     company=(a.get("company") or "").strip(), title=(a.get("title") or "").strip())
    return view

def build(cands, seen, state, cfg, today, applied=()):
    new, changed, dropped = [], [], []
    view = with_applied(seen, applied)
    for c in cands:
        verdict, code, quote = classify(c, cfg)
        c["_v"], c["_code"], c["_quote"] = verdict, code, quote
        hit = find_seen(c["url"], c["company"], c["title"], view)
        if hit and hit[0] == "same-url":
            e = hit[2]
            if e.get("status") in ("reported", "applied") and e.get("policy_hash") and e["policy_hash"] != c["policy_hash"]:
                note = "policy text changed since last report"
                changed.append((c, f"you applied on {e['applied']}; {note}" if e.get("applied") else note))
            continue
        if hit and hit[0] == "repost":
            e = hit[2]
            if e.get("status") == "dropped":
                changed.append((c, f"repost of an ad dropped for {e.get('code')}: {e.get('reason')}"))
            elif e.get("status") == "applied":
                changed.append((c, f"repost of the ad you applied for on {e['applied']}"))
            continue
        if applied_match(c, applied):      # applied row without a link: never list it as new
            continue
        c["_g"] = board_group(c, cfg)
        (dropped if verdict == "drop" else new).append(c)
    keymap = {squash(k): k for k in state}
    closed = []
    for u, e in view.items():
        if e.get("status") in ("reported", "applied") and not e.get("closed"):
            key = keymap.get(squash(e.get("company")))
            if key and u not in set(state[key]):
                closed.append((u, e))
    return new, changed, dropped, closed

def md_row(c):
    q = (c["_quote"] or "").replace("|", "/").replace("\n", " ")
    board = (c.get("location") or "not given").replace("|", "/")
    return (f"| {c['company']} | {c.get('sector') or ''} | {c['title']} | {board} | [link]({c['url']}) | "
            f"{'eligible' if c['_v']=='eligible' else '[verify location]'}: \"{q}\" | "
            f"{'medium' if c['_v']=='eligible' else 'low'} |")

PLACEHOLDER_PLACES = {"yourcountry", "yourcity"}

def settings_notices(cfg):
    places = [p for p in cfg.get("eligible_places", []) if p.lower() not in PLACEHOLDER_PLACES]
    if places:
        return []
    return ["**Your settings have no real places yet.** Every ad below will show [verify location]. "
            "Set `eligible_places` in `data/search.json` (see docs/mac-guide.md, step 6)."]

def render(new, changed, dropped, closed, log_lines, today, notices=()):
    out = [f"# Job ad report {today}", ""]
    failed = [l for l in log_lines if "FAILED" in l]
    scanned = [l for l in log_lines if "SKIPPED" not in l and "CHECK BY HAND" not in l]
    if failed and len(failed) == len(scanned):
        out.append(f"**Scan failed for all {len(failed)} boards**: no result today, not a quiet day. See the footer.")
        return "\n".join(out + _footer(log_lines)) + "\n"
    if not (new or changed or closed):
        out.append(f"No new matches today ({len(dropped)} new ads dropped on explicit title or location text).")
        out += [""] + list(notices) if notices else []
    else:
        worth = [c for c in new if c.get("_g") != "likely-not"]
        unlikely = [c for c in new if c.get("_g") == "likely-not"]
        head = f"**{len(worth)} worth a look**"
        if unlikely:
            head += f" · {len(unlikely)} probably not open to you"
        out.append(f"{head} · {len(changed)} changed · {len(closed)} closed · {len(dropped)} dropped.")
        out += [""] + list(notices) if notices else []
        if worth:
            out += ["", "## New", "", "| Company | Sector | Role | Board says (location) | Link | From the ad itself | Confidence |",
                    "|---|---|---|---|---|---|---|"] + [md_row(c) for c in worth]
            out += ["", "**How to read this.** `eligible` means the ad itself names one of your places (quoted). "
                    "`[verify location]` means it does not say: open the ad and read it before you decide. "
                    "\"Board says\" is the job board's own location field, which is often wrong. "
                    "Pay is not read by the standalone report: check each ad."]
        if unlikely:
            by = {}
            for c in unlikely:
                by.setdefault(c["company"], []).append(c)
            out += ["", "## Probably not open to you", "",
                    "The ad text is silent on where you can work, and the board names only other places. "
                    "Nothing is dropped: open an ad if you want to check.", ""]
            for co, items in by.items():
                places = sorted({(i.get("location") or "").strip() for i in items})
                titles = "; ".join(f"[{i['title']}]({i['url']})" for i in items)
                out.append(f"- **{co}** ({len(items)}; board says {' / '.join(places)}): {titles}")
        if changed:
            out += ["", "## Changed", ""] + [f"- {c['company']}, {c['title']} ([link]({c['url']})): {why}" for c, why in changed]
        if closed:
            out += ["", "## Closed since last run", ""] + [
                f"- {e.get('company')}, {e.get('title')} ({u})" + (f", you applied on {e['applied']}" if e.get("applied") else "")
                for u, e in closed]
    if dropped:
        out += ["", "## Dropped (for the record)", ""] + [
            f"- {c['company']}, {c['title']}: `{c['_code']}` \"{(c['_quote'] or '')[:160]}\"" for c in dropped]
    return "\n".join(out + _footer(log_lines)) + "\n"

def _footer(log_lines):
    problems = [l for l in log_lines if "FAILED" in l or "SKIPPED" in l]
    out = ["", "## Footer", "", f"Boards with problems or skipped: {len(problems)}"] + [f"- {l}" for l in problems]
    hand = [l for l in log_lines if "CHECK BY HAND" in l]
    if hand:
        out += ["", "Check by hand (not scanned automatically):"]
        for l in hand:
            name, _, rest = l.partition(": CHECK BY HAND (")
            out.append(f"- {name}: {rest.rstrip(')')}")
    return out

def update_seen(seen, new, dropped, changed, closed, today, applied=(), cands=()):
    if applied:
        hashes = {c["url"]: c.get("policy_hash") for c in cands}
        for u, e in with_applied(seen, applied).items():
            if e.get("status") == "applied":
                if hashes.get(u) and not e.get("policy_hash"):
                    e["policy_hash"] = hashes[u]
                seen[u] = e
    for c in new:
        seen[c["url"]] = {"status": "reported", "company": c["company"], "title": c["title"],
                          "first_seen": today, "policy_hash": c["policy_hash"]}
    for c in dropped:
        seen[c["url"]] = {"status": "dropped", "code": c["_code"], "reason": (c["_quote"] or "")[:200],
                          "company": c["company"], "title": c["title"], "first_seen": today,
                          "policy_hash": c["policy_hash"]}
    for c, _ in changed:
        if c["url"] in seen:
            seen[c["url"]]["policy_hash"] = c["policy_hash"]
    for u, _ in closed:
        seen[u]["closed"] = today
    return seen

def report_path(folder, date, quiet):
    """Never overwrite an earlier report. Returns (path, write): a quiet rerun leaves today's report alone;
    a rerun that found something new writes report-DATE-2.md, -3.md ..."""
    first = folder / f"report-{date}.md"
    if not first.exists():
        return first, True
    if quiet:
        return first, False
    n = 2
    while (folder / f"report-{date}-{n}.md").exists():
        n += 1
    return folder / f"report-{date}-{n}.md", True

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true", help="print the report, change nothing")
    a = ap.parse_args(argv)
    data = common.data_dir(); cfg = common.load_config()
    cands = json.loads((data / "candidates.json").read_text(encoding="utf-8"))
    sp = data / "seen.json"
    seen = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    state = json.loads((data / "scan-state.json").read_text(encoding="utf-8"))
    log = (data / "scan-log.txt").read_text(encoding="utf-8").splitlines()
    applied = load_applied(data / "applied.csv")
    new, changed, dropped, closed = build(cands, seen, state, cfg, a.date, applied)
    text = render(new, changed, dropped, closed, log, a.date, settings_notices(cfg))
    if a.dry_run:
        print(text); return 0
    (data / "reports").mkdir(exist_ok=True)
    quiet = not (new or changed or closed)
    path, write = report_path(data / "reports", a.date, quiet)
    if write:
        path.write_text(text, encoding="utf-8")
    sp.write_text(json.dumps(update_seen(seen, new, dropped, changed, closed, a.date, applied, cands), ensure_ascii=False, indent=1), encoding="utf-8")
    print(text.splitlines()[2] if len(text.splitlines()) > 2 else text)
    print(f"Report saved to {path}" if write else f"Nothing new since today's earlier report, which is unchanged: {path}")
    return 0

if __name__ == "__main__":
    sys.exit(common.run_main(main))
