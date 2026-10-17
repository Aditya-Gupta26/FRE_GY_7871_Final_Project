# Final Project report

### AI, economic perceptions and consumer sentiment before the 2026 midterms: Jan 2010 to Oct 12, 2026

FRE-GY 7871 A · NLP and the Investment Process

**Name:** Aditya Gupta

**NetID:** ag11023

**GitHub repo:** https://github.com/Aditya-Gupta26/FRE_GY_7871_Final_Project

---

## 1. What I did

**The question.**
- Michigan consumer sentiment (ICS, index points, 1966 = 100) averaged 51.2 over Jan to Oct 2026 and hit a record low of 44.8 in May, while unemployment was only 4.1% to 4.4% and real GDP kept growing.
- The brief asks where this gap comes from: (H1) household pressures the headline numbers miss, (H2) perceptions shaped by coverage, framing or biases, or (H3) measurement, timing or an incomplete model.
- I treated all three as hypotheses and wrote down the rules for judging them before running any test (the pre-registration).

**What I built.**
- **Economy in real time:** unemployment, headline PCE inflation and GDP growth, each as published by day 14 of the survey month.
- **Media corpus:** 602,189 headlines from 34 outlets (Dec 2009 to Oct 12, 2026) and 50,926 Reddit posts.
- **AI measurement:** Claude Opus labelled 9,373 items on the brief's five dimensions, checked against 450 gold items, a word list and a simple classifier.
- **Tier C:** the Claude usage limit capped Opus at about 9,400 items, but monthly tests need all 125,440 economic headlines from the outlet pulls scored. So a simple classifier (TF-IDF + logistic regression) learned from Opus's labels and scored them all (Section 3). "Tier C" because Tiers A and B are the samples Opus labelled itself.

**Annotation disclosure.** The brief asks for two independent *human* annotators. I couldn't find other people, so the two passes are Claude Sonnet 5.5 and Claude Haiku 5.5, each labelling the 450 gold items in its own context, plus my corrections to both; Claude Fable 5.1 settled the items where they still disagreed. None of these is the Opus coder. Because I corrected both passes, I report the two models' agreement before my corrections.

**How to read the numbers.**
- **Index points:** the unit of ICS and its parts, ICC (current conditions) and ICE (expectations). **Gap:** actual ICS minus Model E's prediction for the same month, in index points; negative = gloomier than the economy predicts. "% of the gap" means a share of the 2026 average gap of -39.9 points, unless another model's gap is named.
- **Net negativity:** share of relevant headlines that are negative minus the share positive (-1 to +1). **RMSE:** typical forecast miss, in index points. **R²:** share of one series' ups and downs another explains (0 to 1).
- **p:** chance of a result this strong if nothing were going on (0.05 is the usual bar); **q:** the same, corrected for several tests. **κ, macro-F1:** labeller agreement beyond chance and a tool's accuracy averaged over classes (0 to 1, 1 = perfect).
- **Exploratory:** not in the written pre-registration, or added after the main results: a lead, not a test. **Tests:** EWC standard errors (honest when monthly errors are correlated); Toda-Yamamoto (which series moves first); Clark-West, DM-HLN (does one forecast beat another); Shapley (splits a joint effect between two groups of variables).

**Table 1. Events in the monitoring window (2026; sources in References).**

| Date | Event |
|---|---|
| Jan 31 to Feb 3 | Partial shutdown (Jan jobs report delayed to Feb 11) |
| Feb 20 | Supreme Court: IEEPA does not authorise tariffs; 10% Section 122 surcharge from Feb 24 |
| Feb 28 | US-Iran conflict begins; gasoline \$2.94 (Feb 23) to \$3.50 (Mar 9), peak \$4.50 (May 11) |
| Mar 6 | Feb jobs report: -92k payrolls, unemployment 4.4% |
| May 22 | Michigan May final 44.8, a record low; Warsh sworn in as Fed chair |
| Jun 10 | May CPI 4.2% y/y, the 2026 peak |
| Jul 24 | Section 301 tariffs (10 to 12.5%, 60 economies) replace the Section 122 surcharge |
| Sep 16 | Fed raises 25 bp to 3.75 to 4.00% (held at 3.50 to 3.75% on Jan 28) |
| Oct 2 | Sep jobs report: +29k payrolls, unemployment 4.2% |
| Oct 9 | Michigan Oct preliminary 46.3 (final Oct 23); data cutoff Oct 12 |

**Short answers.** Findings are what the data show under stated assumptions; hypotheses are explanations the data fit but cannot prove.
- **RQ1 (measuring bias).** One dimension at a time, each against its own benchmark. One clear bias: economic coverage turns more negative when inflation rises but not less negative when it falls (p = 0.002). No detectable tone asymmetry in jobs news. 83% of numbers in headlines match the official figure published that day.
- **RQ2 (impact on sentiment).** No reliable depressing effect. Even taken as causal, Tier C news tone explains about 1.0 index point of the 39.9-point 2026 gap (at most 2.4). Sentiment moves before the SF Fed news index, not after it.
- **RQ3 (what the economy explains).** Unemployment, inflation and growth explain 16% (95% CI 5% to 26%) of the 44.8-point fall in ICS from 2019 to 2026.
- **RQ4 (mechanisms).** Measurable: negativity bias (coverage and public, inflation only), anchoring on the price level, partisan switching. Partly: demand for bad news, availability. Not measurable: any reader's own bias.
- **RQ5 (forecasting).** News helps a little (typical miss 13.5 to 13.1 index points, p = 0.053); household costs help much more (to 9.2).
- **RQ6 (falsifiers).** Of seven written in advance, one holds, two partly (one only on the second media series), three do not, one cannot be settled. With how broad the gap is, they lean against media as a main cause.
- **E3 (Reddit, exploratory).** No detectable link between Reddit tone and sentiment; even taken as causal, at most about 0.4 of the 39.9 points.
- **What explains the drop.** Of the 44.8-point fall since 2019, the economy explains 7.1 (2019 already sat 2.2 below the model, so the 2026 gap is 39.9). Two pieces need no model: the web-interview switch (6.6) and the changing party mix of respondents (4.7). The other 28.6 cannot be subtracted without a model. Tested fairly, the suspects explain little of it, unless the model also learns 2021 to 2025 (Section 12).
- **Verdict.** By the rules written in advance: H1 *not supported*, H2 *partly*, H3 *partly*.

## 2. Data

- **Michigan survey.** ICS, ICC and ICE monthly, Jan 2010 to Oct 2026 (October is the preliminary reading of Oct 9). Also the five questions behind the index (X1 to X5, tables to Aug 2026), tables by income, age, region and party (party monthly from Feb 2017), the share "worse off because of higher prices" (Table 7) and news heard (Tables 23, 24).
- **Economy as published at the time.** A value enters month t only if it was published by day 14 of t (ALFRED keeps every past version of a series with its date).
  - Unemployment: U-3, seasonally adjusted; the latest figure is usually last month's. October 2025 was never collected (shutdown).
  - Inflation: headline PCE, 12-month change within one release; usually two months back.
  - GDP growth: quarter on quarter, annualised, held flat until the next quarter.
  - Revisions are small for unemployment and inflation (0.05 and 0.15 pp on average) but large for GDP growth (0.97 pp).
