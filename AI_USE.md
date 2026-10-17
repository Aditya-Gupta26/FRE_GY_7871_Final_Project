# AI use disclosure

## Which AI I used

Only Claude, through Claude Code and its subagents (helper agents that Claude Code starts for a task):
- **Claude Opus 5.5** (`claude-opus-5-5`): the implementation, the headline coder and the reviews.
- **Claude Sonnet 5.5** (`claude-sonnet-5-5`) and **Claude Haiku 5.5** (`claude-haiku-5-5`): the two annotator passes for the gold set.
- **Claude Fable 5.1** (`claude-fable-5-1`): settling the gold items where the two passes disagreed.

No other AI was used anywhere: no local model, no non-Claude LLM, no other classifier model.

## What the AI did

Claude Code built the project in this repository, under my direction:
- the economic data pipeline (real-time ALFRED data, Michigan data, the checks of the course file);
- the news and Reddit collectors, the corpus and its filters;
- the codebook, the labelling guide, the prompts, the samples, the label checker and the labelling and review tool;
- the statistics (Model E and its intervals, the bias tests, the news vs sentiment tests, the forecasts, the falsifiers), the figures and the dashboard;
- the notebook, the README, the presentation and the first draft of the report;
- after the main results, at my request: the Tier C training checks (report Figure 2), the exploratory Reddit question (E3), and a rewrite of the report and presentation in plainer language, with units on every number and a takeaway line on each slide.
- later, also at my request, while I questioned how each number was built: a reworked gap accounting (only the two pieces that need no model, Michigan's web-vs-phone estimate and the party-mix check, are subtracted from the out-of-sample gap; household-cost and news effects are shown for each training window); an ablation of the postulated effects (E4, `scripts/10c_ablation.py`); an inflation-memory check (E5, `scripts/10d_ratchet.py`); the gap with the model trained to 2025 (E6, in `scripts/10_analysis.py`); a fair split of what is left among the suspects (E7, `scripts/10f_suspects.py`: out of sample, Shapley values, bootstrap ranges); a dashboard section on what explains the gap; and the deck changes I asked for (actual prices on the price chart, plain model names, a shorter falsifier slide, the Reddit slide moved to the backup, a slide for the model trained to 2025).

**How the work went:** a written plan; a check of its facts and formulas; the tests and decision rules written down before any test (`src/config.py`); then one piece at a time, with the real numbers checked before the next piece was built.

## Where AI does the measuring

The "AI-assisted framework" in the brief is Claude Opus labelling the news, checked against a gold set that other models labelled and I corrected. Every step is in the report.
- **The coder.** Opus subagents labelled 9,373 headlines and posts with one fixed prompt (`prompts/coder_v1.md`). Items were shown without date or outlet, and every label came with a word-for-word quote from the text that a script checks. 52 batches, up to 20 subagents at a time. Before the prompt was frozen, it was checked on 100 separate practice items labelled by another Opus subagent.
- **Tier C.** Opus could not label all 125,440 economic headlines within the Claude usage limits (a limit stopped the labelling once). So a simple classifier (TF-IDF + logistic regression) was trained on 8,173 Opus labels, in effect a cheap copy of the Opus coder, and it scores every economic headline for the monthly series.
- **The gold labels.** I couldn't find other people to annotate, so each of the two annotator passes is one model's labels plus my corrections.
  - Sonnet 5.5 (pass A) and Haiku 5.5 (pass B) each labelled all 450 items from the guide alone (`prompts/annotator.md`). They ran as ten separate subagents, each in its own folder with only the prompt, the guide and its 90 items, so neither pass saw the other or the coder's labels.
  - I corrected 12 items in Sonnet's pass and 15 in Haiku's, each with its reason (`data/labels/human/human_verified_{A,B}.jsonl`); every other label is the model's own.
  - On the 163 items where the corrected passes still differed, two Fable 5.1 subagents (`prompts/adjudicator.md`, one per sheet of 90 and 73 items) decided, seeing the two labels in random order without names.
  - One adjudicator run first treated single-company job news as relevant, citing a tone example in the guide. It was asked to recheck those items against the guide's relevance rule, and five changed (details in `data/labels/gold_prelabels_README.md`).
  - None of these models is Opus, so the answer key does not come from the model it grades. Because I corrected both passes after seeing the models' labels, the two passes are not independent, so the report uses the two models' agreement before my corrections as the reliability figure.
- **Checks and reviews by other agents.**
  - At the start, an Explore subagent looked through my Assignments 1 to 5 for code to reuse (the Granger module, the report builder, the prose check, the notebook builder).
  - Before building, three subagents checked the plan: data and API facts (V1); domain facts such as Michigan's switch to web interviews, the 2026 events and outlet ratings (V2); citations and formulas (V3). An independent Plan agent critiqued the design.
  - A fresh agent rebuilt the economic baseline from the raw data with its own code and reproduced every number.
  - At the end, three fresh agents checked everything (one on the brief and my decisions, one recomputing every number, one auditing the code), and after the fixes a second fresh agent checked those. Both rounds are listed below.
  - After the plain-language rewrite, a fresh review agent checked the report and deck against the saved results. It found six wrong numbers or claims and some overstatements, all fixed.
  - In the final check, a fresh agent recomputed about 300 numbers in the report and the deck from the saved results. It found one wrong value (30.5 shown as 31 after rounding twice) and several places where the wording went beyond the results or two parts described one number differently (data revisions, which model a number comes from, ranges that include zero), all fixed. Rerunning the analysis scripts then reproduced every output file exactly.

**Explainer artifact.** To prepare the talk, Claude Code made a private speaker guide (a claude.ai page, not part of the hand-in): what each slide shows, timing, a script, and likely questions with answers. It is built from the deck's notes and the saved results, and was rebuilt after each deck change.

## What I decided myself

- **Claude only.** Claude Code started setting up a local Qwen model as a cheap bulk coder. I stopped it ("just use opus for everything... no other thing than claude and opus") and the Qwen files were deleted. For the gold set I chose Sonnet and Haiku as the annotators, with my own corrections, and Fable to settle disagreements, so the answer key does not come from Opus itself.
- **No browser tools.** When I saw Chrome mentioned, I asked why: one verification subagent had tried the browser extension once (it was not connected and nothing was browsed). Every subagent prompt after that forbids browser tools.
- **Run end to end without stopping for approvals,** and pick up again after a usage-limit pause (a scheduled job did this; it is deleted at the end).
- **The repo,** and that it is pushed at the end after a scan for secrets.

- **How the gap is split.** My questions (how each piece was computed; why the news number came from a model that sees 2026) showed that the accounting mixed models. I decided that only pieces needing no model are subtracted from the out-of-sample gap, that model-based pieces are shown for each training window, that the rest is quantified with one fair rule for every suspect, and that a second slide shows the model trained to 2025. I also edited slides myself in PowerPoint; my edits were carried into the deck script.

**Decisions Claude Code took without asking (I was away), all reported back to me:** free data only, with the FRED key from my Assignment 2; monthly data from 2010, with the monitoring window from Jan 1, 2026 and the Oct 12 cutoff; headline PCE as the brief says (not the course file's core PCE); quarterly GDP growth as the main measure; the prediction date (day 14 of the month); leaving the COVID months out of gap summaries; an observational design plus an experiment proposal; the 34 outlets and three subreddits; and, after the coverage problem, the quarterly Opus series with Tier C as the monthly one.

## What the AI got wrong, and how it was caught

All of these come from the working bug log. They were caught by the checks at every step: recomputing against official sources, counting before testing, independent agents and looking at every figure.

**The most serious ones** (they would have changed the results or misled the reader):
- **The news search leaned negative.** It had "layoffs" and "recession" but no positive words (hiring, growth), so the search itself would have tilted the corpus negative. Caught by the Plan agent's critique; the pull was stopped after 357 windows and redone with a neutral search.
- **The course file's "PCE YoY" is core PCE, not headline** (equal to core in all 584 months; 0.41 pp off headline in Aug 2026). Its GDP history is an old mixed vintage, and its Q3 2026 GDP of 3.7 is the Atlanta Fed's GDPNow estimate, not a BEA number. Caught by recomputing the columns from FRED; the models use official real-time data.
- **The outlet groups were mislabelled.** The plan's "centre" group had AP, USA Today and CBS, and "business" had CNBC, all rated Lean Left by AllSides. Caught by the domain-check agent before any labelling; the groups were rebuilt from AllSides, with a recorded note.
- **The history labelling plan could never meet its own coverage rule.** The coder rates only 38% of history headlines relevant, so no month could reach 20 relevant items. Found by counting before any media test. The change (Opus history quarterly, Tier C monthly) was decided on counts only and recorded; the original measure is still tested quarterly.
- **A usage limit stopped all coder agents** for a while. Most batches had already written their files; the rest was re-prioritised, and this is recorded in the same note.
- **The H3 instability rule was written backwards** ("updating-model errors > 1.25x fixed"; it should be the reverse). Not edited: a recorded note, and the report gives the verdict both ways.
- **The independent review of the baseline found six problems,** all fixed with the headline numbers unchanged: the five component questions used the wrong 2026 months (their tables end in August); the bootstrap drew wrap-around error blocks (now only continuous ones), and a stricter AR(1) check (band ±6.3, against the bootstrap's -5.6 to +5.2) is now reported next to it; a p-value printed as 0.0; one interval used 1.96 instead of the t value written in the plan; the long-sample affordability index was defined two ways and missed a month; out-of-date code comments and NaN in the results file.
- **Numbers that went out of date.** My working summary of the release-day test, the accuracy check and the unemployment asymmetry came from a run before the last release-day items were labelled (for example "p = 0.11, 286 items"; final: p = 0.35, 433 items). Caught because the report is written only from the saved results files.
- **Overstated or wrong sentences in the report draft,** caught by checking each against the results: "every party group is 33 to 45 points below its model" (there is no party model, only levels: 30 to 49 points below 2017 to 2019); "survives every robustness gate" for the SF Fed index (only two were run on it); a no-change band written as ±5.6 (it is -5.6 to +5.2); a macro-F1 range that ignored the topic fields; one table value rounded the wrong way; "718 field checks" for the minimal pairs, when it is 654.

**Data and code bugs:**
- **FRED's keyless download hung,** so everything uses the API with a key in `.env`.
- **Gaps in ALFRED:** the quarterly GDP growth series only has versions from Sep 2014 (growth is computed from the GDP level instead; 144 of 145 months match BEA); U-6 and real income versions start in 2011 and 2010 (latest version used there, flagged). The first panel build crashed on the missing U-6 versions.
- **FRED's policy uncertainty series is the old, heavily revised index;** the news-based one is used.
- **pandas 3 dropped grouping columns** inside `groupby().apply()`, so the sample lost the release type and date for all 1,815 release-day items. Caught when the analysis hit a missing release date; fixed and checked to give the identical draw.
- **Test-retest items reused the gold ids,** so loading them would have overwritten the gold labels. Caught while writing the validation script, before any labelling.
- **Reddit self-posts came out as "title. title"** when the body repeats the title. Caught by reading the practice sheet.
- **Long-sample affordability was empty for 2026,** because it was scaled on a table that started in 2020.
- **Saved files turned lists into arrays,** which broke the topic and claim code; a formula clashed with a variable named `C`; a clustered regression had mismatched group lengths. All caught by the scripts failing.
- **Arctic Shift** returned broken JSON for some 2011 windows and timed out on one kind of search.
- **Figures:** overlapping labels, a legend on top of an axis label, counts printed over points, crowded ticks, and an axis label on the asymmetry panel that misread the good-news response. All caught by looking at each render. The first PDF printed the figures too small to read and was rebuilt.
- **The dashboard** still plotted a series that is empty before 2026 after the change of plan; rebuilt on the series the report uses.
- **A privacy slip by a subagent.** The domain-check agent (V2) put my NYU email address in a request header for one request to bls.gov, then switched to another method. It reported this itself. No other personal data was sent anywhere, and the rule now is that no subagent sends personal details to any service.

**What the final check found (three fresh agents, round 1).** All fixed, with the first-run numbers kept in the report where they changed:
- **A look-ahead in the forecasting test.** The Tier C classifier was trained once on Opus labels from every month, including 2026, and then used as a "real-time" input to the 2017 to 2026 forecasts, so later headlines shaped the reading of earlier months. It is now re-trained for every forecast month on labels published before that month's day 15. The news gain went from p = 0.037 to 0.053 (0.052 to 0.13 with last month's sentiment), and the gain beyond household costs from p = 0.31 to 0.10. The verdicts did not change, but the headline number did.
- **Three numbers computed differently from what the report and plan said.** The accuracy check used a looser rounding tolerance than the planned ±0.1 pp / ±1,000 (now the planned rule is the main one and the rounding rule a check; final numbers after round 2: 83% and 86%). CPI release-day changes used the seasonally adjusted index instead of BLS's published unadjusted 12-month change (CPI asymmetry p 0.44 became 0.15). The robustness value used the wrong t (0.087 became 0.12).
- **Two artefacts.** A decimal comparison (4.4 - 4.3 > 0.1) put most ±0.1 unemployment changes in the "large" group, so "12% vs 9% emotional wording" was really 10% vs 10%. One regression of changes subtracted across the dropped COVID months.
- **Wrong counts and wording.** The falsifier tally disagreed between sections; one falsifier (F5) was restated more softly than written in the plan; the sensitivity grid had been changed from the planned one without a note (now added); the asymmetry formula in the register had the wrong sign; RQ2's conclusion ignored that the SF Fed link survives the controls; the presentation claimed more than the spending test shows and gave three implications instead of one; a 14% that is 14 log points; a share of 15% that is 14%; a party range of 31 that is 30; framing results missing from the report; uncited references; figures numbered out of order; and third-person "Aditya" in my own report.
- **Reproducibility.** The last sample month was hard-coded in about 20 places, and a check would have failed once Michigan posts the October final, so the update script could not do what the report said; a fresh copy of the repo could not run the analysis because it read files that are not committed. Fixed with one setting, a fallback to the committed labels, and committing the text-free processed data. A session lock file would have been committed (`.claude/` is now ignored).

**What the second fresh agent found when it checked the fixes (round 2).** It confirmed the real-time Tier C rebuild (each version ends at its forecast month, the last version reproduces the full-sample series, and the economy-only forecasts are unchanged) and the other fixes, and found, all now fixed:
- **The accuracy benchmark still used the seasonally adjusted CPI** for 12-month changes, so five claims that match BLS's published (unadjusted, rounded) figure were scored as wrong. With the published CPI and core CPI changes added, 83% of claims match (inflation 65%, not 53%); 86% with the rounding rule.
- **RQ5 wording left over from the first run** still said news adds nothing beyond household costs; with real-time Tier C a similar borderline gain remains (p = 0.10; 0.047 rolling).
- **E1 and E2 were not labelled exploratory,** and the presentation recommended household-cost data for spending forecasts, which was never tested; both fixed.
- **Smaller ones:** the look-ahead described as "later headlines" instead of "after the forecast date"; an RMSE range (3.6 to 3.9, not 4.0); the changes regression still using one month next to the COVID window (dropped: Tier C +0.21, p = 0.89); the Shapley split missing from the list of full-sample Tier C uses; Newey-West, Granger and BH not cited in the text; "log points × 100" in a caption; Michigan's Table 7 clashing with the report's Table 7; dashboard text that would go out of date after an update.

**Found in the last round, while I questioned the gap accounting.** All fixed:
- **Data revisions were counted twice.** The 39.9-point gap already uses the data people saw at the time (on final data it would be 41.0), but the accounting subtracted another 1.1 points for revisions. Caught when I asked how each piece was computed.
- **The accounting mixed models.** News (about 1 point) came from a model fitted on 2010 to 2026, while the gap and "household costs about 0" came from the 2010 to 2019 model; in the 2010 to 2026 model household costs account for about 19 points. Caught by my questions; now only model-free pieces are subtracted and each training window is shown.
- **The deck file and PowerPoint got out of step twice:** once PowerPoint saved over a rebuild, and once a rebuild replaced a file I had just saved. Both times a backup copy existed and my edits were carried into the deck script; every rebuild now compares the saved file with a fresh build first.
- **Smaller ones:** a variable name reused in the analysis script (it stopped before writing anything); 10.5 shown as "about 11" on one slide; chart labels overlapping negative bars; a report cross-reference to the wrong section.

These were caught because nothing was accepted just because the code ran: the review agent reproduced the baseline exactly, the label checker rejected labels whose quote was not in the text, and every number in the report was checked against the saved results.
