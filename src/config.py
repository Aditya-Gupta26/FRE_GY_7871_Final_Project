"""Central config: paths, dates, data sources, outlets, queries, filters and sampling caps.

The pre-registration (PREREG, CODEBOOK) is appended at the bottom with its own timestamp,
written before any coding or test. All clock times are US/Eastern (ET).
Facts in comments were checked on Oct 12, 2026 (sources in REPORT.md and docs/CORPUS.md).
"""
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
LABELS = DATA / "labels"
CODED = DATA / "coded"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"
PROMPTS = ROOT / "prompts"
DASHBOARD = ROOT / "dashboard"
COURSE_XLSX = ROOT / "Perceptual_Bias_Data.xlsx"

ET = ZoneInfo("America/New_York")
RANDOM_SEED = 7871

# ---------------------------------------------------------------- sample and clocks
SAMPLE_START = "2010-01"          # first survey month in the analysis
SAMPLE_END = "2026-10"            # Oct 2026 = UMich preliminary (Oct 9); final due Oct 23
END = SAMPLE_END + "-01"          # last survey month as a date string; every script reads this (update.py: raise SAMPLE_END)
TRAIN_START, TRAIN_END = "2010-01", "2019-12"   # economic-only model fit (120 months)
OOS_FIRST_ORIGIN = "2017-01"      # first expanding-window nowcast (RQ5)
MONITOR_START = date(2026, 1, 1)  # pre-election monitoring window (text, weekly)
MONITOR_END = date(2026, 10, 11)  # last full week (Sunday); data cutoff below
DATA_CUTOFF = date(2026, 10, 12)
ELECTION_DAY = date(2026, 11, 3)
PREDICTION_DAY = 15               # the prediction date for survey month t is day 15 of t
TEXT_HISTORY_START = date(2009, 12, 15)  # media window of Jan 2010 starts Dec 15, 2009

# ---------------------------------------------------------------- FRED / ALFRED (BLS, BEA mirrors)
FRED_API = "https://api.stlouisfed.org/fred"
VINTAGE_START = "2009-01-01"      # vintages needed from here (predictions from Jan 2010)
OBS_START = "2004-01-01"          # observations needed (36-month changes, 12-month changes)
ALFRED_SERIES = {                 # series pulled with full vintage history
    "UNRATE": "U-3 unemployment rate, SA (BLS LNS14000000)",
    "U6RATE": "U-6 unemployment rate, SA (BLS)",
    "PCEPI": "PCE chain-type price index, SA (BEA)",
    "PCEPILFE": "PCE price index ex food and energy, SA (BEA)",
    "CPIAUCSL": "CPI-U all items, SA (BLS)",
    "CPILFESL": "CPI-U less food and energy, SA (BLS)",
    "PAYEMS": "Total nonfarm payrolls, SA, thousands (BLS)",
    "A191RL1Q225SBEA": "Real GDP, percent change from preceding quarter, SAAR (BEA)",
    "GDPC1": "Real GDP, chained dollars, SAAR (BEA)",
    "A229RX0": "Real disposable personal income per capita, chained dollars (BEA)",
    "TDSP": "Household debt service payments, % of disposable income (Fed Board)",
}
FRED_LATEST_SERIES = {            # latest vintage only (not revised, or vintages not needed)
    "MORTGAGE30US": "30-year fixed mortgage rate, weekly (Freddie Mac PMMS)",
    "USEPUINDXM": "Economic Policy Uncertainty index, monthly (Baker, Bloom and Davis)",
    "GASREGW": "US regular gasoline price, weekly (EIA)",
    "PCEC96": "Real personal consumption expenditures, monthly (BEA)",
    "GDPNOW": "Atlanta Fed GDPNow (for the course-file check only)",
    "UMCSENT": "Michigan sentiment on FRED (cross-check only)",
    "JTSHIL": "JOLTS hires, level, thousands (BLS): selection benchmark",
    "JTSLDL": "JOLTS layoffs and discharges, level, thousands (BLS): selection benchmark",
    "CPIAUCNS": "CPI-U all items, NSA (never revised): long real-time sample",
    "CSUSHPINSA": "S&P Cotality Case-Shiller US national home price index, NSA: affordability",
    "A229RC0": "Disposable personal income per capita, current dollars: affordability",
}
LONG_SAMPLE = ("1992-01", "2019-12")   # long real-time sample for H1 identification
LONG_VINTAGE_START = "1991-06-01"
BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_U3 = "LNS14000000"

