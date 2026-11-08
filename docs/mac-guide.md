# Getting started on a Mac, step by step

For people who have never used Terminal. It takes about 15 minutes the first time. You do not need to understand the code. Windows is not covered and has not been tested.

Prefer to be guided? If you have a paid Claude plan (Pro or above), open the Code tab of the Claude desktop app, click **Choose folder** (next to *This computer*), pick the `careers-page-watch-main` folder and say "set me up". It asks you questions, writes the settings files and runs the first report for you, so you can skip steps 4 to 7. You still need Python (step 3), because the tool runs on it.

## 1. Download the tool
On the project's GitHub page, click the green **Code** button, then **Download ZIP**. Double-click the ZIP in your Downloads folder. It creates a folder called `careers-page-watch-main`. Move that folder somewhere you will find it, such as Documents, and keep its name: the steps below use it.

## 2. Open Terminal
Press **Command + Space**, type **Terminal**, press **Enter**. A window with a text prompt opens. Everything below is typed there, followed by **Enter**.

## 3. Check that Python is installed
Python is a free program that runs the tool. Type this in the **Terminal window** you opened in step 2 and press **Enter**:

```
python3 --version
```

- If it answers `Python 3.something`, you are set. Skip to step 4. (Tested on 3.11 and 3.15.)
- If it says **`command not found`**, Python is not installed. Install it like this:
  1. Go to **python.org/downloads** and click the big **Download Python 3.x** button for macOS.
  2. Open the downloaded file and click **Continue** through the installer (agree to the licence, then **Install**; your Mac password is asked once).
  3. When it finishes, a folder called **Python 3.x** opens. Double-click **Install Certificates.command** in it and wait for it to finish. This lets Python check website certificates; without it the tool can fail with `CERTIFICATE_VERIFY_FAILED`.
  4. **Close Terminal completely and open it again** (Terminal only notices new programs when it starts), then run `python3 --version` once more.
- If instead a window asks to install the **command line developer tools**, click **Install**, wait (it can take several minutes) and run the command again. Either route works.

On a Mac running macOS Tahoe 26.6.2, typing `python3 --version` gave `command not found`, and the python.org route above fixed it. Other macOS versions may behave differently; the python.org route is the dependable one.

## 4. Go to the folder
If you put the folder in Documents, type this in the **Terminal window**, as **one line**, and press **Enter** once:

```
cd ~/Documents/careers-page-watch-main
```

Check you are in the right place by typing `ls` and pressing Enter. You should see files such as `README.md`, `scan.py` and `run.sh`.

Put the folder somewhere else? Type `cd` and a **space**, but **do not press Enter yet**. Drag the folder from Finder into the Terminal window; its address appears after the space. Now press **Enter**. (If you pressed Enter after `cd` alone, nothing is wrong: just start this step again. Pasting an address with no `cd` in front gives "permission denied".)

## 5. Create your settings
Type this in the **Terminal window** from step 4 and press **Enter** (if you closed it, repeat steps 2 and 4 first):

```
python3 init_data.py
```
It prints a few lines starting with `wrote`. It has created a folder called `data` with your settings. Nothing leaves your computer.

## 6. Tell it where you can work
Type this in the **Terminal window** (still in the project folder) and press **Enter**. It opens the data folder in Finder:

```
open data
```

Open `search.json` with **TextEdit** (right-click, **Open With**, **TextEdit**). The file must stay plain text. Open the **Format** menu: if it offers **Make Plain Text**, choose it; if it offers **Make Rich Text** instead, the file is already plain text and you need do nothing. Then open **Edit**, then **Substitutions**, and make sure **Smart Quotes** has no tick: a tick makes TextEdit turn straight quote marks into curly ones, which break the file. Change only these lines:

- `"eligible_places"`: the countries or cities you can work from, for example `["Germany", "Berlin"]`.
- `"max_office_days"`: the most days a week you accept in an office, for example `2`, or `null` if it doesn't matter.
- `"title_regex"`: words in job titles you want, separated by `|`, for example `"research|insight"`.

Keep the quotation marks, commas and brackets exactly as they are. Save the file. If you break it, delete `search.json`, run step 5 again and start over.

`companies.csv` is the list of employers to watch. It starts with 6 well-known examples (not a recommendation). Open it in TextEdit as plain text. Each row looks like this, with commas between the parts and no spaces around them:

```
Example Co,software,,greenhouse,exampleco,,
```

The parts are: company name, sector (any word), an empty size, the job board system, the board's name, and two empty ones. To find the last two, open the company's careers page and click a job. If the address looks like `boards.greenhouse.io/exampleco/...` or `job-boards.greenhouse.io/exampleco/...`, the system is `greenhouse` and the board name is `exampleco`. Likewise `jobs.ashbyhq.com/exampleco` is `ashby` and `jobs.lever.co/exampleco` is `lever`. Three more are experimental: `apply.workable.com/exampleco` is `workable`, `careers.smartrecruiters.com/ExampleCo` (or `jobs.smartrecruiters.com/ExampleCo/...`) is `smartrecruiters`, and for a Teamtailor careers site (often `careers.example.com`) use `teamtailor` and the site address. **Easier: let the tool find the board for you.** This is typed in the **Terminal window**, not in TextEdit.

