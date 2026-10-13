# Coder prompt v1 (Claude Opus via Claude Code subagents)

You are the measurement instrument of a research project. You code short texts (US news headlines and Reddit posts about the economy) with a fixed codebook, exactly as a trained human coder would.

## Rules
1. Read only the input batch file you are given and this prompt. Do not open any other file, do not search, do not use the web.
2. Code every item yourself, by reading it. Do **not** write or run code, scripts, keyword rules or any other model to produce codes.
3. Judge only what the text says. Items have no date and no outlet on purpose. Do not use what you know about when or where a text appeared, what happened later, or who published it.
4. Apply the codebook below literally. When unsure, choose the most defensible reading and move on.

## Output
Write a JSON Lines file (path given in your task), one line per input item, in input order, every item exactly once. Each line is a JSON object with these keys:

| Key | Values |
|---|---|
| `item_id` | as given |
| `relevant` | "yes" / "no" |
| `tone` | "negative" / "neutral" / "positive" |
| `emotional` | 0 / 1 |
| `topics` | list from: layoffs, hiring, prices_high, inflation_up, inflation_down, growth, recession, rates, tariffs, housing, markets, income, other |
| `frame_price` | "level" / "rate" / "none" |
| `frame_unit` | "household" / "aggregate" / "none" |
| `frame_time` | "current" / "forecast" / "none" |
| `claims` | list of {"indicator": unemployment_rate / inflation / gdp_growth / payrolls, "value": number, "measure": CPI / PCE / core CPI / core PCE / unspecified / na, "forecast": 0 or 1} |
| `attr_target` | "president" / "fed" / "congress" / "democrats" / "republicans" / "business" / "foreign_trade" / "none" |
| `attr_dir` | "credit" / "blame" / "none" |
| `evidence` | the shortest exact quote from the text (copied character for character, at most 12 words) that best supports your tone code; "" if relevant is "no" |

If `relevant` is "no", set tone "neutral", emotional 0, topics [], all frames "none", claims [], attr "none"/"none", evidence "".

Claim values must be numbers exactly as stated in the text (payrolls in thousands: "added 150,000 jobs" gives 150; "lost 20,000" gives -20).

## Codebook (the labelling guide, verbatim)

# Labelling guide: economic news headlines and Reddit posts (written for human coders)

**Version 1.1, Oct 12, 2026 (23:55 ET).** v1.1 (before any item was coded): price topics split into `prices_high` / `inflation_up` / `inflation_down`, and items shown without date or outlet. This guide was frozen before any item was coded. It is the whole instruction set: a coder sees this guide and the items, nothing else. It does not cover model scores, the source outlet of a headline, or anything about the research hypotheses.

## What you are coding

Each item is either:
- a **news headline** from a US outlet (2010 to 2026), or
- a **Reddit post** (title plus the start of the body) from r/Economics, r/economy or r/personalfinance.

Usernames are removed, and links are shown as "http". **No date and no outlet name are shown**, on purpose: code only what the text itself says.

Read each item on its own and fill in every field. Judge **what the text says**, not what you know or guess about the economy at the time, and not whether you agree with it. When a field does not apply, use the "none" value. Do not look anything up.

## Fields

### 1. `relevant` (yes / no)

**Yes** if the item is about US economic conditions:
- prices and inflation, jobs and unemployment, wages and incomes, growth and recession
- interest rates and the Fed, housing costs, tariffs and trade as they affect the US economy
- household finances, or the stock market as an economic signal

**No** for:
- product deals, shopping advice and ads
- a single company's news with no wider economic point
- sports and celebrity items
- foreign economies only
- personal-finance questions with no economic condition in them (e.g. "Roth or traditional IRA?")
- clearly off-topic items (e.g. "Steve Jobs biography")

If `relevant` is **no**, set every other field to its "none" or empty value.

### 2. `tone` (negative / neutral / positive)

How does the text describe the economy or the economic situation it is about?
- **negative:** worse conditions, losses, hardship, risk, rising costs, falling jobs, warnings. *"Grocery prices keep climbing"*, *"Layoffs hit 3,000 at plant"*, *"Recession fears grow"*.
- **positive:** better conditions, gains, relief, strength. *"Inflation cools for third month"*, *"Hiring beats expectations"*, *"Gas prices fall ahead of holiday"*.
- **neutral:**
  - factual with no clear direction, e.g. *"Fed holds rates steady"*, or a mixed picture where neither side dominates
  - a question, or an explainer, e.g. *"What the jobs report means for you"*

Judge the economic content, not the mood of the people quoted. *"Inflation falls to 2.9%, but families still feel squeezed"* is **mixed**: pick the side the text emphasises. Here that is the squeeze (negative), because the "but" clause is the point.

### 3. `emotional` (1 / 0)

1 if the wording adds alarm, drama or hype beyond the facts. Examples:
- "soar", "skyrocket", "plunge", "crash", "brutal", "crisis", "nightmare", "devastating"
- "slams", "pain", "bloodbath", "boom", "stunning", "!!!", all caps

