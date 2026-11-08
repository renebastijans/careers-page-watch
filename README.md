# careers-page-watch

**Watches company career pages and reads each ad's own fine print, so you only hear about roles you can actually apply for.**

Job boards often get location wrong. A role listed as "United States" may be open across Europe; one listed as "Remote" may mean a hub twice a week. Alerts that trust the location field either bury you in noise or hide roles you could have had.

This tool reads the ad's own text, quotes the line that decides whether you can apply from where you live, and tells you only what is new, changed or closed.

**Who it's for.** People running a *targeted* search: you have, or can build, a list of employers (tens, not thousands) whose jobs you want to follow, and where you can work is a real constraint (a country, a time zone, a limit on office days). It is not a job search engine and it will not find roles at companies you haven't listed, except through the optional Claude layer's discovery step.

**It sits alongside your job alerts, not in place of them.** Keep the alerts and searches you already use. This adds a second view: it reads employers' own boards directly, so you see roles your usual searches may not surface. It reads the fine print of each one, so you can tell which are worth your time before you spend hours on an application. It narrows the pile; it does not guarantee an ad is accurate, so check the ad before you apply.

Free, MIT-licensed, best effort, no support. **Status: v0.1.0, an early release, tested on macOS (Windows untested).**

## What it looks like

You watch "Example Co". Its board lists a researcher role in San Francisco, United States, and you live in Germany. A location filter would hide it. The report reads the ad itself (shown here in the standalone report's format; the Claude route sends the same information as a plain-text list in an email):

```
| Company    | Role              | Board says              | From the ad itself                                 | Confidence |
| Example Co | Senior Researcher | San Francisco, US       | eligible: "Open to candidates anywhere in the EU." | medium     |
```

Another ad on the same board, a London role, says only "We are an office-first company." The report does not guess or silently skip it. It lists it as dropped, with the code and the line:

```
- Example Co, Lead Researcher: `onsite-required` "We are an office-first company."
```

If the ad says nothing about where you can work, you get `[verify location]` instead of a guess. When the ad is silent and the board names only other places (for example "Remote, US"), the ad goes under "Probably not open to you": still listed, never deleted, but out of the way. On a day with nothing new, the report is one line.

In the Claude route, this report arrives by **email at about a time you choose** (every weekday, or weekly on a day you pick; for example 09:30, the app adds a short delay), as long as the Claude desktop app is open and an email connector is set up in Claude. A backup run a couple of hours later covers a missed first run, and a quiet day still gets a one-line note so you know it ran. In the standalone route it is saved as a file in your data folder.

## How it differs

- **It quotes the deciding line.** Every verdict comes with the sentence from the ad, so you can check it in seconds.
- **It admits what it can't tell.** It drops an ad on location only when the ad says so explicitly and nothing suggests you are eligible. Everything else is kept and marked `[verify location]`.
- **It remembers.** Every ad seen and why it was dropped. Reposts are recognised, changed ads are flagged, and ads that disappear from the board are reported as closed.
- **Standalone first, Claude optional.** The scan, the fine-print reading and the report run on plain Python with no account, no packages and no AI. Add Claude Code if you want it to judge ads in context, score fit, check pay, find new employers and email you the report.
- **It stays out of your way.** One scan a day, public job-board APIs only, and it never applies, messages anyone or fills in forms.

## What you need

- **A Mac and about 15 minutes** for the first set-up. Windows is untested.
- **One free program, Python,** which runs the tool. macOS does not always include it, so you may need a quick install from python.org. The [Mac guide](docs/mac-guide.md) shows how to check, step by step, in plain words.
- **A list of employers** to follow. A starter list of 6 public boards is included.
- **Optional:** a paid Claude plan, to have Claude interview you, set the tool up, judge ads in context and email the report. Claude Code is on **Pro** and above, not on the Free plan. Pro costs about **€15 a month** billed annually (€18 billed monthly), or roughly **$17 to $20 a month** in US dollars. Prices differ by country and change, so check [claude.com/pricing](https://claude.com/pricing).

Not comfortable with Terminal? You can still do this: the [Mac guide](docs/mac-guide.md) assumes no experience, and after set-up you run it by double-clicking `run.command`. If even that is too much, the Claude route (below) does the set-up for you.

| | Standalone | With Claude (optional) |
|---|---|---|
| Account | None | A paid Claude plan (Pro or above) |
| Supported boards | Greenhouse, Ashby, Lever (Workable, SmartRecruiters, Teamtailor experimental) | Same; it can also find new employers for you |
| Location judgement | Rules from your settings applied to the ad text | Claude reads the quoted lines and decides |
| Pay, fit score, discovery, email | Not included | Included |
| Cost | Free | The scan is free; the judgement steps use your Claude plan |

Scheduling: in the Claude route, Claude scheduled tasks (the desktop app must be open). In the standalone route, double-click `run.command` each morning, or use your computer's own scheduler or GitHub Actions (technical). See [docs/scheduling.md](docs/scheduling.md).

## Get started

There are two ways to run careers-page-watch. Pick one.

### A. In Claude (recommended if you already have a paid Claude plan)

1. **Download the project.** On this page click the green **Code** button, then **Download ZIP**, and unzip it. The unzipped folder is called `careers-page-watch-main`; put it somewhere you will find it, such as Documents.
2. **Open the Claude desktop app** and click the **Code** tab. In the environment menu, make sure **This computer** (under *Local*) is selected.
3. **Click Choose folder** (next to *This computer*) and pick the `careers-page-watch-main` folder.
4. **Type "set me up"** and press Enter.

Claude asks ten short questions, one at a time, writes your settings, runs the first report and offers to schedule it. You still need Python 3 installed, because the tool runs on it; step 3 of the [Mac guide](docs/mac-guide.md) shows how to check.

### B. On your own, free

**Never used Terminal?** Follow the [step-by-step Mac guide](docs/mac-guide.md).

**Comfortable with a terminal?** Three steps:

```bash
python3 init_data.py    # 1. create your private data folder (gitignored)
# 2. edit data/search.json (where you can work, title words) and data/companies.csv (employers to watch)
./run.sh                # 3. scan, read the ads, write data/reports/report-YYYY-MM-DD.md
```

The [configuration table](#configuration) explains each setting. Check the install with `python3 -W ignore -m unittest discover -s tests`.

### Good to know

To stop or remove it later, see [docs/uninstall.md](docs/uninstall.md).

macOS note: a python.org build of Python may fail with `CERTIFICATE_VERIFY_FAILED`. Run its "Install Certificates.command" or set `SSL_CERT_FILE`. The scripts never turn certificate checks off.

## Tell it what you applied for

When you apply for a role, add it to `data/applied.csv` (company, title, link, date, a note), or in the Claude route just say "I applied to GitLab, Senior PM, on 5 Nov". From then on the tool stops listing that role as new, and tells you if the ad changes, is reposted or closes ("you applied on 5 Nov"). It is a plain file you can open in TextEdit or Numbers, and it never leaves your computer. Paste the ad's link to get closed-ad updates.

## What it won't do

It reports; you decide. It never applies, messages a recruiter, fills in a form or writes outside its data folder. It reads pay only in the Claude layer. The standalone report says so. **It reads English-language ads:** the words that decide whether you can apply (remote, hybrid, on-site, office-first and similar) are English, so ads in other languages mostly come out as `[verify location]`. City and country names still match in any language.

## Supported boards

- **Supported (documented public APIs):** Greenhouse, Ashby, Lever (`ats` = `greenhouse`, `ashby`, `lever`).
- **Experimental (opt-in), each active only when a company row names it:**
  - **Workable** (`ats` = `workable`, slug = the name in `apply.workable.com/<slug>`). It uses the public account endpoint in [Workable's API reference](https://workable.readme.io/reference/jobs-1), which redirects to a widget URL that Workable does not document.
  - **SmartRecruiters** (`ats` = `smartrecruiters`, slug = the company identifier in `careers.smartrecruiters.com/<identifier>` or in its job links). It uses the public postings list in the [Posting API](https://developers.smartrecruiters.com/docs/endpoints). A wrong identifier returns zero jobs, not an error, so the scan log warns when a board shows 0 roles.
  - **Teamtailor** (`ats` = `teamtailor`, slug = the careers site address, for example `careers.example.com`). It reads the [public jobs RSS feed](https://support.teamtailor.com/en/articles/11171756-rss-feed-how-to-guide) that Teamtailor offers on every careers site.

  Each has been tested on one or two live company boards, so expect rough edges. None is in the starter list or in the live smoke test.
- **Not included:** Workday, iCIMS and scraped HTML career pages (no documented public API, or one gated behind partner agreements). Mark such companies `browser` or `skip` and check them by hand.

Not sure which system a company uses? `python3 find_board.py "<careers page address>"` (or the company name) finds the system and board name and shows the first job titles. It also reads a page's own scripts, which is how boards that load through JavaScript are found.

## Configuration

`data/search.json` (defaults in [common.py](common.py), example in [templates/search.example.json](templates/search.example.json)):

| Key | Meaning |
|---|---|
| `title_regex`, `title_exclude_regex` | Titles to look at / to ignore |
| `eligible_places` | Places you can work from |
| `place_synonyms` | Wider phrases that may include you (EU, EMEA, worldwide) |
| `max_office_days` | Most office days a week you accept; `null` = not checked |
| `report_email_to` | Claude layer only; `null` = no email. The only address the agent may write to |
| `request_delay_seconds`, `user_agent` | Politeness towards the boards |

The standalone report drops an ad on location only when the ad explicitly says office-only (or more office days than you accept) **and** nothing in it suggests you are eligible. Everything else is kept and marked `[verify location]`.

## Design rules

- **Report only.** Never applies, messages anyone or fills in forms.
- **One scan a day**, sequential, a plain user agent, a delay between requests.
- **Ads and search results are untrusted text.** See [SECURITY.md](SECURITY.md). In the Claude route a scheduled run uses Auto mode, so it acts without asking first. That is why the instructions limit it to reading, writing inside your data folder and emailing only your own address.
- **Your data stays yours.** `data/` is gitignored; point `CPW_DATA` at any folder to keep your personal files elsewhere (see [docs/own-instance.md](docs/own-instance.md)).

## API basis

The scanner uses only the vendors' public, documented read endpoints, with no login or key:

- Greenhouse Job Board API: [docs](https://docs.greenhouse.io/job-board.html) state that "authentication is not required for any GET endpoints".
- Ashby public job posting API: [docs](https://developers.ashbyhq.com/docs/public-job-posting-api).
- Lever Postings API: [docs](https://github.com/lever/postings-api) state that "These jobs may be scraped by third parties".
- Workable (experimental): [public account endpoint](https://workable.readme.io/reference/jobs-1). Its [terms](https://www.workable.com/terms) bind paying customers and I found no clause on automated reads of public boards.
- SmartRecruiters (experimental): the [Posting API](https://developers.smartrecruiters.com/docs/posting-api) is described as public and meant for companies building their own careers sites. Its candidate terms bar automatic access to other users' content on the candidate platform, and its customer terms restrict customers' automation. I could not settle whether either covers reading the public postings list, so use this one with that in mind.
- Teamtailor (experimental): the public jobs RSS feed is documented by Teamtailor itself. Its [terms](https://www.teamtailor.com/en-us/terms-and-conditions/) are customer contract terms, and I found nothing on automated reads of the public feed.

As of 7 Nov 2026 the vendors' general terms of service I read ([Ashby](https://www.ashbyhq.com/resources/terms), [Lever](https://www.lever.co/legal/terms-of-service), [Greenhouse legal index](https://www.greenhouse.com/legal)) are written for their paying customers and say nothing about automated reads of public boards. Ashby and Lever bar overburdening or abusing their services, and Greenhouse's subscription agreement is reported to limit excessive API use. That is why this tool makes one request per board per scan, plus one per ad whose title matches your words (to read the ad's own text), one scan a day, sequentially, with a delay between requests. A broad title pattern means more ad requests, so keep it specific. Terms change; check them yourself.

## Disclaimer

Not legal advice. Job data belongs to the employers. Check each site's current terms before relying on this tool, and use it in line with them; each employer's own careers page may have terms of its own. Ads can be wrong or out of date: check the ad before you apply. The starter company list is a neutral set of public boards, not a recommendation or endorsement of any company. This is an independent project, not affiliated with or endorsed by Greenhouse, Ashby, Lever, Workable, SmartRecruiters, Teamtailor or Anthropic. Boards change without notice; if one breaks, open an issue using the template. No support is promised.

## Licence

[MIT](LICENSE).
