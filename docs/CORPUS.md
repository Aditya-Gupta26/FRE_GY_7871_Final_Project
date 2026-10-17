# Corpus documentation and data provenance

This file documents the media corpus the way the brief asks (search terms, dates, source selection and inclusion criteria; unit of observation; geography and audience; duplicates, reposts, ads and bots; missing data, access limits and sampling; supply vs engagement vs exposure), plus where every economic and survey series comes from. All counts are produced by `scripts/05_build_corpus.py` and saved in `outputs/tables/corpus_*.csv|json`; the numbers below are from the final run.

## 1. News headlines (Google News RSS)

**Search terms.** One stable query for the whole sample, with only the neutral names of the economy and its indicators:
`(economy OR economic OR inflation OR prices OR unemployment OR jobs OR wages OR "interest rates")`.

I first ran a query that also had "layoffs" and "recession" without any positive counterparts (hiring, growth). Since that would tilt retrieval itself toward negative stories, I stopped it after 357 windows and set that pull aside (`data/raw/_unused/`, used nowhere). The query is applied per outlet with `site:` and date operators (`after:`, `before:`), US English edition.

**Dates and windows.**
- One window per outlet and calendar month, Dec 2009 to Dec 2025: 6,562 windows.
- One window per outlet and week (Mondays), Dec 29, 2025 to the Oct 12, 2026 cutoff: 1,394 windows.
- Release days: for every jobs report (201) and CPI release (200) from 2010 to Oct 2026, one US-wide query on the release day and the next day:
  - jobs: `("jobs report" OR payrolls OR "unemployment rate")`
  - CPI: `(inflation OR CPI OR "consumer prices")`
- 0 failed calls.
- Every file stores its query, window and retrieval time.

**Source selection.** 34 outlets: 18 national and 16 local.
- The national outlets are grouped by their AllSides media-bias rating (news, not opinion), as shown in Oct 2026:
  - **left-leaning:** NYT, Washington Post, CNN, NBC News, NPR, AP, USA Today, CBS News, CNBC
  - **center:** Reuters, The Hill, WSJ, MarketWatch, Bloomberg
  - **right-leaning:** Fox News, New York Post, Washington Examiner, Breitbart
- AllSides blocks scripted access, so the ratings were read from search-engine snapshots of allsides.com.
- The groups are sampling strata and comparison groups only, not a verdict on any outlet.
- The local outlets are four big-city dailies per Census region, matching the regions of Michigan's Table 5a:
  - **Northeast:** Boston Globe, Philadelphia Inquirer, NJ.com, Pittsburgh Post-Gazette
  - **Midwest:** Chicago Tribune, Detroit Free Press, Star Tribune, Cleveland.com
  - **South:** Houston Chronicle, Atlanta Journal-Constitution, Tampa Bay Times, Dallas Morning News
  - **West:** LA Times, Seattle Times, Denver Post, Arizona Republic (azcentral)
- The Post-Gazette was sold on Apr 14, 2026, and kept publishing.

**Unit of observation.** A headline, with its outlet and publication date. Not the article text: most of these outlets are paywalled, and redistributing article text is not allowed. Google's date-bounded feeds stamp most items 07:00 GMT, so a headline has a date but not a time.

**Inclusion criteria (filter waterfall, `outputs/tables/corpus_waterfall_news.csv`).**

| Step | Kept |
|---|---|
| Downloaded | 664,604 |
| Source is the queried outlet | 664,584 |
| Dated inside its window (±1 day for the GMT stamp) | 645,996 |
| English | 645,929 |
| Not promotional (deals, sponsored, coupons) | 645,599 |
| 4+ words | 635,714 |
| Not an exact duplicate within the outlet | 602,564 |
| Not a near duplicate within the outlet (MinHash, Jaccard ≥ 0.8) | 602,190 |
| Unique links | **602,189** |

- Of these, 132,999 (22.1%) have an economic term in the headline itself. That set is the frame the coding samples are drawn from; the query matches article text, so many headlines are about something else.
- The Claude Opus coder then decides relevance item by item, so off-topic items (single-company news, product deals, foreign-only economies, sports) are dropped before any measure is computed.

