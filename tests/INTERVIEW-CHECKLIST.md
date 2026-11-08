# Interview acceptance checklist (manual)

`tests/test_contract.py` guards the wording of the instructions. It cannot show what Claude actually does, so run this by hand
before a release and after any edit to `AGENTS.md` or `AGENT.md`. Use a fresh unzip, delete old scheduled tasks first, and
answer "set me up" with real answers. Record each failure with a screenshot.

## Questions
- [ ] Every question starts "Question N of 10: Label." in bold; the follow-up is "Question 3b of 10: Exclusions."
- [ ] The text matches `tests/interview_contract.json`. One question per message; nothing repeated after a tool call.
- [ ] 3b arrives as its own message after the answer to 3.
- [ ] Question 8 names careers-page-watch.
- [ ] Question 10 lists the starter employers and offers (a), (b), (c). Choosing (c) leaves no starter rows in `companies.csv`.
- [ ] Employers are looked up with `python3 find_board.py`, not improvised shell loops. Give it a company whose jobs load through JavaScript (for example Superhuman's job link) and check that it finds the board.
- [ ] No red "Failed" step anywhere; no field-specific examples in question 1.

## After the answers
- [ ] The first report is emailed (if an address was given). Subject exactly "…: N worth a look" or "…: quiet".
- [ ] Companies on other systems are listed as full `https://` links, never a bare `name.com`.
- [ ] The time question is open: no suggested times as buttons. Any typed time is accepted.
- [ ] The plan (run, backup two hours later, quiet-day note) is stated before anything is created; a clear yes is required.
- [ ] Scheduled > Yours shows exactly two tasks, "Job ad report" and "Job ad report backup".
- [ ] The closing message covers: created files, exact employers, what happens next, what it needs, changing settings,
      "I applied…", the uninstall link, and "only reports". No internal task names or ids.

## Afterwards
- [ ] "I applied to <company>, <role>, on <date>" adds a row to `data/applied.csv`.
- [ ] Optional: "no backup" and "no notes" give one task and `"email_when_quiet": false`.
- [ ] Uninstall page steps work (three dots > Delete; delete the Setup chat).