# ---------------------------------------------------------------- University of Michigan
UMICH_FILES = "https://www.sca.isr.umich.edu/files/"
UMICH_CSV = {"ics": "tbmics.csv", "components": "tbmiccice.csv"}
UMICH_TABLES_PAGE = "https://data.sca.isr.umich.edu/tables.php"
UMICH_TABLES = {   # historical ("RB") Excel tables used
    "2n": "ICS, ICC, ICE within income terciles",
    "3n": "ICS, ICC, ICE within age groups",
    "5a": "ICS, ICC, ICE within regions",
    "5b": "ICS, ICC, ICE within political party",
    "7": "reasons for opinions about household financial situation",
    "23": "news heard of recent changes in business conditions",
    "24": "news items heard of recent changes in business conditions",
    "32": "expected change in prices during the next year",
    "36": "reasons for opinions about buying conditions for large household durables",
    "42": "reasons for opinions about house buying conditions",
}
# Oct 2026 preliminary (UMich release of Oct 9, 2026, sca.isr.umich.edu): final due Oct 23
UMICH_OCT2026_PRELIM = {"ICS": 46.3, "ICC": 44.7, "ICE": 47.3}

# ---------------------------------------------------------------- media benchmarks
SFFED_NEWS_XLSX = "https://www.frbsf.org/wp-content/uploads/news_sentiment_data.xlsx"

# ---------------------------------------------------------------- news (Google News RSS)
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
RSS_CAP = 100
# One stable, valence-neutral query over the whole sample: only the neutral names of the economy and
# its indicators. (v0 had "layoffs" and "recession" with no positive counterparts, which would have
# tilted retrieval toward negative stories; that pull was discarded, see PROGRESS.md.)
NEWS_QUERY = ('(economy OR economic OR inflation OR prices OR unemployment OR jobs OR wages '
              'OR "interest rates")')
