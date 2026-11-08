# Keep your own files outside the repo

All personal files (`search.json`, `companies.csv`, `criteria.md`, `seen.json`, `applied.csv`, `reports/`) live in one data folder. By default `./data` (gitignored). To keep them elsewhere, set `CPW_DATA`:

```bash
export CPW_DATA="$HOME/job-search"
python3 init_data.py && ./run.sh
```

Update the code with `git pull`; your data folder is untouched. The Claude layer reads the same folder: `AGENT.md` always means `$CPW_DATA` (or `./data`) when it names a file.
