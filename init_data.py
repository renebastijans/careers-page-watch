#!/usr/bin/env python3
"""Creates your private data folder (default ./data, or $CPW_DATA) from the templates. Never overwrites."""
import shutil
import common

FILES = {"search.example.json": "search.json", "companies.starter.csv": "companies.csv",
         "criteria.md": "criteria.md", "seen.json": "seen.json", "applied.csv": "applied.csv",
         "discovery-log.md": "discovery-log.md"}

def main():
    d = common.data_dir(); d.mkdir(parents=True, exist_ok=True)
    for src, dst in FILES.items():
        if (d / dst).exists():
            print(f"kept   {d / dst}")
        else:
            shutil.copy(common.ROOT / "templates" / src, d / dst); print(f"wrote  {d / dst}")

if __name__ == "__main__":
    main()