# Release-day coverage (equivalent good vs bad releases), US-wide, no site filter
RELEASE_QUERIES = {
    "jobs": '("jobs report" OR payrolls OR "unemployment rate")',
    "cpi": '(inflation OR CPI OR "consumer prices")',
}
# Outlets: (lean group, type, Census region). Lean = AllSides media bias rating of the outlet's news
# (allsides.com, as shown in Oct 2026; collected from search snapshots because allsides.com blocks scripts):
# Lean Left / Left -> "left", Center -> "center", Lean Right / Right -> "right". Local dailies form their
# own group. The groups are sampling strata and comparison groups only, not a judgement of the outlets.
OUTLETS = {
    "nytimes.com": ("left", "general", "national"),          # Lean Left
    "washingtonpost.com": ("left", "general", "national"),   # Lean Left
    "cnn.com": ("left", "general", "national"),              # Lean Left
    "nbcnews.com": ("left", "general", "national"),          # Lean Left
    "npr.org": ("left", "general", "national"),              # Lean Left
    "apnews.com": ("left", "wire", "national"),              # Lean Left (May 2026)
    "usatoday.com": ("left", "general", "national"),         # Lean Left
    "cbsnews.com": ("left", "general", "national"),          # Lean Left
    "cnbc.com": ("left", "business", "national"),            # Lean Left (since Mar 2025)
    "reuters.com": ("center", "wire", "national"),           # Center
    "thehill.com": ("center", "general", "national"),        # Center
    "wsj.com": ("center", "business", "national"),           # Center (news)
    "marketwatch.com": ("center", "business", "national"),   # Center
    "bloomberg.com": ("center", "business", "national"),     # Center (Jun 2026)
    "foxnews.com": ("right", "general", "national"),         # Right
    "nypost.com": ("right", "general", "national"),          # Right (Jun 2026)
    "washingtonexaminer.com": ("right", "general", "national"),  # Lean Right
    "breitbart.com": ("right", "general", "national"),       # Right
    # local dailies, 4 per Census region (UMich Table 5a regions)
    "bostonglobe.com": ("local", "local", "Northeast"),
    "inquirer.com": ("local", "local", "Northeast"),
    "nj.com": ("local", "local", "Northeast"),
    "post-gazette.com": ("local", "local", "Northeast"),    # sold Apr 14, 2026; still publishing
    "chicagotribune.com": ("local", "local", "Midwest"),
    "freep.com": ("local", "local", "Midwest"),
    "startribune.com": ("local", "local", "Midwest"),
    "cleveland.com": ("local", "local", "Midwest"),
    "houstonchronicle.com": ("local", "local", "South"),
    "ajc.com": ("local", "local", "South"),                 # digital-only since Jan 1, 2026
    "tampabay.com": ("local", "local", "South"),
    "dallasnews.com": ("local", "local", "South"),
    "latimes.com": ("local", "local", "West"),
    "seattletimes.com": ("local", "local", "West"),
    "denverpost.com": ("local", "local", "West"),
    "azcentral.com": ("local", "local", "West"),
}
OUTLET_GROUPS = ["left", "center", "right", "local"]
NEWS_HISTORY_START = date(2009, 12, 1)   # monthly windows Dec 2009 .. Dec 2025
NEWS_WEEKLY_START = date(2025, 12, 29)   # weekly windows (Mondays) through the monitoring window
RSS_SLEEP_S = 1.3

# ---------------------------------------------------------------- Reddit (Arctic Shift)
REDDIT_API = "https://arctic-shift.photon-reddit.com/api"
REDDIT_SUBS = ["Economics", "economy", "personalfinance"]   # same time-stratified design for all
# r/personalfinance is mostly personal questions; its economic posts are kept by the ECON_RE filter.
REDDIT_WINDOWS_PER_MONTH = 8      # history: 8 six-hour windows per month, seeded start times
REDDIT_WINDOW_HOURS = 6
REDDIT_PER_WINDOW = 50
REDDIT_DAILY_FROM = date(2025, 12, 15)   # 2026: 4 six-hour windows a day, 25 posts each
REDDIT_DAILY_WINDOWS = 4
REDDIT_DAILY_PER_WINDOW = 25
POST_FIELDS = "id,created_utc,subreddit,author,title,selftext,score,num_comments,url"

# ---------------------------------------------------------------- filters (waterfall)
MIN_WORDS = 5
MAX_PER_AUTHOR_DAY = 5
RD_MIN_SCORE = 1                  # score 0 or less = net downvoted
BOT_MAX_POSTS_PER_DAY = 20
NEAR_DUP_JACCARD = 0.8
PROMO_RE = (r"\b(?:sponsored|advertorial|promo code|coupon|deal of the day|best deals?|"
            r"discount code|giveaway|use my code|affiliate|subscribe now|sign up for)\b")
ECON_RE = (r"\b(?:econom\w*|inflation\w*|prices?|pricing|cost of living|afford\w*|unemploy\w*|"
           r"jobs?|jobless|hiring|hire[sd]?|layoffs?|laid off|recession\w*|wages?|salar\w+|"
           r"pay(?:check|checks| raise)?|gdp|growth|cpi|pce|interest rates?|mortgage\w*|rent\w*|"
           r"grocer\w*|gas prices?|tariff\w*|fed|federal reserve|stocks?|market\w*|debt|"
           r"income\w*|spending|consumer\w*|labor|labour|payrolls?|deficit)\b")

