#!/usr/bin/env bash
# Standalone daily run: scan, enrich, report. No AI. Usage: ./run.sh
set -eu
cd "$(dirname "$0")"
python3 -W ignore scan.py
python3 -W ignore report.py
