# Final Project: AI, Economic Perceptions and Consumer Sentiment before the 2026 Midterms (Jan 2010 to Oct 12, 2026)

FRE-GY 7871 A · NLP and the Investment Process · Fall 2026

**Question in one line:** why is Michigan consumer sentiment so far below what unemployment, inflation and GDP growth would predict before the Nov 3, 2026 midterms, and is it (H1) household pressures the headline numbers miss, (H2) perceptions shaped by news coverage, framing or biases, or (H3) measurement, timing or an incomplete model? An AI coder (Claude Opus) measures tone, selection, framing, factual calibration and political attribution in news and Reddit. It is validated on 450 gold items labelled in two passes (Claude Sonnet 5.5 and Claude Haiku 5.5, each in its own context, plus my corrections to both) and adjudicated by Claude Fable 5.1, and the measures are tested against sentiment with chronological holdouts.

Repo: https://github.com/Aditya-Gupta26/FRE_GY_7871_Final_Project

**The deliverables:**
- `REPORT.pdf` is the 12-page report (built from `REPORT.md`).
- `analysis.ipynb` reproduces every table and figure in it, with the report's text copied in section by section.
- `dashboard/index.html` is the monitoring dashboard (one self-contained file; open it in any browser, works offline).
- `presentation/Final_Project_Presentation.pptx` is the 6 to 8 minute deck with speaker notes.
- `AI_USE.md` is the AI disclosure; `docs/CORPUS.md` is the corpus and data provenance; `data/labels/LABELLING_GUIDE.md` is the labelling guide; `prompts/` holds the exact prompts.

---

## What this gives you

Scripts, run in this order:

