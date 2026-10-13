// Builds presentation/Final_Project_Presentation.pptx from presentation/deck_data.json
// (written by scripts/13_deck_data.py from the saved outputs). Native charts, speaker notes.
//   python scripts/13_deck_data.py && node presentation/build_deck.js
// Needs pptxgenjs (npm install pptxgenjs) and, for the theme colours, the pptx skill's apply_theme.js
// (path in APPLY_THEME, optional: without it the deck keeps Office's default palette).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));
const OUT = path.join(__dirname, "Final_Project_Presentation.pptx");
const THEME = {
  name: "Sentiment Gap",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2333", lt1: "FFFFFF", dk2: "3A4659", lt2: "EEF1F5",
    accent1: "D9822B", accent2: "2A7F86", accent3: "C2453A", accent4: "7A8699",
    accent5: "3F6FB5", accent6: "8C6BB1", hlink: "2A7F86", folHlink: "7A8699",
  },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Record-low sentiment is not, by itself, a spending signal";
pres.author = "Aditya Gupta";
const C = pres.SchemeColor;

// ---------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontSize: 44, bold: true,
      color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.6, fontSize: 20,
      color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontSize: 30, bold: true,
      color: C.text1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "FRE-GY 7871 Final Project · Aditya Gupta · data to Oct 12, 2026",
      options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.text2, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.text2 },
});

const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
  dataLabelFontSize: 12, legendFontSize: 12, catAxisLabelColor: HEX.dk2, valAxisLabelColor: HEX.dk2,
  valGridLine: { color: "DDE2E8", size: 0.75 }, catGridLine: { style: "none" } };

function stat(slide, x, y, w, big, label, color, name) {
  slide.addText(big, { x, y, w, h: 0.95, fontSize: 48, bold: true, color, fontFace: THEME.headFontFace, margin: 0,
    isTextBox: true, objectName: name + "_value" });
  slide.addText(label, { x, y: y + 0.95, w, h: 0.75, fontSize: 14, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: name + "_label" });
}
function circleLabel(slide, x, y, txt, fill, name) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.85, h: 0.85, fill: { color: fill }, line: { color: fill }, objectName: name + "_circle" });
  slide.addText(txt, { x, y, w: 0.85, h: 0.85, fontSize: 20, bold: true, color: C.background1, align: "center",
    valign: "middle", margin: 0, isTextBox: true, objectName: name + "_tag" });
}
const fmt = (x) => (x > 0 ? "+" : "") + x.toFixed(1);

// ---------- 1. title
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
s.addText("Record-low sentiment is not, by itself, a spending signal", { placeholder: "title" });
s.addText([
  { text: "AI, economic perceptions and Michigan consumer sentiment before the 2026 midterms", options: { breakLine: true } },
  { text: "Aditya Gupta · FRE-GY 7871 NLP and the Investment Process · Final Project", options: { fontSize: 16 } },
], { placeholder: "body" });
s.addNotes("Michigan sentiment hit a record low of 44.8 in May 2026, below anything in 2008 or 2022, while unemployment sat " +
  "near 4.2% and the economy kept growing. My question is why, and what a forecaster or risk manager should do with that " +
  "number. The answer I will defend in the next seven minutes: the gap is real and huge, but it is mostly about the price " +
  "level and partisanship, news coverage explains very little of it, and in my sample it has not predicted spending. So do " +
  "not plan on the headline sentiment number alone.");