# =====================================================================================
# PRE-REGISTRATION. Written Oct 12, 2026 at 23:58 ET (clock checked), before any model was fitted
# to sentiment, before any text was coded and before any test. Never edited afterwards; later
# notes go in PREREG_NOTES with their own time. Mirrors PLAN.md v2, section 5.
# =====================================================================================
PREREG_TIME = "2026-10-12 23:58 ET"
CODEBOOK = {"guide": "data/labels/LABELLING_GUIDE.md v1.1", "guide_sha256_16": "6d04d0977effe1a9",
            "topics": ["layoffs", "hiring", "prices_high", "inflation_up", "inflation_down", "growth",
                       "recession", "rates", "tariffs", "housing", "markets", "income", "other"],
            "narratives": {"N1_cost_of_living": "prices_high and (frame_price=level or frame_unit=household)",
                           "N2_inflation_cooling": "inflation_down",
                           "N3_jobloss_recession_fear": "(layoffs or recession) and tone=negative",
                           "N4_strong_economy": "(growth or hiring) and tone=positive"},
            "coder": "Claude Opus subagents, prompts/coder_v1.md, items without date or outlet"}
CODER_PROMPT_SHA16 = "3270f542f7bcd015"
PREREG = {
    "econ_model": "S_t = a + b_U U_t + b_pi pi_t + b_g g_t; OLS; train 2010-01..2019-12 real-time "
                  "(published by day 14 of t); U-3 SA, headline PCE YoY, GDP QoQ SAAR",
    "gap": "S_t - out-of-sample prediction, 2020-01..2026-10; targets ICS (primary), ICC, ICE, X1..X5",
    "covid_window_excluded": "2020-03..2021-01 out of every gap summary and test (GDP QoQ SAAR -31..+33)",
    "inference": "EWC HAR (nu=10, t10 critical values; Lazarus-Lewis-Stock-Watson 2018); NW L=12 check",
    "prediction_interval": "moving-block bootstrap (block 12, 2000 reps, re-estimated coefficients + "
                           "residual draw), analytic check; coverage check: train 2010-16, test 2017-19",
    "mean_gap_band": "bootstrap re-estimating coefficients + contiguous residual block of window length",
    "explained": "R2 2010-19; decomposition 2019 mean -> Jan-Oct 2026 mean; OOS RMSE 2021-02..2026-10",
    "h1_controls": ["pi36", "rdpi_yoy", "mort30", "afford", "U6_gap", "dsr"],
    "h1_long_sample": "1992-01..2019-12 real-time: U, GDP QoQ (ALFRED), CPI-U NSA pi and pi36, mort30, afford",
    "media_primary": "own Opus NEGNET (share neg - share pos) of relevant news, equal weights over 5 outlet "
                     "groups, survey-aligned window [day 15 of t-1, day 15 of t); secondary SF Fed monthly mean",
    "media_coverage_rule": ">= 20 relevant coded news items from >= 4 of 5 outlet groups, else missing",
    "coding_caps": {"history_news_per_month": 36, "history_reddit_per_month": 10, "news_2026_per_month": 120,
                    "reddit_2026_per_month": 50, "release_day_per_release": 5, "gold": 450, "dev": 100,
                    "minimal_pairs": 200, "name_swap": 200, "source_swap": 200, "test_retest": 150},
    "kill_switch": "if history coding is not done by 2026-10-14 18:00 ET, the history own-AI series is quarterly",
    "rq1_tests": ["asymmetry: NEG on max(dU3,0), max(-dU3,0), max(dpi,0), max(-dpi,0); one-sided HAC "
                  "b_up > b_down; with and without 2020-21; also for ICS (public side)",
                  "selection: inflation_up/(up+down) by sign of dpi; layoffs/(layoffs+hiring) vs JOLTS",
                  "release days: tone by released change bins; claim calibration +-0.1pp (payrolls +-1k) vs "
                  "the vintage on the publication date; definition match; emotional wording on |dU|<=0.1",
                  "attribution: president blame/credit by outlet lean x president party (descriptive DiD)"],
    "rq2_direct": "S_t on econ + H1 + media (levels, EWC), changes version, OOS-gap version 2017-2026",
    "rq2_granger": "Toda-Yamamoto both directions, p by BIC (max 6), circular shifts > 12 months, BH q=0.10 "
                   "over distinct hypotheses",
    "h2_claim_rule": "expected sign (more negative media -> lower S) AND BH q<0.10 AND permutation p<0.10 AND "
                     "survives H1 controls AND leave-one-year-out AND dropping 2021-22",
    "implied_contribution": "b x (2026 mean - 2019 mean of media), bootstrap CI; Cinelli-Hazlett RV; "
                            "equivalence bound from the 90% CI if null",
    "mde": "r* = tanh((1.96+0.84)/sqrt(N_eff-3)), N_eff = N(1-rho_x rho_y)/(1+rho_x rho_y)",
    "rq5": "models 1 econ, 1b econ+H1, 2 econ+media (NEGNET, INFL_BAL), 3 econ+H1+media; static (primary) "
           "and dynamic (+S_t-1); expanding window from 2010, first origin 2017-01; rolling 84-month check; "
           "Clark-West (HAC, one-sided) 1 vs 2 and 1b vs 3; non-nested DM with HLN; 6-variant grid "
           "(SF Fed, Reddit, dictionary, TF-IDF tier C, start-of-month info, lag-1 media) vs joint shifted null",
    "falsifiers": {"F1": "no H2 claim pass AND CW p>=0.10 for 2 vs 1 and 3 vs 1b",
                   "F2": "S -> media passes TY (q<0.10) while media -> S does not",
                   "F3": "no negativity asymmetry (b_up - b_down CI includes 0 or negative)",
                   "F4": "H1 controls close >= 50% of the 2026 mean gap in both samples (inconclusive if "
                         "jointly p>=0.10)",
                   "F5": "party sentiment shifts at an election precede shifts in own-side media tone",
                   "F6": "a mode shift as large as the gap (UMich's own comparisons)",
                   "F7": "recalled unfavourable news tracks fundamentals better (R2) than media tone"},
    "scorecard": {"H1": "supported if controls close >= 50% of 2026 mean gap in both samples and joint p<0.05; "
                        "partly if 25-50% or one sample; else not",
                  "H2": "supported if claim rule passes, CW p<0.10 and media Shapley share >= 25% of closed gap; "
                        "partly if association without OOS gain or the reverse; else not",
                  "H3": "partly if any of: UMich mode effect >= 25% of gap; real-time vs revised moves 2026 gap "
                        ">= 25%; instability (rolling coefficients change sign and expanding errors > 1.25x "
                        "fixed); supported if two or more"},
    "null_meaning": "a null means 'not detectable with ~17 years of monthly data and this measurement', "
                    "with the MDE and the equivalence bound reported, not 'media do not matter'",
}
PREREG_NOTES = [   # (time ET, note): appended, never edited
    ("2026-10-13 04:03 ET", "FIXES AFTER THE FINAL SCRUTINY (three fresh agents; recorded after seeing the results, so the report "
     "gives the first-run numbers too): (1) the Tier C classifier used in the RQ5 nowcasts was trained on Opus codes from all "
     "months; now re-trained for every origin on codes published before day 15 of t (scripts/09b), which is what the "
     "pre-registered real-time rule requires; (2) the claim-calibration code used a looser rounding-aware tolerance than the "
     "pre-registered +-0.1 pp / +-1k; the pre-registered rule is now primary and the rounding rule a sensitivity; (3) release-day "
     "changes now use the published definitions (U-3 to one decimal; CPI 12-month change from the NSA index rounded to one "
     "decimal) and the noise-band split compares rounded changes; (4) the Cinelli-Hazlett robustness value uses the OLS t; "
     "(5) the changes regression is differenced before dropping the COVID months; (6) the joint shifted null now shifts the "
     "lag-1 variant too."),
    ("2026-10-13 04:03 ET", "NOT NOTED AT THE TIME, recorded now: when 10_analysis.py was written (about 02:50 ET, after the 02:46 "
     "deviation and before any RQ5 result), the sensitivity grid was changed from the pre-registered six (SF Fed, Reddit, "
     "dictionary, Tier C, start-of-month, lag-1) because Tier C had become the main measure and the Reddit history coding had "
     "been cut (15 months with 5+ coded relevant posts): Tier C and Reddit were replaced by 'tone only' and 'news EPU'. Also the "
     "party-timing comparison uses 3-month windows (03:08 ET) because single months had 1 to 9 right-leaning items."),
    ("2026-10-13 02:46 ET", "DEVIATION, decided on item counts only (no media measure or test had been computed): (1) the "
     "Opus coder rates 38% of history headlines relevant (2,869 coded so far), so even full coding of the 36-a-month "
     "history tier would give about 13 relevant items a month and no month can meet the pre-registered >= 20 rule "
     "(0 of 192 do now). By the pre-registered kill switch the own-Opus history series is QUARTERLY (>= 20 relevant "
     "items from >= 3 groups per quarter). The monthly media measure for RQ2/RQ5 becomes the Opus-distilled TF-IDF "
     "series (Tier C, pre-registered as a robustness series; validated on gold), with the SF Fed index as the "
     "pre-registered secondary; the RQ2 direct test with own-Opus tone is also run at quarterly frequency "
     "(the original measure under its fallback rule). (2) A usage limit stopped coding at 01:18 ET with 5,503 of "
     "12,128 sample items coded (a random 45% of every tier, batches were shuffled). Remaining work is re-batched "
     "by priority: swap tests cut from 200 to 100 matched documents per version, all 2026 monitoring items, "
     "1,600 more history headlines (in the original random order) and 400 more release-day items; the rest of the "
     "history and Reddit-history tiers is not coded."),
    ("2026-10-13 00:13 ET", "Independent econ review: (a) X1..X5 tables end Aug 2026, so their windows are now the months "
     "actually observed (Jan-Aug 2026); (b) the bootstrap mean-gap null used wrap-around residual blocks, now "
     "contiguous only, with a conservative AR(1) + N(b, V_EWC) check and the analytic band reported too; "
     "(c) decomposition CIs use t_nu (as pre-registered), not 1.96. The rolling window length (60 months) "
     "is from PLAN.md v2 (23:58 ET Oct 12), not from PREREG. The Oct 2026 row's information set is 'as of the "
     "Oct 12 data pull': Sep CPI (released Oct 14) is absent, which affects only the CPI variant."),
    ("2026-10-13 00:12 ET", "Coder prompt frozen: prompts/coder_v1.md (sha256 3270f542f7bcd015...), unchanged after the dev check "
     "(100 dev items vs a separate Opus dev labeller: agreement 0.94 to 0.99, kappa 0.89 to 0.98 on every field; "
     "LLM-LLM agreement, an upper bound). No gold item had been coded or labelled."),
    ("2026-10-13 00:07 ET", "Data check V1: FRED's USEPUINDXM is the legacy three-component EPU and heavily revised "
     "(mean |revision| 5.5 points). The media/uncertainty block uses the news-based EPU from "
     "policyuncertainty.com instead (latest file, flagged). EPU is not in any pre-registered H1 test."),
    ("2026-10-13 00:03 ET", "Before any coding or media test: outlet groups changed from five (left, right, centre, "
     "business, local) to four by the AllSides rating of each outlet (left 9, center 5, right 4, local 16), "
     "because AllSides rates AP, USA Today, CBS and CNBC Lean Left (domain check V2). So the media measure "
     "weights the 4 groups equally, the coverage rule is >= 20 relevant coded items from >= 3 of the 4 groups, "
     "and the history cap of 36 a month is 9 per group. Outlet type (general, wire, business, local) is kept "
     "as a second label."),
    ("2026-10-13 00:03 ET", "H3 mode check uses UMich's own estimate (technical documentation, docid 75437): web "
     "collection lowers ICS by 6.6 points on average (ICC 13.6), phased in with the web share 0.25, 0.5, "
     "0.75 in Apr-Jun 2024 and 1 from Jul 2024. Mode-adjusted ICS = ICS + 6.6 x web share."),
    ("2026-10-13 00:01 ET", "ERROR IN THE RECORD, found after the econ baseline ran: the H3 instability rule reads "
     "'expanding errors > 1.25x fixed', which is backwards. Instability means the model re-estimated "
     "with new data fits much better than the fixed 2010-19 model, i.e. fixed RMSE > 1.25 x expanding RMSE. "
     "Noted after seeing the numbers (fixed 29.2, expanding 16.6 over 2021-02..2026-10), so the report "
     "gives the result under both the literal and the intended rule."),
    ("2026-10-13 00:01 ET", "EWC nu for samples other than the 2010-19 training sample follows the LLSW rule "
     "nu = round(0.4 T^(2/3)) (the long 1992-2019 sample: T = 336, nu = 19). Seasonality: 11 month "
     "dummies exceed nu = 10, so their joint test uses the Newey-West Wald."),
]