| Script | Does | Writes | Time |
|---|---|---|---|
| `01_get_econ.py [--refresh]` | ALFRED vintages and the real-time panel (each value as published by day 14 of the month), Michigan indexes and tables, SF Fed index, EPU, release calendar, revisions, and checks of the course file against BLS and BEA | `data/processed/`, `outputs/tables/data_*` | ~3 min |
| `02_collect_news.py outlets` then `releases` (`02b`, `02c` are extra workers for the same cached pulls) | Google News RSS: 34 outlets, one neutral query, monthly windows 2010 to 2025, weekly 2026; then release-day pulls for every jobs and CPI release | `data/raw/news/` | ~1.5 h with 3 workers |
| `03_collect_reddit.py` (`03b` = second worker) | Arctic Shift: r/Economics, r/economy, r/personalfinance in seeded time-stratified windows; usernames hashed at download | `data/raw/reddit/` | ~1 h |
| `04_econ_baseline.py` | RQ3: Model E, out-of-sample gap with bootstrap intervals, explained share, H1 controls (2010 to 2019 and 1992 to 2019), H3 variants, components and groups | `outputs/results_econ.json`, `outputs/tables/rq3_*` | ~2 min |
| `05_build_corpus.py` | filter waterfalls, MinHash near-duplicates, survey-month alignment | `data/interim/`, `outputs/tables/corpus_*` | ~3 min |
| `06_make_samples.py`, `06b_make_swaps.py` | seeded gold set, coding tiers, test-retest set and coder batches; the swap-test versions | `data/labels/`, `data/coded/` | ~1 min |
| **AI coding and labelling steps** (see below) | the coder subagents (Opus) code the batches; the two annotator passes (Sonnet, Haiku) label the gold sheets | `data/coded/batches/*_out.jsonl`, `data/labels/gold_prelabels_*.jsonl` | done once |
| `06d_human_label_tool.py`, then my corrections | builds the review tool (each pass pre-filled; it exports the reviewed items and the fields changed); my corrections to each pass | `data/labels/human/review_tool.html`, then `human/human_verified_{A,B}.jsonl` | ~1 s |
| `06c_make_adjudication.py`, then the adjudicator | sheets of the items where the two corrected passes differ (labels in random order, no names); two Fable subagents (one per sheet) settle them | `data/labels/adjudicate_*`, `gold_adjudicated_*.jsonl` | ~1 s |
| `07_ingest_codes.py [resend]` | validates every returned batch (codebook values, verbatim evidence, claim numbers in the text) and merges | `data/coded/codes.parquet`, `codes.csv` | ~10 s |
| `08_validation.py` | agreement, Opus vs gold by class, source and period, dictionary and TF-IDF baselines, test-retest, swap tests, minimal pairs | `outputs/results_validation.json`, `outputs/tables/val_*` | ~1 min |
| `09_media_measures.py` | monthly media measures (own Opus codes, Tier C, dictionary, SF Fed, EPU), quarterly and weekly series, reliability | `data/processed/media_*`, `outputs/results_media.json` | ~2 min |
| `09b_tierc_realtime.py` | real-time Tier C: for every forecast month, re-trains the classifiers on codes published before day 15 and rebuilds the series (used by the out-of-sample tests) | `data/processed/tierC_realtime.parquet` | ~2 min |
| `09c_tierc_checks.py` | how Tier C fits its training labels, cross-validates, scores on gold and agrees with Opus by quarter (report Figure 2; exploratory) | `outputs/results_tierc.json`, `outputs/tables/tierc_*` | ~10 s |
| `10_analysis.py` | RQ1, RQ2, RQ4, RQ5, RQ6, the scorecard, extra questions, monitoring numbers | `outputs/results.json`, `outputs/tables/rq*` | ~20 s |
| `10b_reddit_exploratory.py` | E3 (exploratory): Tier C scores every Reddit post; the monthly Reddit tone goes through the RQ2 tests | `outputs/results_reddit.json`, `outputs/tables/e3_reddit_*` | ~10 s |
| `10c_ablation.py` | E4 (exploratory): ablation of the postulated effects (price level, borrowing costs, partisan mood) on a 1978-2019 panel, plus a regional price panel | `outputs/results_ablation.json`, `outputs/tables/ablation_*` | ~5 s |
| `10d_ratchet.py` | E5 (exploratory): inflation memory, how far inflation has fallen from its 5-year peak, added to the economy model | `outputs/results_ratchet.json`, `outputs/tables/ratchet_panel.csv` | ~5 s |
| `10f_suspects.py` | E7 (exploratory): a fair split of the unexplained gap among the suspects (out of sample, Shapley values, block-bootstrap ranges) | `outputs/results_suspects.json` | ~10 s |
| `11_make_figures.py` | the seven report figures from the saved outputs | `outputs/figures/` | ~20 s |
| `12_build_dashboard.py` | the dashboard from the saved outputs | `dashboard/index.html` | ~10 s |
| `13_deck_data.py`, then `node presentation/build_deck.js` | the presentation's numbers from the saved outputs, then the deck (pptxgenjs: `npm install pptxgenjs`; native charts, speaker notes) | `presentation/deck_data.json`, `presentation/Final_Project_Presentation.pptx` | ~5 s |
| `update.py [--with-text]` | refresh for new data: econ data, gap, corpus, media series, analysis and dashboard (no AI call needed) | all of the above | ~10 min |
| `make_notebook.py` | builds `analysis.ipynb` from `REPORT.md` plus code cells; then run it with nbconvert | `analysis.ipynb` | ~5 min to execute |
| `build_report.py`, `99_lint_prose.py` | REPORT.md to PDF (markdown-it, WeasyPrint); checks for em dashes | `REPORT.pdf` | ~5 s |

The modules:

| Module | What it does |
|---|---|
| `src/config.py` | Paths, dates (window, monitoring window, cutoff), FRED/ALFRED series, Michigan tables, the news query and the 34 outlets with their AllSides group, Reddit settings, filters, the 2026 event calendar and upcoming releases, Michigan's mode effect, and the **pre-registration** (`PREREG`, written before any test) with its numbered notes and the one deviation (`PREREG_NOTES`). |
| `src/fred.py`, `src/realtime.py`, `src/umich.py`, `src/sources.py` | ALFRED vintages and "as of" lookups; the real-time panel with an assert that no value was published after day 14 of its month; Michigan data; BLS, SF Fed, EPU and the course-file check. |
| `src/econ_model.py`, `src/forecast.py`, `src/tests.py`, `src/granger.py` | Model E with EWC and Newey-West inference, prediction intervals, moving-block bootstrap; expanding nowcasts, Clark-West, Diebold-Mariano; asymmetry, Toda-Yamamoto with circular shifts, robustness value, MDE, Shapley. |
| `src/news.py`, `src/reddit.py`, `src/corpus.py`, `src/text_clean.py` | Collectors (cached, resumable) and the corpus build. |
| `src/sampling.py`, `src/coded.py`, `src/gold.py`, `src/validate.py`, `src/minimal_pairs.py` | Samples and batches; the code validator; the two annotator passes (model labels with my corrections); agreement and accuracy statistics; the minimal-pair suite. |
| `src/dictionary.py`, `src/baselines.py`, `src/media.py` | Loughran-McDonald dictionary rules; TF-IDF + logistic regression baselines (gold CV and the Opus-trained Tier C); monthly measures with equal outlet-group weights. |
| `src/plots.py` | One palette and style for all figures. |

