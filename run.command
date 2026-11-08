#!/usr/bin/env bash
# Double-click launcher for macOS. First run: creates your data folder and stops so you can edit it.
# Later runs: scan, read the ads, write the report, then open it.
cd "$(dirname "$0")" || exit 1
pause() { echo; read -n 1 -s -r -p "Press any key to close this window."; echo; }

if ! python3 --version >/dev/null 2>&1; then
  echo "Python 3 is not available yet."
  echo "If a window asked you to install the command line developer tools, finish that, then double-click this file again."
  echo "Otherwise see docs/mac-guide.md, step 3."
  pause; exit 1
fi

DATA="${CPW_DATA:-./data}"
if [ ! -f "$DATA/search.json" ]; then
  python3 init_data.py
  echo
  echo "Your settings folder is ready. Next: open search.json and companies.csv in the folder that is about to open,"
  echo "set where you can work (see docs/mac-guide.md, step 6), then double-click this file again."
  open "$DATA"
  pause; exit 0
fi

./run.sh || { echo; echo "Something went wrong. See 'Common problems' in docs/mac-guide.md."; pause; exit 1; }
latest=$(ls -t "$DATA"/reports/report-*.md 2>/dev/null | head -n 1)
[ -n "$latest" ] && open -e "$latest"
pause