**Duplicates, reposts, ads.**
- Exact and near duplicates within an outlet are dropped.
- The same headline at several outlets (wire copy) is kept but flagged `syndicated` (1.6% of headlines), since each outlet chose to run it.
- Release-day items never displace an outlet-pull item with the same link.
- Opinion pieces ("Opinion |", "Perspective |", ...) are kept and flagged (2.0%).

**Missing data, access limits and sampling.**
- A Google News feed returns at most about 100 items. 65% of outlet windows hit that cap: 39% in 2009, 43% in 2010, rising to 88% in 2025 (`corpus_capped_share.csv`). So each window is a relevance-ranked sample of up to 100 headlines, not a census, and counts are a headline sample, never "supply volume".
- Google's index of older articles is uneven by outlet (`corpus_outlet_year_counts.csv`). In 2010, for example, the Houston Chronicle has 0 headlines, the Free Press 1, azcentral 2, Breitbart 8, USA Today 29 and AP 35, while most other outlets have 1,000+.
- The right-leaning group has few economic headlines before 2016 (45 in 2010, 94 in 2013, 135 in 2016).
- To deal with this, measures weight the four groups equally, and a period enters the own-coded series only with 20+ relevant coded items from 3+ of the 4 groups. Before 2026 no single month reaches that (the coder rates 38% of history headlines relevant), so the own-coded history series is quarterly (50 of 68 quarters covered) and the monthly series is Tier C, the TF-IDF classifier trained on the Opus codes and applied to every economic headline (re-trained each month on the codes available then for the out-of-sample tests). All 10 months of 2026 meet the rule.

**Geography and audience.**
- Local outlets carry a Census region.
- Available audience information is Pew Research Center's survey of Mar 10 to 16, 2025 (published Jun 10, 2025; 9,482 US adults): the share of adults who regularly get news from each outlet.
  - Fox 38%, NBC 35%, CNN 33%, CBS 30%, AP 21%, NPR 20%, NYT 19%, USA Today 14%, WSJ 13%, Washington Post 12%, NY Post 9%, The Hill 5%, Breitbart 3%.
  - By party, Democrats vs Republicans: CNN 48% vs 20%, Fox 18% vs 57%.
  - Pew does not cover the Washington Examiner, Reuters, CNBC, MarketWatch or Bloomberg.
- Michigan's own 2024 report on sources of economic news finds mainstream, general news and internet sources each cited by 30%+ of consumers, business news by 18%, partisan news by 15% and social media by 13%.
- None of this tells us what a Michigan respondent actually read.

## 2. Reddit posts (Arctic Shift archive)

**Subreddits.**
- r/Economics (news links, moderated)
- r/economy (news links and opinion)
- r/personalfinance (household questions; its economic posts are the household-experience voice)

**Sampling.** Time-stratified windows, the same for all three subs.
- **Dec 2009 to Dec 2025:** 8 six-hour windows per month, each starting at a seeded random time inside one eighth of the month, the first 50 posts of each window.
- **Dec 15, 2025 to Oct 11, 2026:** 4 six-hour windows a day (00, 06, 12, 18 UTC), 25 posts each.
- This avoids the clustering of "first N posts" pulls.
- 2,748 windows per sub, 156,491 posts downloaded.

**Unit of observation.** A post: its title plus the first 1,000 characters of its body; at most 600 characters are shown to the coder. Comments are not collected (scope).

**Inclusion criteria (waterfall, `corpus_waterfall_reddit.csv`).**

| Step | Kept |
|---|---|
| Downloaded | 156,491 |
| Unique | 156,318 |
| Not removed or deleted | 123,130 |
| English | 122,790 |
| An economic term in the text (a broad, two-sided list: prices, jobs, hiring, wages, growth, income, rates, ...) | 72,701 |
| Not promotional | 72,444 |
| 5+ words | 71,883 |
| Score ≥ 1 (not net downvoted) | 52,872 |
| Not a bot (AutoModerator; > 20 posts a day in the sample) | 52,856 |
| Not an exact duplicate or crosspost | 51,253 |
| Not a near duplicate | 51,142 |
| At most 5 posts per author per day | **50,926** |

