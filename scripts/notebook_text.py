"""Extra markdown cells for analysis.ipynb. The report sections are copied verbatim from REPORT.md by
make_notebook.py, so the notebook text and the report cannot drift apart. These cells only explain how
things are computed; they carry no result numbers (those come from the code cells)."""

MD = {}
MD["intro"] = """# Final project: AI, economic perceptions and consumer sentiment before the 2026 midterms

This notebook reproduces every table and figure in `REPORT.pdf`.
- It does not download data or call any AI model itself. The collectors (`scripts/01` to `03`), the corpus build (`05`), the samples (`06`) and the AI labelling (documented in the README) write their results to `data/`.
- The first code cell re-runs the economic baseline (`04`), the validation (`08`), the media measures (`09`), the Tier C checks (`09c`), the analysis (`10`), the exploratory Reddit question (`10b`) and the figures (`11`) on the saved data, so everything below is computed here, the same way as for the report.
- Each section starts with the report's own text (copied from `REPORT.md`), then shows the tables behind it, then a short "How this is computed" note where useful."""

MD["how_val"] = """**How the AI labels are checked.**
- **The gold set:** 450 items (180 national headlines, 120 local headlines, 150 Reddit posts; a third each from 2010 to 2019, 2020 to 2024 and 2025 to 2026), picked on text features only.
- **Who labelled it:** I couldn't find other annotators, so each of the two passes is one model's labels plus my corrections. Claude Sonnet 5.5 (pass A) and Claude Haiku 5.5 (pass B) each labelled all 450 items from the guide alone, in separate contexts; I corrected 12 items in A and 15 in B; two Claude Fable 5.1 runs settled the 163 items where the passes still differed, seeing both labels in random order without names. None of these is the Opus coder.
- **Agreement:** Cohen's kappa (plus weighted kappa and Krippendorff's alpha for tone, and Gwet's AC1 for lopsided fields). Because I corrected both passes, the reliability figure is the two models' agreement before my corrections.
- **Scoring the coder:** Opus's labels (items shown without date or outlet) are compared with the gold labels by class, by source, by period, on items where the passes agreed or disagreed, and on the 163 items with any disagreement.
- **Baselines:** the Loughran-McDonald word list with keyword rules; a TF-IDF + logistic regression classifier trained on the gold labels (5-fold cross-validation); and the same classifier trained on Opus's labels of non-gold items (Tier C).
- **Checks that need no labels:** the minimal pairs (right answers known by construction), the test-retest run and the swap tests."""

MD["how_fig1"] = """**How Figure 3 is made.**
- For each survey month t, the economy is what had been published by day 14 of t (from ALFRED): the latest unemployment rate, headline PCE inflation over 12 months, and the latest quarter's real GDP growth (annualised).
- Model E is a straight-line (OLS) fit of the index on these three, over Jan 2010 to Dec 2019.
- Panel (a): the fit and, from Jan 2020, the out-of-sample prediction with a 95% band from a block bootstrap (12-month blocks, coefficients re-estimated).
- Panel (b): the gap (index minus prediction). Grey bars are in-sample errors, orange bars out-of-sample gaps.
- The COVID months (Mar 2020 to Jan 2021) are left out on purpose: real-time GDP growth of -33% to +33% would throw a straight-line prediction off the scale.
- Panel (c): the same model for the current-conditions and expectations indexes and for each of Michigan's five questions (their tables end in Aug 2026). Descriptive, except the bands."""

MD["how_rq1"] = """**How the bias measures are computed.**
- Tests on individual headlines (selection, release days, number accuracy, attribution, outlet groups) use only headlines Opus judged relevant. The monthly Tier C series uses the relevance and tone from the classifier trained on Opus's labels.
- A survey month's news runs from the 15th of the previous month to the 14th, so it ends at the prediction date.
- A month's news measure is the plain average over four outlet groups (left-leaning, center and right-leaning national, and local) of each group's share. The weights are fixed, so nothing depends on later data. Tone = share negative minus share positive.
- **Asymmetry test:** monthly tone is regressed on the rise and the fall of unemployment (3-month change) and of inflation (12-month change in the 12-month rate), separately. The reaction to bad news is the coefficient on the rise; the reaction to good news is minus the coefficient on the fall. Negativity bias means the first is bigger (one-sided test).
- **Release days:** tone of headlines on the day of and the day after each jobs or CPI release, grouped by how much the released number changed.
- **Number accuracy:** each number in a headline is compared with the official figure published by that day."""

MD["how_rq5"] = """**How the forecasts are made.**
- On the prediction date of month t (day 14), each model is re-estimated on all earlier months and then predicts month t from that month's real-time inputs.
- Model 1: economy only. 1b: plus household costs. 2: model 1 plus news. 3: plus both.
- The Tier C news values used at month t come from a classifier re-trained only on labels published before day 15 of t (`scripts/09b`), so nothing published after the forecast date is used.
- Every model is scored over the same months. The Clark-West test asks whether the bigger model's improvement is more than chance would give (one-sided).
- The sensitivity grid swaps the news measure and the timing; its number of hits is compared with what you get after shifting all news series in time by 13 to 57 months (a placebo)."""

PLAN = [("1", []), ("2", ["data"]), ("3", ["method", ("md", "how_val")]), ("4", ["baseline", ("md", "how_fig1")]),
        ("5", ["rq1", ("md", "how_rq1")]), ("6", ["rq2"]), ("7", ["rq3"]), ("8", ["rq4"]), ("9", ["rq5", ("md", "how_rq5")]),
        ("10", ["rq6"]), ("11", ["monitor"]), ("12", ["extras"]), ("13", []), ("14", [])]
