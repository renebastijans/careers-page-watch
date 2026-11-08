#!/usr/bin/env python3
"""Adds the ad's own location/policy sentences to each candidate in candidates.json.
Decisions about location must rest on `policy_lines` (the ad text), not on the board's location field.
Empty policy_lines means the ad text was not readable: treat as unverified. Read-only."""
import hashlib, html, json, re, sys
from urllib.parse import urlparse, parse_qs
import common

# Regex fragments (not escaped); place words from the config are escaped separately.
BASE_WORDS = ["remote", "hybrid", r"on-?site", r"in[- ]office", "office", "timezone", "time zone",
              "based in", r"relocat\w*", r"commut\w*", "work from", "eligible", "countries", "country",
              "travel", "days a week", "days per week", "per week"]

def place_words(cfg):
    return list(cfg.get("eligible_places", [])) + list(cfg.get("place_synonyms", []))

def place_pattern(w):
    """Short all-capitals words (US, UK, EU, SF) must match in capitals only: otherwise "us" in "join us" counts as a place."""
    esc = re.escape(w)
    return f"(?-i:{esc})" if len(w) <= 3 and w.isupper() else esc

def build_key(cfg):
    words = BASE_WORDS + [place_pattern(w) for w in place_words(cfg)]
    return re.compile(r"\b(" + "|".join(words) + r")\b", re.I)

def build_title_signal(cfg):
    words = ["remote"] + [place_pattern(w) for w in place_words(cfg)]
    return re.compile(r"\b(" + "|".join(words) + r")\b", re.I)

def text_of(raw):
    t = html.unescape(raw)
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S)
    t = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[ \t\r\f]+", " ", t)

def sr_text(d):
    """Plain text of a SmartRecruiters posting: location lines plus every ad section."""
    loc = d.get("location") or {}
    lines = [x for x in (loc.get("fullLocation"), loc.get("hybridDescription")) if x]
    sections = (d.get("jobAd") or {}).get("sections") or {}
    lines += [text_of(s.get("text", "")) for s in sections.values()]
    return "\n".join(lines)

def ad_text(c, cfg):
    url = c["url"]; u = urlparse(url); parts = [p for p in u.path.split("/") if p]
    try:
        if "ashbyhq.com" in u.netloc and len(parts) >= 2:
            d = json.loads(common.get(f"https://api.ashbyhq.com/posting-api/job-board/{parts[0]}", cfg))
            for j in d.get("jobs", []):
                if j.get("id") == parts[1]:
                    return j.get("descriptionPlain") or text_of(j.get("descriptionHtml", ""))
        if "greenhouse.io" in u.netloc or "gh_jid" in url:
            jid = parse_qs(u.query).get("gh_jid", [parts[-1] if parts else ""])[0]
            board = parts[0] if "greenhouse.io" in u.netloc and parts[0] != "embed" else c.get("slug", "")
            d = json.loads(common.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}", cfg))
            return text_of(d.get("content", ""))
        if "smartrecruiters.com" in u.netloc and len(parts) >= 2:
            d = json.loads(common.get(f"https://api.smartrecruiters.com/v1/companies/{parts[0]}/postings/{parts[1].split('-')[0]}", cfg))
            return sr_text(d)
        if "lever.co" in u.netloc and len(parts) >= 2:
            d = json.loads(common.get(f"https://api.lever.co/v0/postings/{parts[0]}/{parts[1]}", cfg))
            return d.get("descriptionPlain", "") + "\n" + "\n".join(
                (l.get("text", "") + " " + text_of(l.get("content", ""))) for l in d.get("lists", []))
    except Exception:
        pass
    try:
        return text_of(common.get(url, cfg))   # fallback: raw page (may be empty for JS-only pages)
    except Exception:
        return ""

def extract_policy_lines(text, key, limit=12):
    lines = []
    for ln in re.split(r"\n+|(?<=[.!?])\s+", text):
        ln = ln.strip()
        if 8 < len(ln) < 400 and key.search(ln) and ln not in lines:
            lines.append(ln)
    return lines[:limit]

def title_remote_signal(title, signal):
    return bool(signal.search(title or ""))

def policy_hash(lines):
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:12]

def enrich(c, text, cfg):
    lines = extract_policy_lines(text, build_key(cfg))
    c["policy_lines"] = lines
    c["title_remote_signal"] = title_remote_signal(c.get("title", ""), build_title_signal(cfg))
    c["policy_hash"] = policy_hash(lines)
    return c

def run(data, cfg):
    p = data / "candidates.json"
    cands = json.loads(p.read_text(encoding="utf-8"))
    for c in cands:
        text = text_of(c.pop("description", None) or "") or ad_text(c, cfg)   # Workable sends the text with the list
        enrich(c, text, cfg)
    p.write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"enriched {len(cands)} candidates; {sum(1 for c in cands if not c['policy_lines'])} with no readable policy text")

if __name__ == "__main__":
    sys.exit(common.run_main(lambda: run(common.data_dir(), common.load_config())))
