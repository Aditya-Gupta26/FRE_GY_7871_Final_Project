"""Refresh the monitoring dashboard after new data (the brief's "updateable dashboard").

    python scripts/update.py                  # econ + survey data, gap, existing media codes, dashboard
    python scripts/update.py --with-text      # also re-pull news and Reddit to the new cutoff first

Steps that need no AI run automatically: FRED/ALFRED vintages, Michigan tables, the SF Fed index,
the real-time panel and gap (01, 04), the corpus build (05), media measures (09: own codes so far,
plus the dictionary and TF-IDF series on the whole corpus), the analysis (10) and the dashboard (12).
New headlines are coded by Claude Opus in a separate, documented Claude Code step (README: "Coding
new text"): scripts/06_make_samples.py writes new *_in.jsonl batches, an Opus subagent codes each
with prompts/coder_v1.md, and scripts/07_ingest_codes.py validates and merges them.
Before running, raise SAMPLE_END (the last survey month; all scripts read it), DATA_CUTOFF and MONITOR_END in
src/config.py. The October 2026 preliminary (UMICH_OCT2026_PRELIM) is used only until the final is in tbmics.csv.
"""
import _bootstrap  # noqa: F401
import subprocess
import sys

from src.config import ROOT

steps = []
if "--with-text" in sys.argv:
    steps += [["scripts/02_collect_news.py", "outlets"], ["scripts/02_collect_news.py", "releases"],
              ["scripts/03_collect_reddit.py"]]
steps += [["scripts/01_get_econ.py", "--refresh"], ["scripts/04_econ_baseline.py"], ["scripts/05_build_corpus.py"],
          ["scripts/09_media_measures.py"], ["scripts/09b_tierc_realtime.py"], ["scripts/10_analysis.py"],
          ["scripts/11_make_figures.py"], ["scripts/12_build_dashboard.py"]]
for s in steps:
    print(">>", " ".join(s), flush=True)
    r = subprocess.run([sys.executable, *s], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"step failed: {' '.join(s)}")
print("dashboard/index.html is up to date")