# ---------------------------------------------------------------- 2026 event calendar (verified Oct 13, 2026;
# sources: Federal Reserve press releases, BLS releases and lapse page, EIA weekly gasoline, Federal Register,
# Supreme Court, UMich releases and reports, CRS; full URLs in REPORT.md references and docs/CORPUS.md)
EVENTS_2026 = [
    ("2026-01-28", "Fed holds at 3.50-3.75%"),
    ("2026-01-31", "Partial shutdown to Feb 3 (jobs report delayed to Feb 11)"),
    ("2026-02-20", "Supreme Court: IEEPA does not authorise tariffs; 10% Section 122 surcharge from Feb 24"),
    ("2026-02-28", "US-Iran conflict begins; gasoline $2.94 (Feb 23) to $3.50 (Mar 9)"),
    ("2026-03-06", "Feb jobs report: -92k payrolls, unemployment 4.4%"),
    ("2026-05-11", "Gasoline peaks at $4.50"),
    ("2026-05-22", "Michigan May final 44.8 (record low); Warsh sworn in as Fed chair"),
    ("2026-06-10", "May CPI 4.2% y/y, the 2026 peak"),
    ("2026-07-24", "Section 301 tariffs (10-12.5%, 60 economies) replace the Section 122 surcharge"),
    ("2026-09-02", "Funding through Dec 11 signed (no Oct 1 shutdown)"),
    ("2026-09-16", "Fed raises 25 bp to 3.75-4.00%"),
    ("2026-10-02", "Sep jobs report: +29k payrolls, unemployment 4.2%"),
]
# Releases after the Oct 12 data cutoff (the prospective update plan)
UPCOMING_RELEASES = [
    ("2026-10-14", "BLS CPI, Sep 2026"),
    ("2026-10-23", "Michigan final Oct 2026 (interviews to Oct 19)"),
    ("2026-10-28", "FOMC decision"),
    ("2026-10-29", "BEA GDP Q3 advance; personal income and outlays (PCE), Sep"),
    ("2026-11-03", "Election day"),
    ("2026-11-06", "BLS Employment Situation, Oct; Michigan Nov preliminary (interviews Oct 20 to Nov 2, all pre-election)"),
    ("2026-11-10", "BLS CPI, Oct"),
    ("2026-11-20", "Michigan Nov final (first post-election interviews)"),
    ("2026-11-25", "BEA GDP Q3 second estimate; PCE, Oct"),
    ("2026-12-04", "BLS jobs, Nov; Michigan Dec preliminary"),
    ("2026-12-11", "Government funding expires"),
]
UMICH_MODE = {"announced": "2024-04-05", "web_share": {"2024-04": 0.25, "2024-05": 0.5, "2024-06": 0.75, "2024-07": 1.0},
              "method_effect_ICS": -6.6, "method_effect_ICC": -13.6,
              "source": "UMich technical documentation of the web transition (data.sca.isr.umich.edu docid 75437) "
                        "and the Apr 5, 2024 announcement"}
