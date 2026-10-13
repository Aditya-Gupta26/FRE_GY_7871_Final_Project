# AI use disclosure

**Tools used:** Claude (Opus 5.5, `claude-opus-5-5`), through Claude Code, including Claude Code subagents. No other AI model was used anywhere: no local model, no other LLM, no NLI or transformer classifier.

**What I used them for:** The implementation was done by Claude Code in this repository, under my direction. That covers:
- the economic data pipeline (ALFRED vintages, the real-time panel, Michigan data, the course-file checks)
- the news and Reddit collectors, the corpus build and the filter waterfalls
- the codebook, the labelling guide, the prompts, the sampling and the code validator
- the statistics (Model E and its intervals, the bias tests, the association and Granger tests, the nowcasts, the falsifiers), the figures and the dashboard
- the notebook, the README, the presentation and the first draft of REPORT.md

The process: a written plan, a verification pass on its facts and formulas, pre-registration in `src/config.py` before any test, then one piece at a time with the actual numbers checked before the next piece was built.

The "AI-assisted framework" in the brief is Claude Opus doing the measurement, and every step is disclosed in the report:
- **The coder.** Opus subagents coded 9,373 headlines and posts with one frozen prompt (`prompts/coder_v1.md`), items shown without date or outlet, each code with a verbatim evidence quote that a script checks. 52 batches with output, up to 20 subagents at a time.
- **The gold labels.** Two independent Opus subagents (annotators A and B, `prompts/annotator.md`) labelled the same 450 items from the guide alone; a third (`prompts/adjudicator.md`) settled the 55 items where they differed, seeing the two labels in random order without names. A separate Opus dev labeller labelled 100 dev items before the prompt was frozen. **These are LLM labels, not human labels**, so the agreement numbers are an upper bound. The brief asks for human annotators; I chose Opus-only (below), and the guide and sheets are there for people to relabel.
- **Tier C.** A TF-IDF classifier trained on 8,173 Opus codes, so in effect a distilled copy of the Opus coder, scores every economic headline for the monthly series.
- **Verification and review.**
  - At the start, an Explore subagent surveyed my Assignments 1 to 5 for code and conventions to reuse (the Granger module, the report builder, the prose lint, the notebook builder).
  - Before building, three subagents checked the plan: data and API facts (V1), domain facts such as Michigan's web transition, the 2026 events and outlet ratings (V2), and citations and formulas (V3). An independent Plan agent critiqued the design.
  - A fresh agent re-built the economic baseline from the raw caches with its own code and reproduced every number; its findings are listed below.
  - At the end, three fresh agents did the scrutiny check (one on the brief and my decisions, one recomputing every number, one auditing the code); after the fixes, a second fresh agent checked them. Both rounds are listed below.

No explainer artifact was used.

**What I decided myself:**
- **Claude Opus only.** Claude Code started setting up a local Qwen model as the bulk coder (to save Opus usage). I stopped it ("just use opus for everything... no other thing than claude and opus"); the Qwen weights were deleted. That decision is also why the gold labels are Opus labels and not human ones.
- **No browser tools.** When I saw Chrome mentioned, I asked why; one verification subagent had tried the browser extension once (it was not connected, nothing was browsed). Every subagent prompt after that forbids browser tools.
- **Run it end to end without stopping for approvals,** and resume after a usage-limit pause (a scheduled resume job did this, and is deleted at the end).
- **The repo,** and that it is pushed at the end after a secrets scan.