- **Household costs and other series.** 36-month PCE inflation, real disposable income per head (yearly growth), the 30-year mortgage rate, an affordability index (mortgage payment on the Case-Shiller price over income), U-6 minus U-3, the household debt-service ratio, gasoline prices (EIA), JOLTS hires and layoffs, the SF Fed Daily News Sentiment Index and the news-based policy uncertainty index (Baker, Bloom and Davis 2016).
- **The course data file.** Its unemployment and sentiment match the official series. But its "PCE YoY" is core PCE in all 584 months, not headline; its GDP history is an older vintage; and its Q3 2026 GDP is a GDPNow estimate. So none of its columns enter the models.
- **News.** One neutral search for the whole sample (economy, economic, inflation, prices, unemployment, jobs, wages, "interest rates") per outlet and date window: 6,562 outlet-months (to Dec 2025), 1,394 outlet-weeks (2026) and 401 release-day pulls. A first search with only negative terms ("layoffs", "recession") would tilt the sample, so I stopped it and set it aside.
- **Reddit.** The Arctic Shift archive, eight random six-hour windows per month per subreddit (r/Economics, r/economy, r/personalfinance), so the sample is not just "the first N posts". Usernames are scrambled at download.

**Cleaning.**
- **Headlines** kept if from the queried outlet, inside its window, English, not an ad, 4+ words and not a duplicate: 664,604 downloaded, 602,189 kept; 132,999 have an economic word in the headline (125,440 of them outside the release-day pulls). Wire copies and opinion pieces are flagged.
- **Reddit posts** dropped if removed, not English, without an economic word, ads, under 5 words, net-downvoted, from bots, duplicates or crossposts; at most 5 per author per day: 156,491 downloaded, 50,926 kept.

**Table 2. Corpus documentation the brief asks for.**

| Item | What I did and what it means for claims |
|---|---|
| Sources and inclusion | 34 outlets spanning lean (AllSides: left 9, center 5, right 4) and geography (16 local). Groups are sampling groups, not a verdict on any outlet. |
| Unit of observation | News: a headline with outlet and date (no article text: paywalls, licensing). Reddit: a post (title plus first 1,000 characters), no comments. |
| Audience | Pew (2025): share of adults who regularly use each outlet, e.g. Fox 38%, CNN 33%; Democrats vs Republicans: CNN 48% vs 20%, Fox 18% vs 57%. |
| Missing data, sampling | Google returns about 100 items per search and 65% of outlet windows hit that cap, so each window is a ranked sample and counts are never read as volume. Older coverage is thin for some outlets. Reddit scores were saved at different post ages, so engagement is compared only within a subreddit and month. |
| Supply vs engagement vs exposure | Supply = what was written; engagement = Reddit score; exposure (what respondents saw) is not observed. Michigan's "news heard" questions are recall, not exposure. |

**Window.** Jan 2010 to Oct 2026, with Jan 1 to Oct 11, 2026 as the monitoring window; Oct 12 is the cutoff (update plan, Section 11).

## 3. Measurement and validation

*Readings used:* Sacerdote, Sehgal and Cook (2020) for coding coverage against a benchmark; Loughran and McDonald (2011) for the dictionary; Psomakelis et al. (2014) and Carvalho and Plastino (2020) for comparing tools by macro-F1; Shapiro, Sudhof and Wilson (2022) for a monthly news index; External: Cohen (1960), Krippendorff (2004), Gwet (2008), Glasserman and Lin (2023).

![Figure 1](outputs/figures/fig1_media.png)
*Figure 1. (a) Net negativity of economic headlines in each survey window (15th of the previous month to the 14th), each the equal-weight average of four outlet groups: Tier C monthly; Opus's own labels (quarterly dots where a quarter has 20+ relevant items from 3+ groups, 50 of 68 quarters; monthly line in 2026); the word-list dictionary. (b) SF Fed news sentiment index, survey-window average, in its own units (higher = more positive). (c) Macro-F1 of each tool against the 450 gold labels. Grey: COVID window. Panel (a) follows Shapiro et al. (2022). Descriptive.*

**Codebook and benchmarks.** Written before any labelling: each dimension the brief lists gets its own fields and its own benchmark, because a bias is only a bias against something.
- **Tone:** negative, neutral or positive, plus emotional wording ("soar", "plunge"). Benchmark: the change in the number covered.
- **Selection:** 13 topics (layoffs, hiring, high prices, inflation up or down, growth, recession, ...). Benchmarks: the direction of inflation that month; official layoffs vs hires (JOLTS).
- **Framing:** price level vs inflation rate; household vs national; current vs forecast. Benchmark: other outlets and years.
- **Factual accuracy:** every number on unemployment, inflation, GDP growth or payrolls vs the official figure published by that day (±0.1 pp; payrolls ±1,000).
- **Political attribution:** who gets credit or blame, never treating criticism as bias. Benchmark: the same outlet under presidents of each party.

**The coder (Claude Opus).**
- One prompt, checked on 100 practice items and then frozen. Items shown without date or outlet, in shuffled batches; every label needs a word-for-word evidence quote.
- A checking script rejects labels outside the codebook, quotes not in the text and numbers not in the text: 9,373 of 9,381 items valid after re-sends.

**Tier C: how it was trained and how well it does.**
- **Why.** Opus's sample gives a median of 8 relevant headlines a month, too few for monthly tests, and the usage limit ruled out labelling all 125,440 economic headlines with Opus.
- **Training data.** 8,173 Opus-labelled items: history, 2026 and release-day headlines and Reddit posts. Gold items were never used.
- **Input and output.** Input: the text of one headline or post. Output: a label. Seven classifiers: relevant (yes/no) on all 8,173 items; tone (negative, neutral, positive) and five topics (inflation up, inflation down, prices high, layoffs, hiring) on the 3,811 relevant ones.
- **Method.** TF-IDF turns each text into word and word-pair weights (rare, telling words count more); logistic regression with balanced classes learns which weights go with which Opus label.
- **Scoring.** Applied to all 125,440 economic headlines: 63,043 relevant, a median of 183 a month. Each month gets net negativity, the inflation-up share and the "prices high" share, averaged over the four outlet groups.
- **How well (Figure 2).** On its own training labels it scores macro-F1 0.86 to 0.96 (low training error); on items it has not seen, 0.59 to 0.85 (5-fold cross-validation) and 0.61 to 0.88 on the gold labels. Tone is weakest (0.61 on gold; Opus 0.89). More labels help: cross-validated tone F1 rises from 0.48 with 450 labels to 0.59 with 3,811. Over time it tracks Opus's own series: quarterly net negativity correlates 0.64 in levels and 0.53 in changes (50 quarters; "prices high" 0.89), though this is not an independent check, since Tier C learned from Opus's labels. So it is usable for averages but noisy item by item, and the noise pulls links toward zero.
- **No peeking ahead.** For forecasts it is re-trained every month on labels of items published before day 15 of that month.

![Figure 2](outputs/figures/fig2_tierc.png)
*Figure 2. Tier C. (a) Macro-F1 of each classifier on the Opus labels it was trained on (fit), on Opus labels it did not see (5-fold cross-validation) and on the 450 gold labels (never trained on; "inflation down" has too few gold cases). (b) Cross-validated macro-F1 by number of training items (random subsets, 3 draws each). (c) Quarterly net negativity, Tier C vs Opus's own labels, in the 50 quarters with enough Opus items; gaps are quarters without. Added after the main results (exploratory).*

