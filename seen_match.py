"""Match a candidate ad against seen.json: exact URL first, then company + title.
A company + title match with a different URL is a repost of an ad already seen."""
import re

def squash(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower().replace("&", "and"))

def find_seen(url, company, title, seen):
    """Returns (kind, url, entry) with kind 'same-url' or 'repost', or None if the ad is new."""
    if url in seen:
        return ("same-url", url, seen[url])
    co, ti = squash(company), squash(title)
    if co and ti and not title.startswith("["):   # "[not recorded]" is a placeholder, never a title
        for u, e in seen.items():
            if squash(e.get("company")) == co and squash(e.get("title")) == ti:
                return ("repost", u, e)
    return None