### The AI coding and labelling steps

Every AI code and label in this project was made by Claude subagents in Claude Code, reading files on disk; no API key or paid model call is involved. The coder is Claude Opus 5.5; the gold annotators and adjudicator are deliberately other models (Sonnet 5.5, Haiku 5.5, Fable 5.1), so the answer key does not come from the model it grades. To repeat it (or to code new text after `update.py --with-text`):
1. `python scripts/06_make_samples.py` writes the batches `data/coded/batches/<name>_in.jsonl` (item ids and text only: no date, no outlet).
2. For each batch, start a Claude Code subagent (Opus) with: "Follow `prompts/coder_v1.md` exactly. Code `data/coded/batches/<name>_in.jsonl` and write `data/coded/batches/<name>_out.jsonl`." The prompt forbids code, keyword rules, the web and any other file. Up to 20 run in parallel.
3. `python scripts/07_ingest_codes.py resend` validates the outputs and writes `<name>_resend_in.jsonl` for any failed items; code those the same way and run `07` again.
4. **The gold labels.** I couldn't find other people to annotate, so each annotator pass is one model's labels plus my corrections:
   - Pass A is Sonnet 5.5 and pass B is Haiku 5.5. Each model ran as five separate subagents (one per 90-item sheet part), each in a folder holding only `prompts/annotator.md`, the guide and its own `gold_sheet_part<k>.csv`, so no pass saw the other's labels or the coder's codes. The labels are in `data/labels/gold_prelabels_{sonnet,haiku}_part*.jsonl`; how they were made is in `data/labels/gold_prelabels_README.md`.
   - `06d_human_label_tool.py` builds a review tool with each pass pre-filled. My corrections (12 items in A, 15 in B), each with its reason, are in `data/labels/human/human_verified_{A,B}.jsonl`, and every other label stays as the model gave it (`src/gold.py` combines the two).
   - `06c_make_adjudication.py` writes the items where the two corrected passes still differ, with the labels in random order and no names, and two Fable 5.1 subagents with `prompts/adjudicator.md` (one per sheet) write `gold_adjudicated_<k>.jsonl`. Then run `08`.

The coder prompt is frozen (sha256 prefix `3270f542f7bcd015`); a changed prompt is a new instrument and needs the validation (`08`) re-run. To add independent human annotators later, the plain mode of the same tool (`06d` without the model labels) lets two people label blind; point `src/gold.py` at their exports (`human_labels_{A,B}.jsonl`) instead of the model passes, then rerun `06c`, the adjudication and `08`.

### If a download will not run

- **FRED/ALFRED:** needs a free key in `.env` as `FRED_API_KEY=...` (chmod 600). The keyless CSV endpoint (`fredgraph.csv`) hung from my machine, so everything uses the API. ALFRED's QoQ GDP series has vintages only from Sep 2014, so QoQ is computed from GDPC1 vintages; U-6 vintages start Mar 2011 and real income per head May 2010 (those early months use the latest vintage and are flagged).
- **Michigan:** the public CSVs (`tbmics.csv`, `tbmiccice.csv`) end with the last final reading; the Oct 2026 preliminary (46.3, 44.7, 47.3) is set in `config.UMICH_OCT2026_PRELIM`. The historical tables end in Aug 2026. Table 23's "unfavourable news" counts mentions per 100 respondents and can exceed 100.
- **EPU:** FRED's `USEPUINDXM` is the older three-component index and is revised heavily, so the news-based file from policyuncertainty.com is used.
- **Google News RSS:** at most ~100 items per feed (65% of outlet windows hit the cap); date-bounded feeds stamp items 07:00 GMT (date only). Keep the query neutral: my first version had "layoffs" and "recession" with no positive terms and was set aside (`data/raw/_unused/`).
- **Arctic Shift:** some 2011 windows return JSON with raw control characters (parsed with `strict=False`); `query=` timed out, `title=` works. Scores were archived at different post ages in different years, so compare them only within a sub and month.
- **Loughran-McDonald dictionary:** `data/raw/lexicons/LoughranMcDonald_MasterDictionary.csv` (the file from Assignment 1, or the master dictionary from sraf.nd.edu).
- **Claude usage limits:** a limit stopped the coder subagents once. Most had written their files already; `07_ingest_codes.py resend` finds what is missing.