That is 9,937 from r/Economics, 13,989 from r/economy and 27,000 from r/personalfinance. Of these, 21,914 are link posts (shared news) and 29,012 self-posts (the user's own words).

**Duplicates, reposts and bots.**
- Crossposts with the same title are kept once.
- Usernames are replaced by a salted SHA-256 hash at download; no username is ever written to disk. So bot accounts are found by behaviour (posting rate) and by the known hash of AutoModerator, not by their names.

**Missing data and limits.**
- r/personalfinance was small in 2010 (3 economic posts in the sample).
- Arctic Shift records the score when it archived a post, and that age differs across eras: posts from 2018 were archived about 27 days after posting, recent ones close to posting time. So scores are compared only within a sub and month, never across years.

**Supply, engagement and exposure.**
- **Supply** is what the sample shows was written: headline and post counts and shares.
- **Engagement** is Reddit's score and comment count, which are imperfect attention measures.
- **Exposure** (what Michigan respondents actually encountered) is not observed. Michigan's "news heard" questions (Tables 23 and 24) record what respondents recall hearing; they come from the same people whose sentiment we study, so they are used as recall, not as an exposure measure.

## 3. Economic and survey data (provenance)

| Series | Source | Notes |
|---|---|---|
| ICS, ICC, ICE | University of Michigan, sca.isr.umich.edu `tbmics.csv`, `tbmiccice.csv` | finals to Sep 2026; Oct 2026 preliminary (46.3 / 44.7 / 47.3, released Oct 9; final Oct 23) |
| Five index questions X1 to X5, by income, age, region, party; news heard; reasons; price expectations | Michigan historical tables (data.sca.isr.umich.edu, tables 6, 8, 28, 29, 35, 2n, 3n, 5a, 5b, 7, 23, 24, 32, 36, 42) | to Aug 2026; party monthly from Feb 2017 |
| U-3 unemployment, SA | BLS (LNS14000000, public API v2) = FRED/ALFRED UNRATE vintages | 200 months identical; Oct 2025 never collected (shutdown) |
| PCE price index (headline, core) | BEA via ALFRED vintages (PCEPI, PCEPILFE) | inflation = 100 × (P_m / P_{m-12} - 1) in the same vintage |
| Real GDP | BEA via ALFRED vintages (GDPC1; A191RL1Q225SBEA for checks) | QoQ SAAR = 100 × ((Y_q/Y_{q-1})^4 - 1); YoY = 100 × (Y_q/Y_{q-4} - 1) |
| Controls | ALFRED: U6RATE, A229RX0, TDSP; FRED: MORTGAGE30US, CSUSHPINSA, A229RC0, GASREGW, JTSHIL, JTSLDL, CPIAUCNS, PCEC96 | see `src/config.py` |
| News sentiment benchmark | SF Fed Daily News Sentiment Index (Buckman, Shapiro, Sudhof and Wilson 2020) | to Oct 4, 2026; 24 newspapers; smoothed (half-life ~13.5 days) |
| Policy uncertainty | news-based EPU (Baker, Bloom and Davis 2016), policyuncertainty.com | FRED's USEPUINDXM is the older three-component index and is heavily revised, so not used |
| Course file | `Perceptual_Bias_Data.xlsx` | U-3 and sentiment identical to official data. Its "PCE YoY" is core PCE (PCEPILFE) in all 584 months, not headline. Its GDP history up to Q2 2023 is an older mixed vintage, and its Q3 2026 value (3.7) is the Atlanta Fed GDPNow nowcast of Sep 30, 2026, not a BEA estimate (BEA's advance estimate is due Oct 29). |

**Real-time rule.**
- For survey month t, a value is used only if its ALFRED publication date is on or before day 14 of t; this is asserted in `src/realtime.py`.
- The publication dates come from ALFRED vintage dates, so the 2025 shutdown delays are handled automatically: on Oct 14 and Nov 14, 2025 the latest known unemployment rate was August's.
- Vintage coverage:
  - ALFRED's own QoQ GDP series has vintages only from Sep 2014, so QoQ is computed from GDPC1 vintages (from 2009; it matches BEA's published rate to 0.1 in 144 of 145 overlapping months, and the 145th differs by exactly 0.1).
  - U-6 vintages start Mar 2011 and real disposable income per capita May 2010. Those few early months use the latest vintage and are flagged.