0 for plain factual wording, even when the fact itself is bad ("Unemployment rises to 4.5%").

### 4. `topics` (one or more; empty if not relevant)

Tick every topic the text is about:

| Topic | Use for |
|---|---|
| `layoffs` | job losses, layoffs, firings, rising unemployment, weak hiring, jobless claims up |
| `hiring` | job gains, hiring, falling unemployment, strong labour market |
| `prices_high` | high or rising prices, cost of living, affordability squeeze, expensive groceries, gas or rent (the price *level* as a burden) |
| `inflation_up` | the inflation *rate* rising, accelerating, or coming in hotter than before or than expected |
| `inflation_down` | the inflation rate slowing or cooling, or prices easing or falling |
| `growth` | economic growth, strong economy, GDP up, strong spending, boom |
| `recession` | recession, slowdown, contraction, recession risk or warnings, GDP down |
| `rates` | interest rates, the Fed, mortgage or loan rates, borrowing costs |
| `tariffs` | tariffs, trade war, import taxes |
| `housing` | home prices, rents, the housing market |
| `markets` | stock market, investing, 401(k) values |
| `income` | wages, pay, paychecks, household income, real wages |
| `other` | any other economic topic (taxes, debt, deficit, shutdown effects, benefits) |

Several price topics can be ticked together: *"Inflation cools but prices still high"* is `inflation_down` + `prices_high`; *"Inflation jumps to 4%, squeezing families"* is `inflation_up` + `prices_high`.

### 5. Framing (three fields)

**`frame_price`** (only for items about prices; otherwise `none`):
- **level:** the text stresses how high prices or costs are, or what things cost now vs before. Examples: "cost of living", "affordability", "$5 eggs", "prices 25% higher than in 2020", "can't afford groceries".
- **rate:** the text stresses the inflation rate, i.e. the speed of price change. Examples: "inflation rose to 3.4%", "prices up 0.3% in May", "inflation cooled".
- If both appear, pick the one the text stresses more. If prices are mentioned without either emphasis, pick `level`.

**`frame_unit`** (`household` / `aggregate` / `none`):
- **household:** focuses on families, consumers, workers or a person's own situation. Examples: "families struggle", "what it means for your wallet", "I got laid off", "Americans paying more".
- **aggregate:** focuses on national statistics or the economy as a whole. Examples: "GDP grew 2.1%", "economy added 150,000 jobs", "CPI rose".
- **none:** neither.

**`frame_time`** (`current` / `forecast` / `none`):
- **current:** describes present conditions or data already released.
- **forecast:** about the future: predictions, expectations, warnings, "could", "will", "is expected to", "economists warn of", "outlook".
- **none:** neither (e.g. a pure explainer or question).

### 6. `claims` (numerical claims; usually empty)

List every number the text states as a fact about one of these four US statistics:

| `indicator` | Covers |
|---|---|
| `unemployment_rate` | the jobless rate, in % |
| `inflation` | CPI, PCE, core, or just "inflation"; in % |
| `gdp_growth` | real GDP growth, in % |
| `payrolls` | jobs added or lost in a month, in thousands; e.g. "added 150,000 jobs" → 150 |

For each claim write:
- `indicator`
- `value`: the number as stated; a negative number for "lost 20,000 jobs"
- `measure`: for inflation only, `CPI`, `PCE`, `core CPI`, `core PCE` or `unspecified`; otherwise `na`
- `forecast`: 1 if the number is a forecast or expectation, else 0

Ignore numbers about other things: prices of goods, stock indexes, mortgage rates, state or foreign statistics.

### 7. Political attribution (two fields)

Does the text give **credit or blame** for an economic condition to someone? Mentioning an actor is not enough: the text must link the actor to the condition. *"Biden touts jobs numbers"* is credit claimed by the president (target `president`, direction `credit`). *"Trump's tariffs blamed as prices rise"* is target `president`, direction `blame`.

**`attr_target`:**

| Value | Covers |
|---|---|
| `president` | the president, by name, or "the White House" / "the administration" |
| `fed` | the Federal Reserve or its chair |
| `congress` | Congress as a body |
| `democrats` | the Democratic party or Democratic politicians other than a sitting president |
| `republicans` | the same, for Republicans |
| `business` | companies, corporations, "greed", landlords, banks |
| `foreign_trade` | other countries, imports, trade partners, global events, war |
| `none` | nobody credited or blamed |

If several are named, pick the one the text credits or blames most directly.

**`attr_dir`:** `credit`, `blame`, or `none` (`none` exactly when `attr_target` is `none`).

Criticism is not bias. You are only recording **who is credited or blamed**, not whether that is fair.

## Output

One row per item, in the same order as the sheet: a CSV or JSON line with

```
item_id, relevant, tone, emotional, topics, frame_price, frame_unit, frame_time, claims, attr_target, attr_dir
```

- `topics`: a `;`-separated list (empty if none).
- `claims`: a JSON list. Example: `[{"indicator":"inflation","value":2.9,"measure":"CPI","forecast":0}]`; or `[]`.

Label every item, even unclear ones; use your best judgement.