**Framing and attribution scores come from Opus only.**
- **How they are built.** Each Opus label gives an item a 0/1 score (for example, household frame = 1 if the headline is about a family's budget); a period's score is the share of relevant items, averaged over the four outlet groups. This covers emotional wording, price level vs rate, household vs national, current vs forecast, narratives, credit and blame, and number accuracy.
- **Coverage.** Quarterly for 2010 to 2025 (46 of 64 quarters have enough items), monthly and weekly in 2026.
- **Why not monthly.** The usage limit capped Opus's sample. Tier C was trained only for what the pre-registered monthly models use (tone, inflation direction, topics). A word-count classifier is also weaker on framing (household vs national 0.63, credit vs blame 0.54 on gold), attribution targets are too rare to learn (one gold item credits Republicans), and checking numbers needs exact extraction, not a classifier.
- **So** these scores are descriptive (RQ1 and the dashboard), not inputs to the monthly models.

**Gold labels.** 450 items spread across source (180 national, 120 local, 150 Reddit) and period (a third each from 2010 to 2019, 2020 to 2024, 2025 to 2026), drawn on text features only. Claude Sonnet 5.5 (pass A) and Claude Haiku 5.5 (pass B) each labelled all of them from the guide alone, in separate contexts; I corrected 12 items in A and 15 in B. Two Claude Fable 5.1 runs settled the 163 items where the corrected passes still differed, seeing both labels in random order without names: A's label on 94, B's on 55, a mix on 11, a new value on 3; one run rechecked single-company job news against the guide's relevance rule (5 changed).

**Table 3. Agreement and accuracy against the adjudicated gold labels (N = 450; macro-F1 unless stated).**

| Field | Sonnet/Haiku κ [95% CI] | Opus | Opus national / local / Reddit | Tier C | Classifier on gold | Dictionary |
|---|---|---|---|---|---|---|
| Relevant | 0.74 [0.67, 0.79] | 0.93 | 0.94 / 0.89 / 0.94 | 0.84 | 0.76 | 0.32 |
| Tone | 0.76 [0.69, 0.82] | 0.89 | 0.89 / 0.86 / 0.95 | 0.61 | 0.46 | 0.40 |
| Emotional | 0.89 [0.79, 0.97] | 0.91 | 0.91 / 0.95 / 0.90 | 0.78 | 0.58 | 0.67 |
| Price frame | 0.87 [0.80, 0.93] | 0.98 | 0.98 / 0.99 / 1.00 | 0.84 | 0.75 | 0.34 |
| Household vs aggregate | 0.57 [0.50, 0.64] | 0.84 | 0.83 / 0.86 / 0.84 | 0.63 | 0.51 | 0.40 |
| Current vs forecast | 0.72 [0.66, 0.77] | 0.89 | 0.91 / 0.81 / 0.91 | 0.71 | 0.55 | 0.31 |
| Attribution target | 0.76 [0.65, 0.85] | 0.86 | 0.97 / 0.69 / 0.92 | n/a | n/a | 0.14 |
| Credit vs blame | 0.78 [0.67, 0.87] | 0.92 | 0.96 / 0.88 / 0.84 | 0.54 | 0.44 | 0.37 |

- **By class.** Opus tone F1: 0.86 negative, 0.94 neutral, 0.88 positive. Topics: 0.88 to 0.99. Weakest: rare attribution targets.
- **The answer key.** Sonnet vs Haiku before my corrections: substantial agreement on most fields by Landis and Koch's (1977) bands, almost perfect for emotional wording and price frame, moderate for household vs aggregate.
- **Hard items.** Where the corrected passes disagreed on tone (41 items), Opus tone F1 is only 0.46: reliable on clear items, weak on genuinely unclear ones.
- **Checks that need no labels.**
  - Minimal pairs: 140 made-up items whose answer is known by construction: 654 of 654 checks right.
  - Test-retest: 150 items labelled again in other batches: κ 0.74 to 0.97 (tone 0.92).
  - Swaps on 100 matched items per version: swapping party names changes tone in 8% of items, the same as a meaningless edit (8%), but changes who gets credit or blame in 8% vs 1% (p = 0.035), a small name sensitivity. A "Source: Fox News" or "Source: CNN" tag leaves average tone unchanged.

*Why this result:* Opus reads context: a "fall" in unemployment is good news, but a word list sees "unemployment" and calls it negative. A classifier trained on 8,173 Opus labels learns more than one trained on 450, but word counts still miss direction.

**Table 4. Which tool is used where, and why.**

| Choice | Used for | Why |
|---|---|---|
| Opus coder | All tests on individual headlines; Opus quarterly and 2026 series | Best on gold, 100% on minimal pairs, stable on retest |
| Tier C | **Main monthly media series** 2010 to 2026 | Covers every month; re-trained monthly for forecasts |
| SF Fed news sentiment | **Second media series, chosen in advance** | Independent word-list index on 24 newspapers; no hindsight |
| Dictionary | Baseline; hindsight-free variant | Class reading; cannot know the future |
| Classifier on gold | Conventional baseline | The brief asks for one |

**Table 5. Formula register (each checked numerically in code or against its source).**

| Measure | Formula | Source |
|---|---|---|
| Headline PCE inflation | $100 \times \left(P_m / P_{m-12} - 1\right)$, one vintage | Brief; BEA |
| Gap | $S_t - \hat{S}_t$ (out of sample), index points | Brief |
| HAR covariance; band | EWC, $\nu = \mathrm{round}(0.4\,T^{2/3})$; moving-block bootstrap, 12-month blocks | Lazarus et al. (2018); Künsch (1989) |
| Share explained | $\Sigma_k\, b_k\, \Delta\bar{x}_k \,/\, \Delta S$, 2019 mean to 2026 mean | Decomposition |
| Net negativity | $\mathrm{NEG} = s_{\mathrm{neg}} - s_{\mathrm{pos}}$ (shares of relevant items), equal weights over 4 groups | Shapiro et al. (2022) |
| Asymmetry | $\mathrm{NEG} = a + b^{+}\max(\Delta x, 0) + b^{-}\max(-\Delta x, 0)$; test $b^{+} > -b^{-}$ | Soroka (2006) |
| Clark-West | $f = e_1^2 - \left(e_2^2 - (\hat{y}_1 - \hat{y}_2)^2\right)$, one-sided HAC $t$ | Clark and West (2007) |
| Toda-Yamamoto | VAR with $p + 1$ lags, Wald test on the first $p$ | Toda and Yamamoto (1995) |
| Robustness value | $\mathrm{RV} = \frac{1}{2}\left(\sqrt{f^4 + 4f^2} - f^2\right),\ f = t/\sqrt{df}$ | Cinelli and Hazlett (2020) |
| Implied contribution | $b \times (\bar{m}_{2026} - \bar{m}_{2019})$, $\bar{m}$ the media measure's yearly mean, index points | Pre-registered |
| Price level vs trend | $100 \times (\ln P_t - \widehat{\ln P}_t)$, $\widehat{\ln P}$ the 2010-19 linear trend | PCE price index |

**Pre-registration and changes to the plan.**
- **Written before any test:** tests, signs, the H2 claim rule, the sensitivity grid, falsifiers and scorecard. Every later change is a recorded note.
- **The one main change.** Opus rates only 38% of history headlines relevant, so no month could reach the 20 relevant items the plan required, and the usage limit also cut history labelling. So, by the fallback in the plan, Opus history became quarterly and Tier C the monthly measure.
- **Before labelling:** outlet groups re-based on AllSides ratings, Michigan's own estimate used for the survey-mode check, the news-based uncertainty index used instead of FRED's, the prompt frozen after the practice check.
- **Later:** my H3 instability rule was written the wrong way round, so both versions are reported (Table 8); the forecast sensitivity grid was changed when the code was written but recorded only later (Section 9); fixes from independent reviews (real-time Tier C, the pre-set accuracy tolerance, published release definitions). The gold set, built after the main results, feeds only the validation. The Tier C checks (Figure 2) and E3 (Section 12) were added after the main results and are exploratory.

## 4. Economic baseline and the sentiment gap

*Readings used:* Bolhuis, Cramer, Schulz and Summers (2024), the key paper for an economy-only sentiment model; Bybee et al. (2024) for using text only where it adds to economic data.

- **Model E (E for economy).** $\mathrm{ICS}_t = 117.2 - 4.87\,U_t - 2.18\,\pi_t + 0.87\,g_t$, in index points per percentage point, fitted on Jan 2010 to Dec 2019 (N = 120, R² = 0.88), each input the latest value published by day 14 of month t. Its leftover errors are stationary, so it is not two trends lining up by chance. In a dry run (fit 2010 to 2016, predict 2017 to 2019) the 95% band covered 33 of 36 months.
- **The gap.** Out of sample the model expects ICS of about 91 on average in 2026; actual ICS was 44.8 to 56.6 (average 51.2).
  - The Jan to Oct 2026 average gap is **-39.9 index points**.
  - If the 2010s relationship still held, a 10-month average gap would fall between -5.6 and +5.2 points (from the model's own resampled errors), so p < 0.0005.
  - From Feb 2021 to Oct 2026 the average gap is -27.2 points, and 93% of those 69 months lie outside the 95% band. The gap is pessimism the economy cannot explain, not proof of any bias.

![Figure 3](outputs/figures/fig3_baseline_gap.png)
*Figure 3. (a) ICS and Model E (fitted 2010 to 2019 on real-time data, dashed from 2020) with its 95% band, index points. (b) Gap = ICS minus Model E: grey in sample, orange out of sample. Grey shading: COVID window, left out (real-time GDP growth swung -33% to +33%). (c) 2026 average gap for each index and question, from its own Model E, in its own points. Panel (a) follows Bolhuis et al. (2024).*

## 5. RQ1: How can we measure bias in news coverage or social media?

*Readings used:* Sacerdote, Sehgal and Cook (2020), the key paper (coverage against a benchmark, outlet groups); Soroka (2006) and External: Gambetti, Maffei-Faccioli and Zoi (2023) for asymmetry; Harris and Sojourner (2024).

![Figure 4](outputs/figures/fig4_bias_tests.png)
*Figure 4. (a) Rise in monthly Tier C net negativity per 1 pp worsening (orange) and fall per 1 pp improvement (blue; below zero means it rose) in unemployment (3-month change) and inflation (12-month change in the 12-month rate), 90% EWC intervals; fair coverage puts both dots of a pair at the same height (N = 191 months, COVID window out). (b) Share of release-day headlines (Opus labels) that are negative, by the change in the released number. (c) Share of inflation-direction stories saying "rising", in months when published inflation fell vs rose. (d) Share of Opus-labelled news that is negative, by outlet group and president's party. (a) and (b) are tests; (c) and (d) descriptive with intervals.*

**Result.** Bias can be measured, but only one dimension at a time and against a stated benchmark. I find one clear bias (how coverage reacts to inflation), none clear in jobs or release-day coverage, mostly accurate numbers with loose definitions, and outlet differences that fit political lean (descriptive).
1. **Negativity asymmetry (benchmark: equal good and bad news).**
   - Inflation: net negativity rises 0.057 per 1 pp rise in inflation, but when inflation falls 1 pp it rises 0.045 instead of falling. Asymmetry p = 0.002 (0.019 without 2020 to 2021). The SF Fed index shows the same, more weakly (p = 0.10).
   - Unemployment: bad news moves net negativity 0.30 per pp, good news 0.10, not significantly different (p = 0.20).
2. **Selection (benchmark: what the data did).**
   - In months when published inflation fell, 33% of inflation-direction stories (26 of 78) still said it was rising; in rising months, 41% said it was falling. So which stories run is roughly balanced; the bias is in tone.
   - Layoff stories are 53% of layoff-or-hiring stories, while official layoffs are 25% of layoffs plus hires (JOLTS); the two do not move together (r = -0.11).
3. **Release days and accuracy (benchmark: the official release).**
   - Jobs days: 24% to 28% of headlines are negative when unemployment fell or held, 56% after a rise of 0.2 pp or more; no detectable asymmetry between +0.1 and -0.1 pp moves (p = 0.35). CPI days: no asymmetry (p = 0.15).
   - 83% of 161 numerical claims match the official figure published that day: unemployment 90%, payrolls 87%, inflation 65%. Only 10% say which measure they mean (CPI, PCE, core).
4. **Outlet groups and attribution (benchmark: center outlets, same month).** Right-leaning outlets are 9.7 percentage points more likely to be negative (p = 0.001) and Reddit 10.5 points (p < 0.001); left and local outlets do not differ. Split by the party in the White House, right-leaning outlets run 15.9 points darker than center outlets under Democratic presidents (p < 0.001) and 6.0 under Republican ones (p = 0.11; difference p = 0.07), and Reddit 12.0 under Republicans (p = 0.004). Blame on the president shows no partisan pattern (difference-in-differences in the share of items blaming the president: +0.03, 95% CI -0.07 to +0.07), from only three changes of president.
5. **Framing (descriptive).** Price stories stress price levels over rates in every group. Household framing rose from 9% to 19% of items a year before 2020 to 31% to 33% in 2022 to 2024. Right-leaning outlets use emotional wording most (33% of items, others 13% to 14%, Reddit 25%).

*Against Sacerdote et al. (2020):* they find stories about rising COVID cases outnumbering falling-case stories 5.3 to 1 even when cases fell. My inflation ratio in falling months is 0.5 to 1 (26 up vs 52 down): economic news does report improvement, just less than worsening, and the bias shows in tone more than in which stories run. Unlike them, I find right-leaning outlets more negative.

*Why this result:* with inflation, "good news" is ambiguous: a lower rate still means higher prices, so a cooling-inflation story is often written around prices still being high, which the coder rightly marks negative. For jobs, Gambetti et al. (2023) show apparent negativity bias can come from unemployment rising faster than it falls. Inflation numbers fail the accuracy check most because headlines mix CPI and PCE, or monthly and yearly changes: a definition problem more than a false number.

**In short.** Against fair benchmarks, economic news turns darker when inflation rises and does not brighten when it cools, while which stories run is roughly balanced. Jobs news shows no detectable tone asymmetry (though layoff stories are over-represented against official data) and most numbers are right. That is selective framing of inflation in tone, not a general negativity bias.

## 6. RQ2: How can we determine the impact of such bias on Michigan sentiment?

*Readings used:* Shapiro, Sudhof and Wilson (2022), the key paper; Souza et al. (2015) for Granger tests both ways; Doms and Morin (2004); External: Toda and Yamamoto (1995), Cinelli and Hazlett (2020), Gentzkow and Shapiro (2010). Figure 1 shows the media series used.

**Result.** With 17 years of monthly data I cannot detect a depressing effect of negative news on sentiment that passes the rule set in advance, and the most it could explain, even if fully causal, is small next to the gap. This is about what is detectable, not proof that media do not matter.
- **News vs sentiment, economy held fixed.** ICS on the economy, the six household costs and Tier C net negativity (N = 191 months).
  - Coefficient: -6.17 index points per 1.0 of net negativity (about -0.6 per 0.1), one-sided p = 0.12, q = 0.18.
  - If causal: Tier C net negativity rose 0.16 from 2019 to 2026, so it explains -1.0 index point of the -39.9-point gap (90% CI -2.4 to +0.4).
  - Without the household costs (so the news also gets credit for the pressures it reports): -14.7 per 1.0 (one-sided p = 0.061), about -2.4 points if causal (90% CI -4.9 to +0.2).
  - Fragile: a hidden factor explaining 12% of what is left of both would wipe it out (robustness value 0.12).
  - The claim rule fails: the sign and a shuffle test pass, but q, the household costs, dropping any one year and dropping 2021 to 2022 do not.
  - In month-to-month changes the sign flips (+0.21 index points per 1.0, p = 0.89).
- **SF Fed index.** +22.4 index points per index unit (q = 0.010; survives every check). But it barely moved from 2019 to 2026 (+0.03), so it explains +0.6 points, the opposite direction to the gap.
- **The original Opus measure, by quarter** (N = 47): -23.8 points per 1.0 with the economy only (p = 0.050), +0.44 once household costs enter (p = 0.96).
- **Forecast misses.** The economy-only forecast misses of 2017 to 2026 (index points) correlate -0.58 with Tier C net negativity (p = 0.003, N = 107): darker-news months are months gloomier than the economy predicts. But both trend after 2021, and with household costs the link goes away.
- **Which moves first.** Tier C to sentiment: p = 0.057 (q = 0.115); sentiment to Tier C: p = 0.67. SF Fed to sentiment: p = 0.80; **sentiment to SF Fed: p = 0.0005 (q = 0.003)**: past sentiment helps predict the index, not the reverse.
- **Demand for bad news.** Within the same subreddit and month, negative Reddit posts get 0.86 more log points of upvotes (about 2.4 times; p = 0.003, N = 616): audiences reward negativity (engagement, not exposure).
- **Party timing.** From October to December 2024, Democrats' ICS fell 21.8 points and Republicans' rose 31.8, while unemployment moved +0.1 pp and inflation +0.07 pp. Right-leaning outlets' net negativity (-1 to +1) went from 0.42 to 0.34 and left-leaning from 0.22 to 0.27 (3-month windows); 2020 cells are too small.

*Against Shapiro et al. (2022):* they find news sentiment predicts Michigan sentiment (correlation 0.58). I find the same kind of link out of sample, and their index stays significant with my controls. But over my sample sentiment moves before their index, and Tier C's link does not survive household costs.

*Why this result:* common shocks (gas prices and tariffs move both news and sentiment), reverse causation (sentiment moves first; audiences reward bad news) and noise in monthly tone (Tier C tone F1 0.61, which pulls toward zero). Household costs absorb most of the Tier C link, as expected if news mostly reports the same pressures people feel.

**How a causal answer would be obtained (the design I propose).**
- **Design.** A randomized framing experiment, written down in advance, IRB approval first, with about 4,000 consenting US adults (e.g. a probability panel such as NORC AmeriSpeak).
- **Arms**, all truthful, from the same official numbers: (1) neutral summary of the latest CPI, jobs and GDP; (2) price level ("prices are 25% higher than in 2020"); (3) rate ("inflation slowed to 3%"); (4) a typical family's budget; (5) control, no economic text.
- **Outcomes.** Michigan's five questions word for word, scored as in the index, plus inflation expectations and a recall item; party, income and news diet measured first; a two-week follow-up for fading.
- **Size.** 800 per arm detects a 3.5-index-point difference between two arms (80% power, 5% level, assumed spread 25 points). Detecting 2.4 points, the upper bound above, needs about 1,700 per arm.
- **From the sample to the national index.** Needs (a) how many people actually meet each frame, (b) weights to Michigan's mix of age, income, region and party, (c) the same effect within groups or modelled differences, (d) a one-time vignette that behaves like months of exposure, (e) no spill-over. National effect $\approx \Sigma_g\, s_g\, r_g\, \beta_g$ (share × exposure rate × effect, over groups $g$).
- Natural experiments (local paper closures; regional coverage vs regional sentiment) are possible, but local groups are thin.

**In short.** News tone and sentiment move together, but taken as causal Tier C explains about 1 of the 40 points, the SF Fed index points the wrong way, and sentiment leads that index. A proper impact estimate needs randomized framing plus exposure data.

## 7. RQ3: How much of the gap can unemployment, inflation and real GDP growth explain?

*Readings used:* Bolhuis et al. (2024), the key paper; External: Stantcheva (2024) on why people dislike inflation; Malmendier and Nagel (2016). Figure 3(c).

**Result.** About a sixth.
- **The decomposition.** From the 2019 average (96.0) to the Jan to Oct 2026 average (51.2), ICS fell 44.8 points. Unemployment rose 0.56 pp, inflation 1.82 pp and growth fell 0.51 pp, which Model E turns into a predicted fall of 7.1 points: **16% of the actual fall (95% CI 5% to 26%)**. Inflation accounts for 4.0 points, unemployment 2.7, growth 0.4.
- **The gap sits in households' own finances.** Model E explains only 6% to 8% of the fall in personal finances (X1, X2) and 14% in buying conditions for big items (X5), against 27% to 29% for business conditions (X3, X4).
- **Robust to how the economy is measured.** Yearly GDP growth, core PCE, CPI, start-of-month data, revised data and a quarterly model all give a 2026 gap of -39.7 to -41.7 points.
- **Household costs do not close it.** Added to the 2010 to 2019 model, alone or together, they leave the 2026 gap between -39.9 and -43.8 points (all six: p = 0.46). In a long sample (1992 to 2019) three of them close 6% of that model's own 2026 gap (-41.0 points), because historically high mortgage rates came with booms.
- **But the 2010s never saw 2026's housing costs** (exploratory). The mortgage payment on a typical home is 149 against income in 2026 (2019 = 100; 78 to 114 in 2010 to 2019), so the 2010s model cannot learn its effect. In the Section 6 model, fit on 2010 to 2026, the six costs account for about 19 points of the fall (90% CI 10 to 28), mostly housing (two overlapping terms), against about 1 for news; that model partly explains the years it learned from.

*Against Bolhuis et al. (2024):* their model leaves a similar gap in 2023, and an inflation measure that includes borrowing costs closes almost three quarters of it. My mortgage-rate and affordability controls do not; their result needs their cost-of-money price index, which I did not build.

*Why this result:* a linear model learns how sentiment moved with the *rate* of inflation in a decade when the price *level* never jumped. In 2026 the PCE price level was about 14% above its 2010 to 2019 trend, and falling inflation leaves that level in place: in Aug 2026, 53% of respondents said they were worse off because of higher prices, against 6% to 9% in 2019. And while GDP grew, real disposable income per head grew only -1.4% to +1.4% year on year during 2026, and the 30-year mortgage rate rose from 6.2% in January to 7.4% in October 2026 (3.9% in 2019).

**In short.** The headline numbers explain about a sixth of the fall; the rest sits in personal finances and buying conditions, which points to price levels and borrowing costs that a 2010s model cannot price.

## 8. RQ4: Which perceptual mechanisms can the data actually measure?

*Readings used:* Soroka (2006); External: D'Acunto, Malmendier, Ospina and Weber (2021); Malmendier and Nagel (2016); Carroll (2003); Mian, Sufi and Khoshkhou (2023). Apart from the public-side asymmetry test (pre-registered with RQ1), these were planned before testing but not written into the pre-registration, so they are exploratory.

![Figure 5](outputs/figures/fig5_mechanisms.png)
*Figure 5. (a) Share worse off because of higher prices (%, Michigan Table 7) against the PCE price level relative to its 2010 to 2019 trend (%, lagged two months), COVID window out. (b) Recall of bad news about high prices (Table 24) and the Tier C "prices high" share of coverage, each standardised over 2010 to 2026. (c) ICS by party (index points); dotted lines: 2016, 2020, 2024 elections. Descriptive.*

**Result.** Four mechanisms can be measured (negativity bias in coverage and in the public, price-level anchoring, partisan switching), two only partly (demand for negativity, availability), experience effects only weakly, and an individual's confirmation or availability bias not at all.

**Table 6. Mechanisms: measure, result, verdict.**

| Mechanism | Measure | Result | Verdict |
|---|---|---|---|
| Negativity bias, coverage | Asymmetry of net negativity (Figure 4a) | Inflation yes (p = 0.002); unemployment no (p = 0.20) | Measurable |
| Negativity bias, public | Same test on ICS | A 1 pp rise in inflation lowers ICS 6.2 points; a 1 pp fall changes it by -2.9 points instead of raising it (p = 0.018); unemployment p = 0.11 | Measurable (pre-registered) |
| Negativity bias, demand | Reddit upvotes; recalled news (Table 23) | Negative posts get about 2.4 times the upvotes; recalled bad news rises with inflation, does not fall back (p = 0.038) | Partly (engagement is not exposure) |
| Availability | Recall of price news (Table 24) vs coverage; gas | Correlation 0.78, but recall moves before coverage (p = 0.0001), not after (p = 0.43); gas prices add nothing to Model E (p = 0.22) | Partly |
| Anchoring on the price level | "Worse off because of prices" vs inflation rate, 36-month inflation, level vs trend | R² 0.41 (rate), 0.66 (36-month), **0.81 (level)**; worse off: 7% (2019), 40% (2022), 51% (2026) | Measurable |
| Partisan filter | Party ICS around elections with the economy flat; outlet tone | 2024: Democrats -21.8, Republicans +31.8 points in two months; outlet net negativity moved less than 0.08 (on -1 to +1) | Switching measurable; individual bias not |
| Experience effects | 2026 gap by age | 18 to 34: -38.4; 35 to 54: -45.1; 55+: -38.0 points: no age order | Weak |
| Not measurable | Which stories a respondent saw and believed | No data link news to respondents | Needs the experiment or a panel |

*Against Soroka (2006):* he finds asymmetry in UK coverage and in the public. I find the same for US inflation, on both sides, and on neither side for unemployment.

*Why this result:* the price level reaches people through every bill, so a level that stays high keeps "worse off because of prices" high even as inflation cools (partly a contrast between periods, since the level gap is near zero by construction in 2010 to 2019). Coverage behaves the other way: "prices high" coverage follows the inflation rate (R² 0.35) more than the level (0.27), so the media move on when inflation cools while households do not. And people report hearing about high prices before coverage rises, which fits experience at the till driving both.

**In short.** What the data can see (inflation negativity, level anchoring, party switching) points to prices and party more than to coverage. Whether any reader's beliefs were bent by what they read cannot be measured from text.

## 9. RQ5: Does media analysis improve predictions of consumer sentiment beyond economic indicators?

*Readings used:* Shapiro, Sudhof and Wilson (2022), the key paper; Bybee et al. (2024); Jurafsky slides on O'Connor et al. (2010); External: Clark and West (2007), Diebold and Mariano (1995), Harvey, Leybourne and Newbold (1997).

**Result.** News improves forecasts a little over the economy alone (borderline); with household costs in, a similar gain just misses the 0.10 bar except with a rolling window. Household costs improve forecasts a lot.
- **The models.** The brief's three: m1 economy only; m2 economy + Tier C news (net negativity and inflation-up share); m3 economy + news + household costs (the brief allows household or political controls; party is handled in Section 11). I add m1b, economy + household costs, to isolate the controls.
- **How.** For each month from Jan 2017 to Oct 2026 (107 months), each model is re-fitted on all earlier months and predicts that month from data published by day 14; Tier C is re-trained each month on labels available then.
- **Typical miss (RMSE, index points).** m1 13.5, m2 13.1, m1b 9.2, m3 9.0.
  - m2 vs m1: 3% smaller misses, Clark-West p = 0.053 (rolling 84-month window p = 0.028; with last month's sentiment in both, p = 0.13).
  - m3 vs m1b: 2% smaller, p = 0.10 (rolling 0.047).
  - m1b vs m1 (exploratory): 32% smaller, p = 0.001.
- **Example, March 2026 (actual 53.3).** Model E, fixed on 2010 to 2019, predicted 90.2. The updating forecasts: m1 76.2, m2 73.5, m1b 71.8, m3 70.7. News moved the forecast 2.8 points the right way, household costs 4.4; all were still 17 to 23 points too high.
- **By period.** All models do equally well in 2017 to 2019 (RMSE 3.6 to 3.9). From 2021, news cuts m1's miss from 16.6 to 16.1 and household costs to 11.1. In 2026 every model is 16 to 22 points too high on average.
- **Sensitivity.** Six variants of the news block (SF Fed, dictionary, tone only, news uncertainty, start-of-month data, news lagged a month) all beat m1 at p < 0.10. Tone only and news uncertainty replaced the planned Reddit and Tier C variants (too few labelled Reddit posts; Tier C became the main series), a change recorded only later. But news series shifted 13 to 57 months out of line (a placebo) still win 4.25 of 6 on average, so the count alone is not convincing. No news tool beats another (DM-HLN p = 0.60 and 0.90).
- **Stability.** In 60-month rolling fits the coefficients change sign two to six times; for 2021 to 2026 the updating model misses by 16.6 points, a model fixed on 2010 to 2019 by 29.2.
- **Look-ahead fix.** A first run used one Tier C classifier trained on all labels, so it had seen later headlines: m2 vs m1 p = 0.037, m3 vs m1b p = 0.31. The numbers above are the fixed, real-time ones.

*Against Shapiro et al. (2022):* their news index adds predictive power beyond the economy, and so does mine, but the gain is small (3%) and borderline, and with household costs in, which they did not test, it shrinks to 2% (p = 0.10).

*Why this result:* after 2021, news and household costs carry much of the same information (prices, rates, gas), so once household costs are in, text adds little. Tone is measured with noise, and the gap is too large and lasting for any monthly signal to close.

![Figure 6](outputs/figures/fig6_prediction.png)
*Figure 6. (a) Forecasts for each month from Jan 2017 (index points), each model re-fitted on all earlier months with data published by day 14 (COVID window skipped): m1 economy only, m2 plus real-time Tier C news, m1b plus the six household costs. (b) Running total of m1's squared misses minus the larger model's, in thousands of squared index points: rising means the larger model is winning. (c) RMSE by model and period (index points). Out-of-sample tests.*

**In short.** For forecasting Michigan sentiment, household-cost variables are worth far more than news tone; news adds a small, borderline gain over the economy alone and less once household costs are in.

## 10. RQ6: What evidence would contradict a media-bias explanation?

*Readings used:* External: Gambetti et al. (2023); Mian et al. (2023); Sacerdote et al. (2020). Figures 4 and 5.

**Result.** Seven falsifiers written before testing: one holds clearly (F7), two partly (F2, F3), three do not (F1, F4, F6), one cannot be settled (F5). F2 counts as partly only through the second media series; on Tier C, as coded, it does not hold. The three that fail rule out rival explanations or show a small news gain; none points to media as the main cause.

**Table 7. Falsifiers written in advance ("true" = evidence against media bias).**

| Falsifier | Rule | Result |
|---|---|---|
| F1 | News passes no test: claim rule fails and Clark-West p ≥ 0.10 for m2 vs m1 and m3 vs m1b | False: m2 vs m1 p = 0.053 |
| F2 | Sentiment moves before media (q < 0.10), media not before sentiment | Partly: false for Tier C (the coded test); true for the SF Fed index (q = 0.003 vs 0.80) |
| F3 | No negativity asymmetry in coverage | Partly: true for unemployment, false for inflation |
| F4 | Household costs close ≥ 50% of the 2026 gap in both samples | False: 6% of the 1992 to 2019 model's own gap; -8% in 2010 to 2019 (they widen it) |
| F5 | Party sentiment shifts before own-side media tone at an election | Cannot be settled: party swings of 22 to 32 index points vs outlet net negativity moving under 0.08, and 3-month windows cannot order them |
| F6 | The survey's switch to web interviews is as large as the gap | False: 6.6 points, 17% of the 39.9-point gap |
| F7 | Recalled bad price news fits the economy better than coverage | True: R² 0.80 (inflation) vs 0.61 (coverage) |

**Table 8. Three-explanation scorecard (rules written in advance).**

| Explanation | Rule result | Verdict |
|---|---|---|
| H1 pressures | Household costs close -8% of the 2026 gap in the 2010 to 2019 model and 6% of the 1992 to 2019 model's own gap; ≥ 50% needed in both | Not supported (by rule; the exploratory forecast result in Section 9 points the other way) |
| H2 perceptions | Claim rule fails; m2 vs m1 p = 0.053; media close none of the gap (Shapley: household costs -8.1%, media -1.5%, both widen it) | Partly |
| H3 measurement and model | Web interviews 17% of the gap; revisions none (the gap is 3% larger on final data); the 2010s model is unstable (fixed-model miss 29.2 > 1.25 × updating 16.6 points) | Partly (by the rule as first written, the wrong way round: not supported) |

- **Breadth.** Jan to Aug 2026 gaps are -37 to -42 points across income thirds, -38 to -45 across age groups and -33 to -41 across regions. Every party sits far below its 2017 to 2019 level: Democrats 78.8 to 38.1, independents 96.6 to 47.4, Republicans 120.2 to 89.7, even though Republicans hold the presidency and their outlets are no more negative under it.

*Against Gambetti et al. (2023):* like them, I find no unemployment negativity bias once uneven dynamics are allowed for; the asymmetry is specific to inflation.

*Why this result:* if negative coverage were the main driver, the fall should be biggest among readers of the most negative outlets, and coverage should move first. Instead every group fell by similar amounts, both parties fell, recall of bad price news follows the economy, and sentiment moves before the SF Fed index. What survives (inflation asymmetry, a small forecast gain) fits coverage amplifying a real price-level squeeze.

**In short.** The strongest evidence against media bias: the gap is broad, recall follows the economy more than coverage, and sentiment moves before the SF Fed news index. Media framing of inflation is real but explains little.

## 11. Monitoring the pre-election period

- **Dashboard.** One self-contained page: sentiment and Model E with its band; the gap; news tone, framing, salience and accuracy (monthly Tier C and SF Fed; 2026 Opus monthly and weekly); releases and events; source mix, missing months and validation scores. An update script refreshes the economy, the gap and the Tier C and dictionary series without any AI call.
- **Groups.** Income, age and region gaps are similar (Section 10). Party is both a moderator (Democrats' ICS 38.1 vs Republicans' 89.7, Jan to Aug 2026) and a confounder, since the Republican share of respondents fell from March 2025. But an equal-weighted average of the three party indexes fell 40 points (98.5 in Feb 2017 to 2019, 58.4 in Jan to Aug 2026) against 45 for ICS over the same months, so the changing mix explains about 5 points (4.7).
- **Survey method.** Michigan's move from phone to web interviews (Apr to Jul 2024) lowers ICS by 6.6 points on its own side-by-side comparison. Adding that back gives a 2026 gap of -33.3 points, so the switch explains 17% of the gap. Michigan also finds the May 2026 low below its June 2022 web reading, so the record is not a mode effect.
- **Election timing.** From June to October the gap moved -1.0 points on average in past midterm years and -5.3 in other years; 2026's -5.0 is ordinary, so I put no 2026 change down to the campaign.
- **Cutoff and update plan.** Data end Oct 12, 2026.
  - Before election day: September CPI (Oct 14), Michigan's October final (Oct 23), Q3 GDP and September PCE (Oct 29), October jobs and the November preliminary (Nov 6).
  - After: the November final (Nov 20, first post-election interviews), the December preliminary (Dec 4), government funding expiry (Dec 11).
  - Each release reruns the update script. A midterm does not change the White House, so a 2020- or 2024-style party flip is not expected; any November move should be compared with past midterms first.

![Figure 7](outputs/figures/fig7_monitoring.png)
*Figure 7. (a) ICS (black; hollow: October preliminary) and Model E's prediction with its 95% band, Jan 2025 to Oct 2026, index points. (b) Weekly net negativity and "prices high" share of relevant 2026 headlines (Opus labels, 11 to 32 items a week; display only), with three events. (c) Change in the gap from June to October each year, index points; orange: midterm years; light grey: 2020 (COVID window, left out of the averages). Descriptive.*

## 12. Conclusions

**What explains the drop (2026 averages, index points).** The gap is out of sample, so only pieces that need no model are subtracted; model-based pieces depend on the training years and are listed as explanations.
- **The economy:** 7.1 of the 44.8-point fall since 2019 (inflation 4.0, unemployment 2.7, growth 0.4). With 2019 already 2.2 below the model, the 2026 gap is 39.9.
- **No model needed:** the switch from phone to web interviews, 6.6 (Michigan's own estimate); the changing party mix of respondents, about 5 (Section 11). Data revisions explain none: the gap already uses real-time data (41.0 on final data).
- **Left: 28.6 points that cannot be subtracted without a model.** In the Section 6 model (in sample) news gives about 1 point and household costs about 19; out of sample both are about 0. **A fair test of the suspects** (exploratory, scripts/10f): each is added to a model that never sees 2026, its drop in the gap averaged over every order of adding them, with 90% bootstrap ranges. Trained on 1978 to 2019 (that model's own 2026 gap: 40.3), only **borrowing costs** help (5.3, 3 to 9; 1.5 on its own); the **price level** is about 0 (-1.4, -3 to 1) and **inflation memory** pulls the other way (-3.1, the 1980s relief); **partisan mood** is about 0 (at most 9.6: Republicans, in power both times, fell 30.5). So about 27 points stay unexplained. Trained on 2010 to 2025, inflation memory (5.6, 1 to 9) and the price level (5.3, -1 to 8) roughly cover the last 10.5 of that model's gap (together 11.8, -3 to 15).

1. **The gap is real and large:** ICS is 39.9 points below an economy-only model in 2026 (p < 0.0005), across six data variants.
2. **The economy explains a sixth of the fall; most of the rest is unexplained pessimism under the strict rule,** but in a model that learns 2021 to 2025, retraining absorbs 16.6 points and inflation memory and the price level about 11 more (exploratory).
3. **Economic news darkens when inflation rises and does not brighten when it falls** (p = 0.002); jobs news shows no detectable tone asymmetry and most numbers are right.
4. **No detectable depressing effect of media bias.** Taken as causal, Tier C news tone accounts for about 1 index point (at most 2.4); the claim rule fails; sentiment moves before the SF Fed index.
5. **Partisanship is a large, separate factor:** party sentiment swung 22 to 32 points after the 2024 election, economy flat (one event).
6. **For a portfolio manager:** do not read record-low Michigan sentiment as a spending signal on its own; it has not predicted real spending (E1). To forecast sentiment, put household costs in before news tone.

**Extra questions that came up (exploratory).** *Readings used:* External: Carroll, Fuhrer and Wilcox (1994); Mian et al. (2023).
- **E1. Does the gap forecast spending?** *Result:* No: sentiment and the gap do not predict real spending growth 1 or 3 months ahead beyond the economy (p = 0.25 to 0.36; modest power), as pessimism need not change what households can spend (Mian et al.).
- **E2. Do consumers recall what the media cover?** *Result:* For prices yes (correlation 0.78), for jobs much less (layoffs 0.15, hiring 0.29): price news echoes what people see at the till.
- **E3. Does Reddit tone move sentiment, the way RQ2 asks of news?** *How:* Tier C scored all 50,926 Reddit posts (15,265 relevant); monthly net negativity with subreddit fixed effects; then the RQ2 tests.
  - *Result:* No detectable link: -3.3 index points per 1.0 of Reddit net negativity with the economy only (p = 0.18), +2.1 with household costs (p = 0.72); neither series moves first. Even taken as causal, it explains +0.2 index points (90% CI -0.4 to +0.7).
  - *Caveat:* Tier C reads Reddit tone poorly (macro-F1 0.47; Opus 0.92) and the series is noisy (split-half 0.41), which pulls toward zero.
- **E5 and E6. What explains the rest of the gap?** (the fair test of the suspects is above)
  - *E5, inflation memory:* adding how far inflation has fallen from its 5-year peak to a 1978 to 2019 economy model widens the 2026 gap (40.3 to 46.9): after the 1980 peak, sentiment recovered more than inflation alone predicts.
  - *E6, trained to 2025:* the economy model still predicts 2026 out of sample but expects 74.4, a gap of 23.2, as inflation weighs three times more. Added in turn, the web switch fills 5.6, household costs 2.3 and news 0.2; with the party mix (4.7), 10.5 is left.

## 13. Limitations and ethics

- **Gold labels made by models, with my corrections.** The two passes are models' labels plus my corrections (12 and 15 items) and a third model settling disagreements. One person corrected both, so they are not independent; on items where the passes disagreed on tone, Opus tone F1 is 0.46. Two independent labellers would be the first step with more time.
- **AI hindsight.** Opus may label old headlines with hindsight (Glasserman and Lin 2023). Items were shown without dates; the dictionary and SF Fed series, which cannot have hindsight, agree in sign.
- **Headlines only, sampled.** Google's 100-item cap makes each window a ranked sample; no article text; Reddit is a narrow, self-selected audience; exposure is not observed.
- **Thin history labelling.** The usage limit and a 38% relevance rate made the Opus history series quarterly; monthly tests use Tier C, which is noisier (tone F1 0.61) and pulls toward zero. In-sample tests use one Tier C trained on all labels; forecasts use the real-time one.
- **Framing scores only quarterly.** Framing, attribution and number accuracy exist only quarterly before 2026, so are not in the monthly models.
- **Model scope.** Model E is linear and trained on a decade without price-level shocks; I did not build Bolhuis et al.'s cost-of-money index.
- **Ethics.** Public or licensed data only. No human-subject research was run (the experiment is a proposal and needs IRB approval first). Reddit usernames were scrambled at download. No headline or post text is redistributed: the repo has labels and ids, and evidence quotes stay local. One privacy slip: a verification subagent put my NYU email in one request header to bls.gov; it is disclosed in the AI-use statement.

## 14. References

<p class="refs"><b>Class readings.</b> Sacerdote, B., Sehgal, R., Cook, M. (2020). Why Is All COVID-19 News Bad News? NBER WP 28110. · Bybee, L., Kelly, B., Manela, A., Xiu, D. (2024). Business News and Business Cycles. J. Finance 79(5): 3105-3147. · Loughran, T., McDonald, B. (2011). When Is a Liability Not a Liability? J. Finance 66(1): 35-65. · Psomakelis, E. et al. (2014). Comparing Methods for Twitter Sentiment Analysis. KDIR. · Carvalho, J., Plastino, A. (2020). On the Evaluation and Combination of State-of-the-Art Features in Twitter Sentiment Analysis. Artificial Intelligence Review. · Souza, T. et al. (2015). Twitter Sentiment Analysis Applied to Finance: A Case Study in the Retail Industry. · Jurafsky, D., lecture slides on sentiment, citing O'Connor, B., Balasubramanyan, R., Routledge, B., Smith, N. (2010). From Tweets to Polls. ICWSM 4(1): 122-129.<br>
<b>External.</b> Bolhuis, M., Cramer, J., Schulz, K., Summers, L. (2024). The Cost of Money is Part of the Cost of Living. NBER WP 32163. · Shapiro, A., Sudhof, M., Wilson, D. (2022). Measuring News Sentiment. J. Econometrics 228(2): 221-243. · Buckman, S., Shapiro, A., Sudhof, M., Wilson, D. (2020). News Sentiment in the Time of COVID-19. FRBSF Economic Letter 2020-08. · Doms, M., Morin, N. (2004). Consumer Sentiment, the Economy, and the News Media. FRBSF WP 2004-09. · Soroka, S. (2006). Good News and Bad News. J. Politics 68(2): 372-385. · Gambetti, L., Maffei-Faccioli, N., Zoi, S. (2023). Bad News, Good News: Coverage and Response Asymmetries. FEDS 2023-001. · Harris, B., Sojourner, A. (2024). Why are Americans so displeased with the economy? Brookings, Jan 5. · Gentzkow, M., Shapiro, J. (2010). What Drives Media Slant? Econometrica 78(1): 35-71. · Stantcheva, S. (2024). Why Do We Dislike Inflation? BPEA Spring: 1-46. · D'Acunto, F., Malmendier, U., Ospina, J., Weber, M. (2021). Exposure to Grocery Prices and Inflation Expectations. JPE 129(5): 1615-1639. · Malmendier, U., Nagel, S. (2016). Learning from Inflation Experiences. QJE 131(1): 53-87. · Mian, A., Sufi, A., Khoshkhou, N. (2023). Partisan Bias, Economic Expectations, and Household Spending. REStat 105(3): 493-510. · Carroll, C. (2003). Macroeconomic Expectations of Households and Professional Forecasters. QJE 118(1): 269-298. · Carroll, C., Fuhrer, J., Wilcox, D. (1994). Does Consumer Sentiment Forecast Household Spending? AER 84(5): 1397-1408. · Baker, S., Bloom, N., Davis, S. (2016). Measuring Economic Policy Uncertainty. QJE 131(4): 1593-1636. · Lazarus, E., Lewis, D., Stock, J., Watson, M. (2018). HAR Inference: Recommendations for Practice. JBES 36(4): 541-559. · Newey, W., West, K. (1987). Econometrica 55(3): 703-708. · Künsch, H. (1989). Ann. Statist. 17(3): 1217-1241. · Clark, T., West, K. (2007). J. Econometrics 138(1): 291-311. · Diebold, F., Mariano, R. (1995). JBES 13(3): 253-263. · Harvey, D., Leybourne, S., Newbold, P. (1997). IJF 13(2): 281-291. · Toda, H., Yamamoto, T. (1995). J. Econometrics 66(1-2): 225-250. · Granger, C. (1969). Econometrica 37(3): 424-438. · Benjamini, Y., Hochberg, Y. (1995). JRSS-B 57(1): 289-300. · Cohen, J. (1960). Educ. Psychol. Meas. 20(1): 37-46. · Landis, J., Koch, G. (1977). Biometrics 33(1): 159-174. · Krippendorff, K. (2004). Content Analysis, 2nd ed. · Gwet, K. (2008). Br. J. Math. Stat. Psychol. 61(1): 29-48. · Cinelli, C., Hazlett, C. (2020). JRSS-B 82(1): 39-67. · Hulley, S. et al. (2013). Designing Clinical Research, 4th ed. · Glasserman, P., Lin, C. (2023). Assessing Look-Ahead Bias in Stock Return Predictions Generated by GPT Sentiment Analysis. arXiv:2309.17322.<br>
<b>Data and facts.</b> University of Michigan Surveys of Consumers (sca.isr.umich.edu; data.sca.isr.umich.edu tables; technical documentation of the web transition, docid 75437, Apr 5, 2024; "Sentiment, Web-Based Data Collection, and Partisanship", Jul 10, 2026; "Gasoline Prices and Expected Consumer Spending", Oct 9, 2026, for the Iran conflict date). · BLS (LNS14000000; Employment Situation and CPI releases; 2025 lapse release dates). · BEA (PCE, GDP; release schedule). · ALFRED and FRED, Federal Reserve Bank of St. Louis (18 series; ids listed in the repo). · SF Fed Daily News Sentiment Index. · Economic Policy Uncertainty, news-based index (policyuncertainty.com). · Atlanta Fed GDPNow. · Google News RSS. · Arctic Shift Reddit archive. · AllSides media bias ratings. · Pew Research Center (2025), The Political Gap in Americans' News Sources, Jun 10. · Events: Federal Reserve press releases (Jan 28, May 22, Sep 16, 2026); Supreme Court, Learning Resources v. Trump (Feb 20, 2026); Federal Register (Proclamation 11012; Section 301 actions, Jul 2026); EIA weekly retail gasoline; BLS Employment Situation (Mar 6, Oct 2, 2026) and CPI (Jun 10, 2026); CRS R41759 (shutdowns); White House (H.R. 6500, Sep 2, 2026). · Course data file (Perceptual Bias Data). · AI: Claude Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1 via Claude Code, Anthropic.</p>