**Decisions Claude Code took without asking (I was away), all reported back to me:** free data only, with the FRED key from my Assignment 2; monthly data from 2010 with the monitoring window from Jan 1, 2026 and the Oct 12 cutoff; headline PCE as the brief says (not the course file's core PCE); QoQ GDP as the main measure; the prediction date (day 14); excluding the COVID window from gap summaries; an observational design with an experiment proposal; the 34 outlets and three subreddits; and, after the coverage problem, the quarterly own-Opus series with Tier C as the monthly one.

**Anything the model got wrong that I had to correct:** All of these are from the running bug log (`PROGRESS.md`). They were caught by the checks at every step: recomputing against official sources, counts before tests, independent agents, and looking at every figure.

The most serious ones would have changed the results or misled the reader:
- **The news query was valence-biased.** It had "layoffs" and "recession" but no positive terms (hiring, growth), so retrieval itself would have tilted the corpus negative and biased every tone result. Caught by the Plan agent's critique; the pull was stopped after 357 windows and restarted with a neutral query.
- **The course data file's "PCE YoY" is core PCE, not headline** (equal to core in all 584 months, 0.41 pp off headline in Aug 2026). Its GDP history is an old mixed vintage, and its Q3 2026 GDP of 3.7 is the Atlanta Fed GDPNow nowcast, not a BEA number. Caught by recomputing the columns from FRED; the models use official real-time data.
- **The outlet groups were mislabelled.** The plan's "centre" group had AP, USA Today and CBS, and "business" had CNBC, all rated Lean Left by AllSides. Caught by the domain-check agent before any coding; the groups were rebuilt from AllSides with a dated note.
- **The history coding design could never meet its own coverage rule.** The coder rates only 38% of history headlines relevant, so no month could reach 20 relevant items. Found when counting before any media test. The deviation (own-Opus history quarterly, Tier C as the monthly series) was decided on counts only and recorded with a timestamp; the original measure is still tested at quarterly frequency.
- **A usage limit stopped all coder agents** at 01:18 ET (resumed 02:44). Most batches had already written their files; the rest was re-prioritised and recorded in the same deviation note.
- **The H3 instability rule was pre-registered backwards** ("expanding errors > 1.25x fixed"; it should be the reverse). Not edited: a dated note, and the report gives the verdict under both versions.
- **The independent econ review found six problems,** all fixed with headline numbers unchanged: the five component questions used the wrong 2026 months (their tables end in August); the bootstrap null for the mean gap drew wrap-around residual blocks (now contiguous ones), and a conservative AR(1) check, whose band is ±6.3 against the bootstrap's -5.6 to +5.2, is now reported next to it; a p-value printed as 0.0; the decomposition interval used 1.96 instead of the pre-registered t critical value; the long-sample affordability index was defined two ways and missing a month; stale docstrings and NaN in the JSON.
- **Numbers that went stale.** My working summary of the release-day test, the calibration and the unemployment asymmetry came from a run before the last release-day items were coded (for example "p = 0.11, 286 items"; final: p = 0.35, 433 items). Caught because the report is written only from `outputs/*.json`.
- **Overstated or wrong sentences in the report draft,** caught by checking each against the outputs: "every party group is 33 to 45 points below its model" (there is no party model gap, only levels: 30 to 49 points below 2017 to 2019); "survives every robustness gate" for the SF Fed index (only two gates were run on it); a no-change band written as ±5.6 (it is -5.6 to +5.2); a macro-F1 range that ignored topic fields reaching 1.00; one table value rounded the wrong way.

Data and code bugs:
- **FRED's keyless CSV endpoint hung,** so everything uses the API with a key in `.env`.
- **ALFRED gaps:** the QoQ GDP series has vintages only from Sep 2014 (QoQ is computed from GDPC1 vintages instead; 144 of 145 months match BEA); U-6 and real income vintages start in 2011 and 2010 (latest vintage, flagged). The first panel build crashed on the missing U-6 vintages.
- **FRED's EPU series is the old three-component index** and heavily revised; the news-based EPU is used.
- **pandas 3 dropped grouping columns** inside `groupby().apply()`, so the sample key lost the release type and date for all 1,815 release-day items. Caught when the analysis hit a missing release date; fixed and verified to reproduce the identical draw.
- **Test-retest items reused the gold ids,** so the ingest step would have overwritten gold codes with retest codes. Caught while writing the validation script, before any coding.
- **Reddit self-posts came out as "title. title"** when the body repeats the title. Caught reading the dev sheet.
- **Long-sample affordability was NaN for 2026** because it was normalised on a frame that started in 2020.
- **Parquet round trips turn lists into numpy arrays,** which broke the topic and claim code; a patsy formula clashed with a variable named `C`; a clustered regression had a group-length mismatch. All caught by the scripts failing.
- **Arctic Shift** returned JSON with raw control characters for some 2011 windows and timed out on `query=`.
- **Figures:** overlapping labels, a legend on top of an axis label, counts printed over points, crowded ticks, and an axis label on the asymmetry panel that misread the good-news response. All caught by looking at each render. The first PDF printed the figures too small to read and was rebuilt.
- **The dashboard** still plotted a series that is empty before 2026 after the deviation; rebuilt on the series the report uses.
- **Record-keeping:** I wrote clock times from memory more than once (five entries before midnight stamped after midnight; the pre-registration stamped 23:59 at 23:58, fixed within the minute; seven later log entries stamped up to an hour ahead of the clock). Each was caught by running `date` and corrected. I also wrote "718 field checks" for the minimal-pair suite when it is 654.
- **A privacy slip by a subagent.** The domain-check agent (V2) put my NYU email address in a User-Agent header for one request to bls.gov, then switched to another method. It reported this itself. No other personal data was sent anywhere, and the rule now is that no subagent sends personal details to any service.

**What the final scrutiny found (three fresh agents, round 1).** All fixed, with the first-run numbers kept in the report where they changed:
- **A look-ahead in the forecasting test.** The Tier C classifier was trained once on Opus codes from every month, including 2026, and then used as a "real-time" input to the 2017 to 2026 nowcasts, so later headlines shaped the reading of earlier ones. It is now re-trained for every forecast month on codes published before that month's day 15. The media gain went from p = 0.037 to 0.053 (dynamic 0.052 to 0.13), and the gain beyond household controls from p = 0.31 to 0.10. The verdicts did not change, but the headline number did.
- **Three numbers computed differently from what the report and pre-registration said.** Claim calibration used a looser rounding tolerance than the pre-registered ±0.1 pp / ±1k (now the pre-registered rule is primary and the rounding rule a sensitivity; final numbers after round 2: 83% and 86%). CPI release-day changes used the seasonally adjusted index unrounded instead of BLS's published unadjusted 12-month change (CPI asymmetry p 0.44 became 0.15). The robustness value used the HAC t instead of the OLS t (0.087 became 0.12).
- **Two artefacts.** A float comparison (4.4 - 4.3 > 0.1) put most ±0.1 unemployment changes in the "large" group, so "12% vs 9% emotional wording" was really 10% vs 10%. The changes regression differenced across the dropped COVID months.
- **A mislabelled subset.** The "0.38 F1 on the 55 adjudicated items" was on the 11 items where the annotators disagreed on tone; on all 55 it is 0.81.
- **Wrong counts and wording.** The falsifier tally disagreed between sections; one falsifier (F5) was restated in a softer form than pre-registered; the sensitivity grid had been changed from the pre-registered one without a dated note (now added); the asymmetry formula in the register had the wrong sign; RQ2's conclusion ignored that the SF Fed link survives the controls; the presentation's implication claimed more than the spending test shows and gave three implications instead of one; a 14% that is 14 log points; a share of 15% that is 14%; party range 31 that is 30; framing results were missing from the report; uncited references; figures numbered out of order; and third-person "Aditya" in my own report.
- **Reproducibility.** The sample end month was hard-coded in about 20 places and an assert would fail once Michigan posts the October final, so `update.py` could not do what the report said; a fresh clone could not run the analysis because it read files that are not committed. Fixed with one config setting, a fallback to the committed codes, and committing the text-free processed data. A session lock file would have been committed (`.claude/` is now ignored).
- **More clock slips of my own:** two notes stamped 04:20 at 04:03 and a log entry stamped 04:40 at 04:20, each corrected when `date` was checked.

**What the second fresh agent found when it checked the fixes (round 2).** It confirmed the real-time Tier C rebuild (each vintage ends at its origin, the last vintage reproduces the full-sample series, the economy-only nowcasts are unchanged) and the other fixes, and found, all now fixed:
- **The calibration benchmark still used the seasonally adjusted CPI** for 12-month changes, so five claims that equal BLS's published (unadjusted, rounded) figure were scored as wrong. With the published CPI and core CPI changes added as benchmarks, 83% of claims match (inflation 65%, not 53%); 86% under the rounding rule.
- **RQ5 wording left over from the first run** still said news adds nothing beyond household controls; with real-time Tier C a similar borderline gain remains (p = 0.10; 0.047 rolling).
- **E1 and E2 were not labelled exploratory,** and the deck's implication recommended household-pressure data for spending forecasts, which was never tested; both fixed.
- **Smaller ones:** the look-ahead described as "later headlines" instead of "after the forecast origin"; an RMSE range (3.6 to 3.9, not 4.0); the changes regression still using one month next to the COVID window (dropped: Tier C +0.22, p = 0.89); the Shapley split missing from the list of full-sample Tier C uses; Newey-West, Granger and BH not cited in the text; "log points × 100" in a caption; Michigan's Table 7 colliding with the report's Table 7; dashboard text that would go stale after an update.

These got caught because nothing was accepted just because the code ran: the review agent reproduced the baseline to floating point, the validator rejected codes whose evidence was not in the text, and every number in the report was checked against `outputs/results*.json` and the tables.
