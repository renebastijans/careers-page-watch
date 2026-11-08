"""Opt-in live check: one request per supported ATS against a public board, parsed with scan.py's parsers.
Run by hand or via the manual GitHub workflow. Not part of the unit tests (no network there)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import common, scan

def main():
    cfg = dict(common.DEFAULTS)
    boards = {"ashby": ("Notion", "notion"), "greenhouse": ("GitLab", "gitlab"),
              "lever": ("Contentsquare", "contentsquare")}   # one public board per supported system
    failed = 0
    for ats in sorted(scan.SCANNED):
        r = {"name": boards[ats][0], "slug": boards[ats][1]}
        try:
            jobs = scan.PARSERS[ats](json.loads(common.get(scan.board_url(ats, r["slug"]), cfg)))
            ok = len(jobs) > 0 and all(j["title"] and j["url"] for j in jobs)
        except Exception as e:
            ok = False; print(f"{ats}: {type(e).__name__}: {e}")
        print(f"{ats} ({r['name']}): {'ok' if ok else 'CHANGED OR BROKEN'}")
        failed += not ok
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