## Setup

```bash
cd Final_Project
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "FRED_API_KEY=your_key_here" > .env && chmod 600 .env
python scripts/01_get_econ.py
python scripts/02_collect_news.py outlets && python scripts/02_collect_news.py releases
python scripts/03_collect_reddit.py
python scripts/04_econ_baseline.py && python scripts/05_build_corpus.py
python scripts/06_make_samples.py && python scripts/06b_make_swaps.py
# AI coding and labelling steps (above), then:
python scripts/06d_human_label_tool.py        # review tool; after the review of both passes:
python scripts/06c_make_adjudication.py       # then the adjudicator subagent
python scripts/07_ingest_codes.py && python scripts/08_validation.py
python scripts/09_media_measures.py && python scripts/09b_tierc_realtime.py && python scripts/09c_tierc_checks.py
python scripts/10_analysis.py && python scripts/10b_reddit_exploratory.py && python scripts/10c_ablation.py
python scripts/10d_ratchet.py && python scripts/10f_suspects.py && python scripts/11_make_figures.py
python scripts/12_build_dashboard.py
python scripts/13_deck_data.py && node presentation/build_deck.js
python scripts/make_notebook.py && jupyter nbconvert --to notebook --execute --inplace analysis.ipynb && python scripts/make_notebook.py --strip-times
python scripts/build_report.py && python scripts/99_lint_prose.py
```

**From a fresh clone** (no text data): the committed text-free processed data (`data/processed/`), codes (`data/coded/codes.csv`, read when `codes.parquet` is absent), keys and labels let `04`, `10`, `11`, `12`, `13` and the notebook run with only a FRED key (10 reads ALFRED vintages, cached on first use). Steps `07`, `08`, `09` and `09b` need the collected text (`data/interim/`, the gold sheets and the batch files), which is not redistributed; the notebook skips them and uses the committed outputs. Re-pulled Google News feeds will not return exactly the same items, so the coded samples are tied to the original pull by `doc_id` in the `*_key.csv` files. The verbatim evidence quote behind every code is kept locally (`data/coded/codes.parquet`, the batch outputs) but not committed, because it is headline text.

## Reading the data you end up with

```python
import pandas as pd
P = pd.read_parquet("data/processed/panel_realtime_mid.parquet")   # month x U, pi, g_qoq (+ *_ref, *_pub dates), controls
gap = pd.read_parquet("data/processed/gap_main.parquet")            # actual, pred, band, gap (Model E, ICS)
news = pd.read_parquet("data/interim/news.parquet")                 # one row per kept headline: outlet, group, date, survey_month
codes = pd.read_csv("data/coded/codes.csv")                         # Opus codes per item_id (no text)
key = pd.read_csv("data/coded/sample_key.csv")                      # item_id -> doc_id, tier, outlet, group, date
M = pd.read_parquet("data/processed/media_monthly.parquet")          # TC_NEGNET (Tier C), SFFED, DICT_NEGNET, own_* (2026), ...
```

A survey month's media window is the 15th of the previous month to the 14th, so it ends at the prediction date. `*_pub` columns in the panel are the ALFRED publication dates of the values used, and the build asserts each is on or before day 14.

## Updating the dashboard

Raise `SAMPLE_END` (the last survey month; every script reads it), `DATA_CUTOFF` and `MONITOR_END` in `src/config.py` (the October preliminary in `UMICH_OCT2026_PRELIM` is used only until the final appears in `tbmics.csv`), then run `python scripts/update.py` (economic data, gap, existing codes, Tier C and dictionary series on any new headlines, dashboard) or `python scripts/update.py --with-text` to re-pull news and Reddit first. New Opus coding is the separate step above. The upcoming releases to watch are listed in `config.UPCOMING_RELEASES` and on the dashboard.

## Submitting

1. **GitHub:** the notebook with outputs saved, all code, `outputs/figures/*.png`, the results JSON files and tables, the dashboard, the presentation, `AI_USE.md`, `docs/`, `prompts/`, the label and code files without text (`data/labels/*labels*.jsonl`, `data/labels/human/human_verified_*.jsonl`, `gold_adjudicated*.jsonl`, `*_key.csv`, `gold_final.csv`, `data/coded/*.csv`), and the text-free processed data (`data/processed/`). No raw or text data (headline and post text are not ours to redistribute), no `.env`, no `PROGRESS.md`, no course files.
2. **Brightspace:** `REPORT.pdf` and the presentation, plus the repo URL.