1. Go back to the Terminal window from step 4. Its last line should end with the project folder's name, for example `careers-page-watch-main %`. If you closed it, repeat steps 2 and 4 first.
2. Type the line below, put the company's careers page address (copy it from your browser, keep the quote marks) in place of the example, and press **Enter**:

```
python3 find_board.py "https://example.com/careers"
```

   You can also type just the company's name, for example `python3 find_board.py "GitLab"`. An address works better, and a link to a single job also works.
3. Wait up to a minute while it reads the page. It prints something like this:

```
== GitLab
  greenhouse       gitlab        248 jobs, for example: AI Transformation Owner, CRO; ...
  -> companies.csv row: <Name>,<sector>,,greenhouse,gitlab,,
```

4. Check that the job titles really belong to that company. Then copy the line after `companies.csv row:` into `companies.csv` as a new row, replacing `<Name>` with the company's name and `<sector>` with any word, such as `software`.
5. If it says "Nothing usable found", the company uses a system the tool cannot read. Put `browser` as the system and the careers page address in place of the board name; the report then lists the company under "check by hand" with that link.

Keep the rows in alphabetical order.

## 7. Run it
Type this in the **Terminal window** (the same one, still in the project folder) and press **Enter**:

```
./run.sh
```

It takes a minute or two and prints where it saved the report, for example `data/reports/report-2026-11-08.md`. To read it, type `open -e` and a space, then that path, and press **Enter**. For example: `open -e data/reports/report-2026-11-08.md`.

Instead of typing, you can also double-click **run.command** in the project folder in Finder. It runs the same steps and then opens your report by itself.

**The first double-click is blocked by macOS** ("Apple could not verify run.command is free of malware"). This happens to any script that arrived from another computer or a download, and only the first time. To allow it: click **Done** (not "Move to Trash"), open **System Settings**, then **Privacy & Security**, scroll to **Security**, click **Open Anyway** next to the line about `run.command`, and enter your Mac password. These steps were tested on macOS Tahoe 26.6.2; older versions may differ (some let you right-click the file and choose **Open** instead). Only do this for a file you downloaded from the project yourself and are happy to run; you can read `run.command` in TextEdit first, it is short. If you would rather not, skip the launcher and type `./run.sh` in Terminal instead.

## 8. Read the report
It is saved in `data/reports/` as `report-DATE.md`; TextEdit opens it.

- **eligible** with a quote: the ad's own words say you can apply from where you live. Check the ad.
- **[verify location]**: the ad doesn't say. Read the ad before you decide.
- **Probably not open to you**: the ad doesn't say, and the board names only other places (for example "Remote, US"). Still listed, never deleted; open one if you want to check.
- **Dropped**: the ad said something that rules it out, with the quote.
- A day with nothing new is a single line.

The tool only reports. It never applies for anything or contacts anyone.

## 9. Run it again
Run it once a weekday, no more. If you run it again the same day, your earlier report is kept: a rerun with nothing new leaves it alone, and one with something new saves a second file (`report-DATE-2.md`). Double-click `run.command`, or type `./run.sh` in the **Terminal window** (in the project folder), or see [scheduling.md](scheduling.md) to have it run by itself.

## 10. Tell it when you apply
Open `data/applied.csv` in TextEdit (or Numbers) and add a line for each role you apply for, with commas between the parts: company, job title, the ad's link, the date, and an optional note. This is a line to add in the file, not something to type in Terminal. For example:

```
Example Co,Senior Researcher,https://example.com/job/123,2026-11-05,via recruiter
```

The tool then stops listing that role as new and tells you if it changes or closes. In the Claude route you can simply say "I applied to Example Co, Senior Researcher, on 5 Nov" instead.

## Common problems
- **`CERTIFICATE_VERIFY_FAILED`** in the report footer: your Python can't check website certificates. Find **Install Certificates.command** in the Python folder in Applications and double-click it, then run again.
- **`Problem: Your settings file … has a typo near line N`**: the message tells you the line to look at in `data/search.json`. Usual causes are curly quotes (see step 6: keep the file plain text and untick Smart Quotes in TextEdit), a missing comma at the end of a line, or a missing bracket. Fix it and run again, or delete the file and repeat step 5.
- **`Scan failed for all boards`**: usually no internet connection or the certificate problem above.
- **`Permission denied`** on `./run.sh` or `run.command`: type `chmod +x run.sh run.command`, press Enter, and try again.
- **Anything else:** best effort, no support. You can open an issue on GitHub; please don't paste personal details.