// ---------- 2. the gap
pres.addSection({ title: "The gap" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The gap" });
s.addText("Sentiment is 40 points below what the economy predicts", { placeholder: "title" });
s.addChart(pres.charts.LINE, [
  { name: "Michigan sentiment (ICS)", labels: D.ics.labels, values: D.ics.actual },
  { name: "Economy-only model (U, PCE inflation, GDP)", labels: D.ics.labels, values: D.ics.pred },
], { x: 0.6, y: 1.45, w: 8.1, h: 5.3, ...chartText, chartColors: [HEX.dk1, HEX.accent2], lineSize: 2, lineDataSymbol: "none",
  catAxisLabelFrequency: 24, catAxisLabelRotate: 0, valAxisMinVal: 40, valAxisMaxVal: 120, showLegend: true,
  legendPos: "b", displayBlanksAs: "gap", objectName: "gap_chart" });
stat(s, 9.2, 1.6, 3.6, fmt(D.gap2026), `points: mean gap Jan to Oct 2026 (no-change band ${D.null_lo} to +${D.null_hi})`, C.accent3, "gap");
stat(s, 9.2, 3.45, 3.6, `${D.share_explained}%`, `of the 2019 to 2026 fall explained by unemployment, inflation and growth (CI ${D.share_lo} to ${D.share_hi}%)`, C.accent2, "explained");
stat(s, 9.2, 5.3, 3.6, `${D.ics_min}`, "May 2026, the lowest reading on record", C.text1, "low");
s.addNotes(`I fit sentiment on unemployment, headline PCE inflation and real GDP growth over 2010 to 2019, using only data ` +
  `that was actually published by mid-month, and predict forward. The model expects sentiment around ${D.pred2026} in 2026; ` +
  `actual sentiment averaged ${D.ics2026}. The mean gap is ${D.gap2026} points, against a no-change band of about plus or minus 5. ` +
  `From 2019 to 2026 sentiment fell 45 points and these three indicators explain only ${D.share_explained} percent of it. ` +
  `The gap itself held for every data variant I tried: core PCE, CPI, year-on-year GDP, revised data. So the question is what fills the other 84 percent.`);

// ---------- 3. three explanations
pres.addSection({ title: "Approach" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
s.addText("Three explanations, judged by rules written before the data", { placeholder: "title" });
const cards = [
  ["H1", "Household pressures", "Price level, borrowing costs, real income, housing", "Not supported by the rule: six household controls close none of the gap in a fixed 2010-19 model; three close 6% in 1992-2019", C.accent1],
  ["H2", "Perceptions and media", "Negative, selective or framed coverage; partisan filters", "Partly: a small, borderline forecast gain from news tone; no effect on the gap that survives the controls", C.accent3],
  ["H3", "Measurement and model", "Survey mode, data timing and revisions, unstable model", `Partly: the 2010s model is unstable; web interviewing is ${D.mode_share}% of the gap, revisions 3%`, C.accent2],
];
cards.forEach(([tag, head, what, verdict, col], i) => {
  const x = 0.6 + i * 4.15;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 3.85, h: 5.0, rectRadius: 0.12, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: `card_${tag}` });
  circleLabel(s, x + 0.3, 1.85, tag, col, `card_${tag}`);
  s.addText(head, { x: x + 1.3, y: 1.85, w: 2.4, h: 0.85, fontSize: 20, bold: true, color: C.text1, valign: "middle",
    margin: 0, isTextBox: true, objectName: `card_${tag}_head` });
  s.addText(what, { x: x + 0.3, y: 2.95, w: 3.3, h: 1.2, fontSize: 15, color: C.text2, valign: "top", margin: 0,
    isTextBox: true, objectName: `card_${tag}_what` });
  s.addText(verdict, { x: x + 0.3, y: 4.3, w: 3.3, h: 2.0, fontSize: 15, bold: true, color: C.text1, valign: "top",
    margin: 0, isTextBox: true, objectName: `card_${tag}_verdict` });
});
s.addNotes("The brief asks us to separate three stories and not to assume any of them. Before running any test I wrote " +
  "down, with a timestamp, what result would count as support for each one. H1: household pressures that the headline " +
  "numbers miss. H2: perceptions shaped by coverage. H3: measurement, timing or a broken model. The verdicts by those rules " +
  "are on the cards. For H1 the rule was that controls like mortgage rates and real income close at least half the gap; " +
  "for H2, that news tone passes a strict multi-gate test and improves forecasts; for H3, that survey mode, revisions or " +
  "model instability account for at least a quarter. The next slides show the evidence, starting with how I measured the media.");

// ---------- 4. AI measurement
pres.addSection({ title: "Measuring the media" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Measuring the media" });
s.addText("Claude Opus reads economic news far better than word lists", { placeholder: "title" });
const tools = ["Claude Opus coder", "TF-IDF trained on Opus codes", "TF-IDF trained on gold", "Loughran-McDonald dictionary"];
const keys = ["opus", "tfidf_opus_trained", "tfidf_goldcv", "dictionary"];
s.addChart(pres.charts.BAR, [
  { name: "Relevance", labels: tools, values: keys.map((k) => D.f1.relevant[k]) },
  { name: "Tone", labels: tools, values: keys.map((k) => D.f1.tone[k]) },
], { x: 0.6, y: 1.45, w: 7.6, h: 5.3, barDir: "bar", barGrouping: "clustered", ...chartText,
  chartColors: [HEX.accent4, HEX.accent2], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00",
  valAxisMinVal: 0, valAxisMaxVal: 1.1, valAxisHidden: true, showLegend: true, legendPos: "b", catAxisOrientation: "maxMin",
  showTitle: true, title: "Macro-F1 against 450 double-labelled items", titleFontSize: 14, titleColor: HEX.dk2,
  objectName: "f1_chart" });
const checks = [
  ["654 / 654", "minimal-pair checks right (labels known by construction)"],
  ["0.91 to 0.98", "kappa between two independent Opus annotators on the eight main fields"],
  ["8% = 8%", "tone flips when party names are swapped, same as a null edit"],
];
checks.forEach(([big, lab], i) => {
  s.addText(big, { x: 8.7, y: 1.6 + i * 1.7, w: 4.1, h: 0.75, fontSize: 32, bold: true, color: C.accent2,
    fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: `check_${i}_value` });
  s.addText(lab, { x: 8.7, y: 2.35 + i * 1.7, w: 4.1, h: 0.75, fontSize: 14, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `check_${i}_label` });
});
s.addNotes("I coded about 8,600 distinct headlines and Reddit posts with Claude Opus on five dimensions: tone, which topics get " +
  "attention, framing such as price levels versus inflation rates, whether numbers match official data, and who gets blamed. " +
  "Against 450 items labelled by two independent annotators, Opus scores 0.94 on tone; a classic finance dictionary scores " +
  "0.38. Opus also passed every minimal-pair check, and swapping party names did not change tone more than a meaningless edit. " +
  "One honest caveat: the gold labels are also from Opus instances, not humans, so treat these as upper bounds. The guide is " +
  "in the repo for human relabelling.");

// ---------- 5. what coverage does
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Measuring the media" });
s.addText("Coverage over-weights rising inflation, not job losses", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Share of inflation stories saying 'rising'", labels: ["Months when inflation fell", "Months when inflation rose"],
    values: [D.selection.falling, D.selection.rising] },
], { x: 0.6, y: 1.45, w: 6.6, h: 5.3, barDir: "col", ...chartText, chartColors: [HEX.accent5, HEX.accent1],
  invertedColors: [HEX.accent5, HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%",
  valAxisMinVal: 0, valAxisMaxVal: 0.8, valAxisLabelFormatCode: "0%", showLegend: false, showTitle: true,
  title: "Share of inflation-direction stories saying inflation is rising", titleFontSize: 14, titleColor: HEX.dk2,
  objectName: "selection_chart" });
stat(s, 7.8, 1.6, 5.0, `p = ${D.asym_pi_p}`, "news gets more negative when inflation rises and does not recover when it falls", C.accent3, "asym_pi");
stat(s, 7.8, 3.45, 5.0, `p = ${D.asym_u_p.toFixed(2)}`, "no significant asymmetry for unemployment (bad 0.30 vs good 0.10 per point)", C.text1, "asym_u");
stat(s, 7.8, 5.3, 5.0, `${D.calib}%`, `of numerical claims match the official data that day (inflation ${D.calib_infl}%: outlets mix CPI, PCE, months and years)`, C.accent2, "calib");
s.addNotes(`Each bias needs a benchmark. Benchmarked against what inflation actually did: in the 97 months when inflation ` +
  `fell, a third of inflation-direction stories still said it was rising. Tone gets darker when inflation rises and does not ` +
  `brighten when it falls, one-sided p of ${D.asym_pi_p}. For jobs I find no significant asymmetry, and most jobs numbers are reported ` +
  `accurately. So the media bias is specific: cooling inflation is under-reported. Right-leaning outlets are also more ` +
  `negative, more so under Democratic presidents, but that part is descriptive.`);

// ---------- 6. impact on sentiment
pres.addSection({ title: "Impact" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Impact" });
s.addText("News tone explains about 1 point of a 40-point gap", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "points", labels: ["Sentiment gap, 2026 mean", "Survey switch to web interviews", "News tone, if fully causal (90% bound)"],
    values: [-D.gap2026, -D.mode_effect, -D.media_ci[0]] },
], { x: 0.6, y: 1.45, w: 7.8, h: 5.3, barDir: "bar", ...chartText, chartColors: [HEX.accent3, HEX.accent4, HEX.accent1],
  invertedColors: [HEX.accent3, HEX.accent4, HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
  valAxisMinVal: 0, valAxisMaxVal: 45, showLegend: false, catAxisOrientation: "maxMin", showTitle: true,
  title: "Index points below the economy-only model, 2026", titleFontSize: 14, titleColor: HEX.dk2, objectName: "impact_chart" });
const imp = [
  [`${D.media_contrib.toFixed(1)} pts`, `implied media contribution (90% CI ${D.media_ci[0]} to +${D.media_ci[1]}); fails the pre-registered test (q = ${D.media_q})`],
  [`q = ${D.ty_s_to_sf_q}`, "sentiment leads the SF Fed news index, not the other way round"],
  ["Experiment", "a randomized framing test plus exposure data is what a causal answer needs (design in the report)"],
];
imp.forEach(([big, lab], i) => {
  s.addText(big, { x: 8.9, y: 1.6 + i * 1.75, w: 3.9, h: 0.75, fontSize: 32, bold: true, color: i === 2 ? C.text1 : C.accent3,
    fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: `impact_${i}_value` });
  s.addText(lab, { x: 8.9, y: 2.35 + i * 1.75, w: 3.9, h: 0.95, fontSize: 14, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `impact_${i}_label` });
});
s.addNotes(`Does that bias depress sentiment? With 17 years of monthly data and household controls, news negativity has the ` +
  `right sign but fails the pre-registered test. If I take the association as fully causal, it accounts for about one point ` +
  `of the 40-point gap, and at most 2.4 points. The survey's own switch to web interviews moves the index by 6.6. And in ` +
  `Granger terms sentiment leads the SF Fed news index, not the reverse. So media coverage looks more like a mirror than a ` +
  `driver; a proper causal answer would need a randomized framing experiment, which I lay out in the report.`);

// ---------- 7. what does track it
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Impact" });
s.addText("What tracks the gap: the price level and the party in power", { placeholder: "title" });
s.addChart(pres.charts.LINE, [
  { name: "% worse off because of higher prices", labels: D.worse_prices.years.map(String), values: D.worse_prices.values },
], { x: 0.6, y: 1.45, w: 6.0, h: 4.4, ...chartText, chartColors: [HEX.accent1], lineSize: 3, lineDataSymbol: "none",
  catAxisLabelFrequency: 4, valAxisMinVal: 0, valAxisMaxVal: 60, showLegend: false, showTitle: true,
  title: "Share worse off because of higher prices (%)", titleFontSize: 14, titleColor: HEX.dk2, objectName: "prices_chart" });
s.addChart(pres.charts.LINE, [
  { name: "Democrats", labels: D.party.labels, values: D.party.dem },
  { name: "Republicans", labels: D.party.labels, values: D.party.rep },
], { x: 6.9, y: 1.45, w: 5.9, h: 4.4, ...chartText, chartColors: [HEX.accent5, HEX.accent3], lineSize: 3, lineDataSymbol: "circle",
  lineDataSymbolSize: 7, valAxisMinVal: 30, valAxisMaxVal: 100, showLegend: true, legendPos: "b", showTitle: true,
  title: "Sentiment by party around the Nov 2024 election", titleFontSize: 14, titleColor: HEX.dk2, objectName: "party_chart" });
s.addText(`Fits the price level against trend (R² ${D.anchor_r2.price_level_gap}) far better than the inflation rate (R² ${D.anchor_r2.pi})`,
  { x: 0.6, y: 6.0, w: 6.0, h: 0.8, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "prices_note" });
s.addText("Democrats -21.8, Republicans +31.8 in two months with unemployment and inflation flat",
  { x: 6.9, y: 6.0, w: 5.9, h: 0.8, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "party_note" });
s.addNotes(`Two things do track the gap. First the price level: the share of people who say they are worse off because of ` +
  `higher prices went from about 7 percent in 2019 to about half in 2026, and it follows the level of prices against ` +
  `trend, R squared ${D.anchor_r2.price_level_gap}, far better than the inflation rate. Falling inflation does not undo a ` +
  `higher bill. Second, party: after the 2024 election Democrats dropped 22 points and Republicans jumped 32 in two months, ` +
  `with fundamentals unchanged and partisan outlets' tone barely moving. The gap is also broad: every income, age and region ` +
  `group sits 33 to 45 points below its model.`);

// ---------- 8. forecasting
pres.addSection({ title: "Forecasting" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Forecasting" });
s.addText("For nowcasting sentiment, household pressures beat news tone", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "RMSE", labels: ["Economy only", "+ news tone", "+ household pressures", "+ both"],
    values: [D.rmse.m1, D.rmse.m2, D.rmse.m1b, D.rmse.m3] },
], { x: 0.6, y: 1.45, w: 7.4, h: 5.3, barDir: "col", ...chartText, chartColors: [HEX.accent4, HEX.accent3, HEX.accent1, HEX.accent2],
  invertedColors: [HEX.accent4, HEX.accent3, HEX.accent1, HEX.accent2], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 16, showLegend: false, showTitle: true,
  title: "Out-of-sample error, 107 monthly nowcasts 2017-2026 (index points)", titleFontSize: 14, titleColor: HEX.dk2,
  objectName: "rmse_chart" });
const fc = [
  [`p = ${D.cw_m1_m2}`, "news tone beats the economy-only model only by 3%, a borderline result"],
  [`p = ${D.cw_m1b_m3.toFixed(2)}`, "a similar borderline gain from news remains with household pressures in"],
  ["-32%", `error cut by six household-pressure controls (exploratory, p = ${D.cw_m1_m1b})`],
];
fc.forEach(([big, lab], i) => {
  s.addText(big, { x: 8.5, y: 1.6 + i * 1.75, w: 4.3, h: 0.75, fontSize: 32, bold: true, color: i === 2 ? C.accent1 : C.text1,
    fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: `fc_${i}_value` });
  s.addText(lab, { x: 8.5, y: 2.35 + i * 1.75, w: 4.3, h: 0.95, fontSize: 14, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `fc_${i}_label` });
});
s.addNotes(`For prediction I re-estimated each model every month using only past data, 107 nowcasts from 2017. Adding news ` +
  `tone to the economy cuts the error from ${D.rmse.m1} to ${D.rmse.m2}: borderline, p = ${D.cw_m1_m2}, and tiny. The news classifier is ` +
  `re-trained every month on codes available at the time, so nothing published later enters a forecast. Adding household pressures, cumulative ` +
  `inflation, mortgage rates, affordability, real income, cuts the error to ${D.rmse.m1b}, and news then adds a similar, borderline amount on top. That household ` +
  `comparison was not pre-registered, so I flag it as exploratory, but the gap is large. The small news gain holds with a ` +
  `rolling window and across six variants of the news measure, but a placebo that shifts the news series in time gets almost ` +
  `as many hits, so I read it as fragile.`);

// ---------- 9. implication
pres.addSection({ title: "Implication" });
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Implication" });
s.addText("Don't read record-low sentiment as a spending signal on its own", { placeholder: "title" });
s.addText([
  { text: `Sentiment and the gap have not predicted real consumer spending 1 to 3 months ahead (exploratory test, p = ${Math.min(...D.e1_p).toFixed(2)} to ${Math.max(...D.e1_p).toFixed(2)})`, options: { bullet: true, breakLine: true } },
  { text: "The gap looks mostly like price-level and partisan pessimism, not a fall in what households can spend", options: { bullet: true, breakLine: true } },
  { text: "So in spending forecasts and consumer risk models, do not lean on the headline index on its own", options: { bullet: true } },
], { placeholder: "body", fontSize: 18, paraSpaceAfter: 8 });
s.addNotes(`So the one practical implication for forecasting and risk: do not treat the record low as a signal of weaker ` +
  `consumer spending on its own. In this sample neither sentiment nor the gap predicted real consumer spending one or three ` +
  `months ahead, which matches research showing partisan pessimism does not reach the wallet. That is a null with modest ` +
  `power, from an exploratory test, and I did not test recession risk directly. In practice: in a spending forecast or a ` +
  `consumer-credit risk model, do not give the headline index weight on its own. Separately, for nowcasting sentiment itself, ` +
  `household-pressure data beat news tone. Limitations: AI labels are not human labels, ` +
  `I used headlines only, and the media evidence is observational. Thank you.`);

(async () => {
  await pres.writeFile({ fileName: OUT });
  const applyPath = process.env.APPLY_THEME;
  if (applyPath && fs.existsSync(applyPath)) {
    const { applyTheme } = require(applyPath);
    await applyTheme(OUT, THEME);
  }
  console.log("wrote", OUT);
})();
