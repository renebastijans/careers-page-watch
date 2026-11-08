# Changelog

## 0.1.0 (draft, not yet released)

First public-ready version.

- Standalone scan, ad-text reading and markdown report for Greenhouse, Ashby and Lever boards (Workable, SmartRecruiters and Teamtailor experimental), with no packages and no account.
- Location rules from `search.json`: eligible places, wider phrases (EU, EMEA), maximum office days. The report quotes the line from the ad that decides, and says `[verify location]` when the ad is silent.
- Remembers every ad seen and why it was dropped; reports new, changed and closed ads; never overwrites an earlier report.
- "Probably not open to you" group for ads whose board names only other places (listed, never deleted).
- Optional Claude layer: setup interview (`AGENTS.md`), judgement run (`AGENT.md`), optional email to one address you choose, optional scheduled task (every weekday or weekly, never more than daily) with a backup run and a one-line quiet-day note.
- `data/applied.csv`: tell the tool what you applied for (in the Claude route, just say so); applied roles are not listed as new again, and you are told if one changes, is reposted or closes.
- `find_board.py`: finds a company's job board system and board name from its careers page address (including boards loaded by JavaScript) or from its name, and shows the first job titles to confirm it is the right company.
- Mac guide for first-time users, double-click launcher, plain-language error messages, uninstall guide.
- Tests run offline; an opt-in live smoke test checks the three supported APIs.
