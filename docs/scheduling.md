# Scheduling

One scan a day is the intended use. Do not run it more often.

**cron (macOS or Linux), weekdays 09:30:**

```
30 9 * * 1-5  cd /path/to/careers-page-watch && CPW_DATA=/path/to/data ./run.sh >> /path/to/data/run.log 2>&1
```

**GitHub Actions:** keep your data out of a public repo. Run it only from a private repo of your own, and store `data/` there deliberately; reports can contain your search criteria.

**Claude scheduled tasks (Claude layer):** the setup interview offers to create these for you. To make them yourself, create two tasks.

Main run (weekdays at the time you choose, or one day a week for a weekly rhythm):

> Open the careers-page-watch folder and follow AGENT.md. Today's run only; report only, never apply or contact anyone, and email only the address in search.json.

Backup run (about two hours later, same days):

> Open the careers-page-watch folder and follow AGENT.md. This is a BACKUP run: if today's report already exists in data/reports, stop and do nothing and send nothing. Otherwise do today's run. Report only, never apply or contact anyone, and email only the address in search.json.

- **Why a backup:** a scheduled task only runs while the computer is awake and the Claude app is open. If the first run is missed, the backup picks it up the same day; if the first run worked, the backup does nothing.
- **Quiet days:** by default you get a one-line email so you know it ran. Set `"email_when_quiet": false` in `search.json` to switch that off.
- **Never more than once a day:** the tool is polite to the boards, so it does not offer a faster rhythm.
- **Delay and Auto mode:** the app adds a short delay to spread its load (a task set for 09:30 ran at about 09:44 in a test), and the task is saved in Auto mode, so a run uses tools and connectors without asking first. That is why the instructions limit it to reading, writing inside your data folder and emailing only your own address. You can edit, pause or delete tasks under **Scheduled**.

**Check the first run by hand** before relying on a schedule.
