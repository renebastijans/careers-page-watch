"""Shared helpers: data folder, config, polite HTTP. Standard library only."""
import json, os, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEFAULTS = {
    # Which job titles to look at (case-insensitive regex) and which to ignore.
    "title_regex": "research|insight",
    "title_exclude_regex": "security|vulnerab|penetration",
    # Places where you can work. Matching is case-insensitive on whole words.
    "eligible_places": [],
    # Wider phrases that may include your place (EU, EMEA, worldwide...).
    "place_synonyms": ["europe", "european", "EU", "EMEA", "worldwide", "anywhere", "global"],
    # Most days a week you accept in an office. null = do not check.
    "max_office_days": None,
    # Informational only: the standalone report does not read pay.
    "pay_floor": None,
    "pay_currency": "EUR",
    # Used only by the optional Claude layer (AGENT.md step 8). null = no email.
    "report_email_to": None,
    # Claude layer: on a day with nothing new, still send a one-line note so you know it ran.
    "email_when_quiet": True,
    # Politeness towards the boards.
    "request_delay_seconds": 1.0,
    "user_agent": "careers-page-watch/0.1 (personal job search; read-only; one scan a day)",
}

def data_dir():
    """Where your private files live. Default ./data (gitignored). Override with CPW_DATA."""
    return Path(os.environ.get("CPW_DATA") or ROOT / "data")

class ConfigError(ValueError):
    """A problem with the user's settings, worded for a non-technical reader."""

FIX = "Fix it and run again. If you get stuck, delete the file and run `python3 init_data.py` to start over."

def _check(cfg, p):
    def bad(key, why):
        raise ConfigError(f'Your settings file {p} has a problem with "{key}": {why}. {FIX}')
    for k in ("eligible_places", "place_synonyms"):
        v = cfg[k]
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            bad(k, 'it must be a list of words in quotes, like ["Germany", "Berlin"]')
    m = cfg["max_office_days"]
    if m is not None and (isinstance(m, bool) or not isinstance(m, int) or m < 0):
        bad("max_office_days", "it must be a whole number such as 2, or null")
    for k in ("title_regex", "title_exclude_regex"):
        if not isinstance(cfg[k], str):
            bad(k, 'it must be words in quotes, separated by |, like "research|insight"')
        try:
            re.compile(cfg[k])
        except re.error as e:
            bad(k, f"it is not a valid pattern ({e})")
    d = cfg["request_delay_seconds"]
    if isinstance(d, bool) or not isinstance(d, (int, float)) or d < 0:
        bad("request_delay_seconds", "it must be a number of seconds such as 1.0")
    if not isinstance(cfg["email_when_quiet"], bool):
        bad("email_when_quiet", "it must be true or false")
    e = cfg["report_email_to"]
    if e is not None and (not isinstance(e, str) or "@" not in e):
        bad("report_email_to", "it must be one email address in quotes, or null")

def load_config(d=None):
    d = Path(d) if d else data_dir()
    cfg = dict(DEFAULTS)
    p = d / "search.json"
    if p.exists():
        try:
            user = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"Your settings file {p} has a typo near line {e.lineno}, column {e.colno} ({e.msg}). "
                              "Common causes: curly quotes instead of straight quotes (save as plain text), "
                              f"a missing comma between lines, or a missing bracket. {FIX}") from None
        if not isinstance(user, dict):
            raise ConfigError(f"Your settings file {p} must be one block in curly braces {{ }}. {FIX}")
        unknown = set(user) - set(DEFAULTS)
        if unknown:
            raise ConfigError(f"Your settings file {p} has settings the tool does not know: {sorted(unknown)}. "
                              f"Check the spelling against templates/search.example.json. {FIX}")
        cfg.update(user)
    _check(cfg, p)
    return cfg

def run_main(fn):
    """Run an entry point; show setup problems as one plain sentence, not a Python traceback."""
    try:
        return fn()
    except ConfigError as e:
        print(f"\nProblem: {e}", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"\nProblem: a file the tool needs is missing ({e.filename}). "
              "Run `python3 init_data.py` first, then check your data folder.", file=sys.stderr)
    return 1

_last = [0.0]

def get(url, cfg, timeout=30):
    """One GET with a plain user agent, spaced by request_delay_seconds. Returns text."""
    wait = cfg["request_delay_seconds"] - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": cfg["user_agent"]})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    finally:
        _last[0] = time.monotonic()
