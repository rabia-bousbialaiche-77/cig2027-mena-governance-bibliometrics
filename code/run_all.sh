#!/usr/bin/env bash
set -e
export PYTHONHASHSEED=${PYTHONHASHSEED:-0}
cd "$(dirname "$0")"
python3 01_retrieve_crossref.py
python3 02_screen.py
python3 03_enrich.py
python3 04_analysis.py
python3 05_refmeta.py
python3 06_extra_stats.py
python3 07_prisma.py
