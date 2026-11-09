# Keep your own files outside the repo

All personal files (`search.json`, `companies.csv`, `criteria.md`, `seen.json`, `applied.csv`, `reports/`) live in one data folder. By default `./data` (gitignored). To keep them elsewhere, set `CPW_DATA`:

```bash
export CPW_DATA="$HOME/job-search"
python3 init_data.py && ./run.sh
```

Update the code with `git pull`; your data folder is untouched. The Claude layer reads the same folder: `AGENT.md` always means `$CPW_DATA` (or `./data`) when it names a file.

## Add boards the tool does not read (advanced)

If an employer uses a system the tool does not support, you can add your own reader. Put a file called `custom_boards.py` in your data folder:

```python
import common

def fetch(name, slug, cfg):
    html = common.get(f"https://careers.example.com/{slug}", cfg)
    # ...parse it yourself...
    return [{"title": "Senior Researcher", "location": "Remote, Europe", "remote": True,
             "url": "https://careers.example.com/jobs/123", "posted": None}]

BOARDS = {"mysystem": fetch}
```

Then give the company row `ats=mysystem`. The reader returns a list of ads; `description` is optional (without it the tool opens the ad's `url` to read the text). Everything after that (filters, report, `seen.json`) works as usual, and the scan log marks these rows "(custom)".

This is your own code and it runs with your permissions, so only use code you wrote or trust. It cannot replace the built-in board types (`ashby`, `greenhouse`, `lever`, `workable`, `smartrecruiters`, `teamtailor`, `browser`, `skip`, `unknown`). Without the file nothing changes.
