// Builds presentation/Final_Project_Presentation.pptx from presentation/deck_data.json
// (written by scripts/13_deck_data.py from the saved outputs). Native charts, speaker notes.
//   python scripts/13_deck_data.py && node presentation/build_deck.js
// Needs pptxgenjs (npm install pptxgenjs) and, for the theme colours, the pptx skill's apply_theme.js
// (path in APPLY_THEME, optional: without it the deck keeps Office's default palette).
// Slides 1 to 12 are the timed talk; 13 to 15 are backup slides for questions.
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
pres.title = "Deciphering the disconnect between economic data and the mood of American Consumers";
pres.author = "Aditya Gupta";
const C = pres.SchemeColor;

// ---------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.6, w: 11.7, h: 1.9, fontSize: 44, bold: true,
      color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.7, w: 11.7, h: 2.0, fontSize: 20,
      color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({   // the closing slide: dark, a title only, placed where Aditya put it
  title: "THANKS_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.69, y: 2.67, w: 11.7, h: 1.9, fontSize: 44, bold: true,
      color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontSize: 28, bold: true,
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
const TOP = 1.45, CH = 4.65;   // content top and chart height: charts end at 6.1, above the takeaway band

function stat(slide, x, y, w, big, label, color, name) {
  slide.addText(big, { x, y, w, h: 0.75, fontSize: 36, bold: true, color, fontFace: THEME.headFontFace, margin: 0,
    isTextBox: true, objectName: name + "_value" });
  slide.addText(label, { x, y: y + 0.75, w, h: 0.75, fontSize: 13, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: name + "_label" });
}
function stats(slide, x, w, items, name) {   // up to three stacked stats in the right-hand column
  items.forEach(([big, lab, col], i) => stat(slide, x, TOP + 0.1 + i * 1.57, w, big, lab, col || C.accent2, `${name}_${i}`));
}
function takeaway(slide, text) {   // the one-line conclusion at the foot of every slide
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.28, w: 12.1, h: 0.6, rectRadius: 0.08,
    fill: { color: C.background2 }, line: { color: C.background2 }, objectName: "takeaway_box" });
  slide.addText([{ text: "Takeaway   ", options: { bold: true, color: C.accent1 } }, { text, options: { color: C.text1 } }],
    { x: 0.85, y: 6.28, w: 11.7, h: 0.6, fontSize: 15, valign: "middle", margin: 0, isTextBox: true, objectName: "takeaway" });
}
function darkTakeaway(slide, text, y = 6.05) {
  slide.addText([{ text: "Takeaway   ", options: { bold: true, color: C.accent1 } }, { text, options: { color: C.background1 } }],
    { x: 0.8, y, w: 11.7, h: 0.7, fontSize: 17, valign: "middle", margin: 0, isTextBox: true, objectName: "takeaway" });
}
function circleLabel(slide, x, y, txt, fill, name, d = 0.85, fs = 20) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + "_circle" });
  slide.addText(txt, { x, y, w: d, h: d, fontSize: fs, bold: true, color: C.background1, align: "center",
    valign: "middle", margin: 0, isTextBox: true, objectName: name + "_tag" });
}
const fmt = (x) => (x > 0 ? "+" : "") + x.toFixed(1);
const minus = (s) => String(s).replace(/-/g, "−");

// ---------- 1. title
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
s.addText([   // line breaks by meaning, so no word is left alone on the last line
  { text: "Deciphering the disconnect", options: { breakLine: true } },
  { text: "between economic data", options: { breakLine: true } },
  { text: "and the mood of American Consumers" },
], { placeholder: "title" });
// layout as Aditya set it in PowerPoint: subtitle, a gap, then name, course and project on their own lines; no takeaway here
s.addText([
  { text: "AI-measured news, Michigan sentiment and the economy before the 2026 midterms", options: { breakLine: true } },
  { text: "", options: { breakLine: true } }, { text: "", options: { breakLine: true } },
  { text: "", options: { breakLine: true } }, { text: "", options: { breakLine: true } },
  { text: "Aditya Gupta", options: { fontSize: 16, breakLine: true } },
  { text: "FRE-GY 7871 NLP and the Investment Process", options: { fontSize: 16, breakLine: true } },
  { text: "Final Project", options: { fontSize: 16 } },
], { placeholder: "body" });
s.addNotes("Michigan consumer sentiment hit a record low of 44.8 in May 2026, lower than in 2008 or 2022, while unemployment " +
  "sat near 4.2 percent and the economy kept growing. So why the disconnect? The brief gives three explanations: real " +
  "pressures the headline numbers miss, perceptions shaped by the news, or a measurement problem. My answer: the gap is real " +
  "and huge, the news explains about one point of it, and most of the rest stays unexplained unless the model learns from 2021 to 2025. I will end " +
  "with what that means for forecasters.");

// ---------- 2. the gap (RQ3)
pres.addSection({ title: "The gap" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "The gap" });
s.addText("The Gap : Sentiment is 40 points below what the economy predicts", { placeholder: "title" });   // title as Aditya set it
s.addChart(pres.charts.LINE, [
  { name: "Michigan sentiment (ICS, index points)", labels: D.ics.labels, values: D.ics.actual },
  { name: "Economy-only model (unemployment, PCE inflation, GDP growth)", labels: D.ics.labels, values: D.ics.pred },
], { x: 0.6, y: TOP, w: 8.1, h: CH, ...chartText, chartColors: [HEX.dk1, HEX.accent2], lineSize: 2, lineDataSymbol: "none",
  catAxisLabelFrequency: 24, catAxisLabelRotate: 0, valAxisMinVal: 40, valAxisMaxVal: 120, showLegend: true,
  legendPos: "b", displayBlanksAs: "gap", objectName: "gap_chart" });
stats(s, 9.2, 3.6, [
  [minus(fmt(D.gap2026)), `index points: 2026 average gap, actual ICS minus the model (a normal year: ${minus(D.null_lo)} to +${D.null_hi})`, C.accent3],
  [`${D.share_explained}%`, `of the 44.8-point fall in ICS from 2019 to 2026 is explained by the three indicators`, C.accent2],
  [`${D.ics_min}`, "ICS in May 2026, the lowest reading on record", C.text1],
], "gap");
takeaway(s, "The economy explains about a sixth of the slump; the other five-sixths needs another explanation.");
s.addNotes(`First, how big is the gap? I fit sentiment on unemployment, headline PCE inflation and GDP growth over 2010 to ` +
  `2019, using only data published by mid-month, and predicted forward. In 2026 the model expects about ${Math.round(D.pred2026)}; actual ` +
  `sentiment averaged ${Math.round(D.ics2026)}. So the gap, actual minus predicted, is minus ${Math.abs(D.gap2026)} index points, where a normal year ` +
  `stays within about five. Of the 45-point fall since 2019, these three indicators explain only ${D.share_explained} percent, and the gap holds ` +
  `with CPI, core PCE or revised data.`);

// ---------- 3. three explanations
pres.addSection({ title: "Approach" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
s.addText("The Approach : Which of three explanations can fill the gap?", { placeholder: "title" });   // title as Aditya set it
const cards = [
  ["H1", "Household pressures", "Price level, borrowing costs, real income, housing",
    `Household costs close ${D.f4_shares[0]}% of the 2026 gap in the 2010-19 model (they widen it) and ${D.f4_shares[1]}% in 1992-2019`, C.accent1],   // wording as Aditya set it
  ["H2", "Perceptions and media", "Negative, selective or framed coverage; partisan filters",
    "Partly: a small, borderline forecast gain from news tone; no effect on the gap that survives household costs", C.accent3],
  ["H3", "Measurement and model", "Survey method, data timing and revisions, an unstable model",
    `Partly: the 2010s model is unstable; the web-interview switch is ${D.mode_share}% of the 39.9-point gap; data revisions none`, C.accent2],
];
cards.forEach(([tag, head, what, verdict, col], i) => {
  const x = 0.6 + i * 4.15;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: TOP + 0.05, w: 3.85, h: 4.6, rectRadius: 0.12, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: `card_${tag}` });
  circleLabel(s, x + 0.3, TOP + 0.3, tag, col, `card_${tag}`);
  s.addText(head, { x: x + 1.3, y: TOP + 0.3, w: 2.4, h: 0.85, fontSize: 20, bold: true, color: C.text1, valign: "middle",
    margin: 0, isTextBox: true, objectName: `card_${tag}_head` });
  s.addText(what, { x: x + 0.3, y: TOP + 1.35, w: 3.3, h: 1.0, fontSize: 15, color: C.text2, valign: "top", margin: 0,
    isTextBox: true, objectName: `card_${tag}_what` });
  s.addText(verdict, { x: x + 0.3, y: TOP + 2.45, w: 3.3, h: 2.1, fontSize: 15, bold: true, color: C.text1, valign: "top",
    margin: 0, isTextBox: true, objectName: `card_${tag}_verdict` });
});
takeaway(s, "No single explanation wins on its own; each was held to a bar set before seeing any result.");
s.addNotes("The brief gives three candidate explanations, and I did not want to pick a favourite after seeing the data. So " +
  "before any test I wrote down the bar each one had to clear. H1, household pressures: costs must close half the gap. H2, " +
  "media and perceptions: news must pass a six-gate test and improve forecasts. H3, measurement: survey method or revisions " +
  "must account for a quarter of the gap, or the 2010s model must prove unstable. By those rules H1 fails, and H2 and H3 are partly supported.");

// ---------- 4. AI measurement
pres.addSection({ title: "Measuring the media" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Measuring the media" });
s.addText("Measuring the News : Turning headlines into scores", { placeholder: "title" });   // title as Aditya set it
s.addText("To turn news into numbers, every headline needs a score. We compared four ways of scoring on a 450-item answer key.",
  { x: 0.6, y: TOP - 0.12, w: 12.1, h: 0.42, fontSize: 15.5, color: C.text1, margin: 0, valign: "middle", fit: "none",
    isTextBox: true, objectName: "score_lead" });
s.addText([
  { text: "Relevance: ", options: { bold: true, color: C.accent4 } },
  { text: "is the headline about the US economy (prices, jobs, interest rates, growth)? Yes or no.", options: { color: C.text2, breakLine: true } },
  { text: "Tone: ", options: { bold: true, color: C.accent2 } },
  { text: "does it describe the economy getting worse (negative), better (positive) or neither (neutral)?", options: { color: C.text2 } },
], { x: 0.6, y: TOP + 0.42, w: 7.9, h: 0.62, fontSize: 13.5, margin: 0, valign: "top", isTextBox: true, objectName: "score_defs" });
const tools = ["Claude Opus coder", "Tier C (classifier trained on Opus labels)", "Classifier trained on 450 gold items", "Loughran-McDonald dictionary"];
const keys = ["opus", "tfidf_opus_trained", "tfidf_goldcv", "dictionary"];
s.addChart(pres.charts.BAR, [
  { name: "Relevance", labels: tools, values: keys.map((k) => D.f1.relevant[k]) },
  { name: "Tone", labels: tools, values: keys.map((k) => D.f1.tone[k]) },
], { x: 0.6, y: TOP + 1.1, w: 7.9, h: 3.55, barDir: "bar", barGrouping: "clustered", ...chartText,
  chartColors: [HEX.accent4, HEX.accent2], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00",
  valAxisMinVal: 0, valAxisMaxVal: 1.1, valAxisHidden: true, showLegend: true, legendPos: "b", catAxisOrientation: "maxMin",
  showTitle: true, title: "Accuracy on the answer key: 300 headlines, 150 Reddit posts (macro-F1, 1 = perfect)", titleFontSize: 13, titleColor: HEX.dk2,
  objectName: "f1_chart" });
// right: how the scoring was scaled to every headline
const RX = 8.85, RW = 3.85;
s.addText("How we scaled it", { x: RX, y: TOP + 0.42, w: RW, h: 0.35, fontSize: 14, bold: true, color: C.text2, margin: 0,
  isTextBox: true, objectName: "scale_head" });
const steps = [
  ["1", "Claude Opus scores a sample", `about 9,400 headlines and posts, as many as the usage limit allowed`],
  ["2", "A classifier learns from Opus", `TF-IDF + logistic regression ("Tier C"), trained on ${D.tierc.n_train.toLocaleString("en-US")} Opus labels`],
  ["3", "Tier C scores every headline", ""],
];
steps.forEach(([n, head, body], k) => {
  const y = TOP + 0.9 + k * 1.12;
  circleLabel(s, RX, y, n, C.accent2, `scale_${n}`, 0.45, 14);
  s.addText(head, { x: RX + 0.6, y: y - 0.02, w: RW - 0.6, h: 0.34, fontSize: 14, bold: true, color: C.text1, margin: 0,
    valign: "middle", isTextBox: true, objectName: `scale_${n}_head` });
  if (body) s.addText(body, { x: RX + 0.6, y: y + 0.33, w: RW - 0.6, h: 0.62, fontSize: 12, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `scale_${n}_body` });
  if (k < steps.length - 1) s.addShape(pres.shapes.LINE, { x: RX + 0.225, y: y + 0.5, w: 0, h: 0.57,
    line: { color: HEX.accent4, width: 1.5, endArrowType: "triangle" }, objectName: `scale_arrow_${n}` });
});
s.addText("125,440", { x: RX + 0.6, y: TOP + 0.9 + 2 * 1.12 + 0.36, w: RW - 0.6, h: 0.7, fontSize: 36, bold: true, color: C.accent1,
  fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: "scale_count" });
s.addText("economic headlines scored, 2010 to 2026, for the monthly news series", { x: RX + 0.6, y: TOP + 0.9 + 2 * 1.12 + 1.05,
  w: RW - 0.6, h: 0.55, fontSize: 12, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "scale_count_label" });
takeaway(s, "Opus is the measuring tool; Tier C copies it at scale, with noisier tone (F1 0.61 vs 0.89).");
s.addNotes("Next, how to measure the news. To turn news into numbers, every headline needs a score: is it about the economy, " +
  "that is relevance, and does it describe things getting worse or better, that is tone. I compared four ways of scoring " +
  "against a 450-headline answer key built by two other Claude models plus my corrections. " +
  `Claude Opus scores ${D.f1.tone.opus.toFixed(2)} on tone; a classic finance word list scores ${D.f1.tone.dictionary.toFixed(2)}, because it cannot read context. ` +
  "Opus could only score about 9,400 items within the usage limit, so I trained a simple classifier, TF-IDF plus logistic " +
  "regression, on its labels. That classifier, Tier C, scored all 125,440 economic headlines; it is good on relevance, noisier on tone.");

// ---------- 5. what coverage does (RQ1)
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Measuring the media" });
s.addText("News Bias : Is economic coverage biased against the facts?", { placeholder: "title" });   // title as Aditya set it
// three panels, one per kind of news: how negativity reacts to bad news (red) and to good news (blue).
// The units differ between panels, so each has its own scale; fair coverage gives mirror-image bars in each.
s.addText("How news negativity reacts to bad and good news. Fair coverage gives mirror-image bars.", { x: 0.6, y: TOP - 0.08,
  w: 7.75, h: 0.4, fontSize: 14, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "asym_head" });
const A3 = D.asym3;
const panels = [   // [title, values, axis limit, axis step, label format, p-value text]
  ["Inflation (per 1 pp)", A3.inflation, 0.08, 0.04, "+0.000;-0.000", `p = ${A3.inflation.p}: lopsided`],
  ["Unemployment (per 1 pp)", A3.unemployment, 0.4, 0.2, "+0.00;-0.00", `p = ${A3.unemployment.p.toFixed(2)}: no detectable gap`],
  ["Jobs days (per 0.1 pp)", A3.jobs_days, 0.2, 0.1, "+0.000;-0.000", `p = ${A3.jobs_days.p.toFixed(2)}: no detectable gap`],
];
panels.forEach(([name, v, lim, step, fmtc, ptxt], k) => {
  const x = 0.6 + k * 2.62;
  s.addChart(pres.charts.BAR, [{ name, labels: ["Bad news", "Good news"], values: [v.bad, v.good] }], {
    x, y: TOP + 0.38, w: 2.5, h: 3.55, barDir: "col", ...chartText, chartColors: [HEX.accent3, HEX.accent5],
    invertedColors: [HEX.accent3, HEX.accent5], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: fmtc,
    dataLabelFontSize: 10, valAxisMinVal: -lim, valAxisMaxVal: lim, valAxisMajorUnit: step, valAxisLabelFontSize: 10,
    catAxisLabelFontSize: 11, valAxisLabelFormatCode: step < 0.1 ? "0.00" : "0.0", showLegend: false, showTitle: true,
    title: name, titleFontSize: 12, titleColor: HEX.dk2, objectName: `asym_chart_${k}` });
  s.addText(ptxt, { x, y: TOP + 3.96, w: 2.5, h: 0.3, fontSize: 12, bold: k === 0, color: k === 0 ? C.accent3 : C.text2,
    align: "center", margin: 0, isTextBox: true, objectName: `asym_p_${k}` });
});
s.addText("Bad news: inflation or unemployment rises. Inflation and unemployment: monthly change in net negativity of all economic " +
  "headlines. Jobs days: change in the share of a jobs-report day's headlines that are negative, against an unchanged report.",
  { x: 0.6, y: TOP + 4.3, w: 7.75, h: 0.45, fontSize: 10.5, color: C.text2, margin: 0, valign: "top", isTextBox: true,
    objectName: "asym_note" });
// by source, benchmarked: difference from center outlets covering the same month (so the economy is held fixed),
// split by the party in the White House; both panels share one scale so they can be compared
const SRC = [["Left-leaning", "left", HEX.accent4], ["Local", "local", HEX.accent4], ["Right-leaning", "right", HEX.accent3],
  ["Reddit", "reddit", HEX.accent6]];
const BP = D.by_source_by_president;
[["D", "Democratic president (points vs center, same month)"],
 ["R", "Republican president (points vs center, same month)"]].forEach(([prt, ttl], k) => {
  s.addChart(pres.charts.BAR, [
    { name: prt, labels: SRC.map((x) => x[0]), values: SRC.map((x) => BP[prt][x[1]].pts) },
  ], { x: 8.6, y: TOP - 0.08 + k * 2.12, w: 4.1, h: 2.08, barDir: "col", ...chartText, chartColors: SRC.map((x) => x[2]),
    invertedColors: SRC.map((x) => x[2]), showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.0;-0.0",
    dataLabelFontSize: 10, valAxisMinVal: -10, valAxisMaxVal: 25, valAxisMajorUnit: 10, valAxisLabelFormatCode: "+0;-0;0",
    valAxisLabelFontSize: 9, catAxisLabelFontSize: 10, showLegend: false, showTitle: true, title: ttl, titleFontSize: 11,
    titleColor: HEX.dk2, objectName: `source_chart_${prt}` });
});
// (the note under these two charts was removed by Aditya in PowerPoint)
takeaway(s, "Inflation coverage is lopsided. Also, right-leaning outlets run darkest when Democrats hold the White House.");   // Aditya's wording
s.addNotes(`RQ1: is the coverage biased? Fair coverage reacts to good news as strongly as to bad, so the bars would be mirror ` +
  `images. For inflation they are not: net negativity rises after inflation goes up and rises again after it comes down; ` +
  `p is ${D.asym_pi_p}. Unemployment and jobs-report days show no detectable gap. By source, against center outlets in the same ` +
  `month, right-leaning outlets run 16 points darker under Democratic presidents and 6 under Republican ones, and Reddit is ` +
  `darker under Republicans. So the bias is specific: news stays dark when inflation cools, and partisan outlets are darkest in opposition.`);

// ---------- 6. impact on sentiment (RQ2)
pres.addSection({ title: "Impact" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Impact" });
s.addText("Impact : Does negative news pull sentiment down?", { placeholder: "title" });   // title as Aditya set it
// left: bars drawn with shapes. The gap, the survey's web switch (a measurement change, not media), and media tone
// (news + Reddit, each at its 90% upper bound if causal) with and without the household costs in the model
s.addText("Index points of sentiment below the economy-only model, 2026", { x: 0.6, y: TOP - 0.08, w: 7.9, h: 0.32,
  fontSize: 13, color: C.text2, margin: 0, isTextBox: true, objectName: "impact_head" });
const BX6 = 0.6, BW6 = 7.0, MAX6 = 45, sc6 = BW6 / MAX6, GY0 = TOP + 0.55, GY1 = TOP + 3.95;
[0, 10, 20, 30, 40].forEach((v) => {
  s.addShape(pres.shapes.LINE, { x: BX6 + v * sc6, y: GY0, w: 0, h: GY1 - GY0, line: { color: "DDE2E8", width: 0.75 },
    objectName: `impact_grid_${v}` });
  s.addText(String(v), { x: BX6 + v * sc6 - 0.3, y: TOP + 0.27, w: 0.6, h: 0.28, fontSize: 10, color: C.text2, align: "center",
    margin: 0, isTextBox: true, objectName: `impact_tick_${v}` });
});
const NEWS = -D.media_ci[0], RED = -D.e3.ci_h1[0], NEWS0 = -D.media_no_h1.ci[0], RED0 = -D.e3.ci_econ[0];
const rows6 = [
  ["2026 sentiment gap", [[-D.gap2026, C.accent3]], `${(-D.gap2026).toFixed(1)}`],
  ["Survey switch to web interviews (a measurement change, not media)", [[-D.mode_effect, C.accent4]], `${(-D.mode_effect).toFixed(1)}`],
  ["Media tone, household costs in the model (90% upper bound)", [[NEWS, C.accent1], [RED, C.accent6]], `at most ${(NEWS + RED).toFixed(1)}`],
  ["Media tone, household costs left out (90% upper bound)", [[NEWS0, C.accent1], [RED0, C.accent6]], `at most ${(NEWS0 + RED0).toFixed(1)}`],
  // the household costs' own share in the same model (coefficient x change, best estimate), for scale against the media
  ["Household costs, same model (points of the 2019-26 fall, best estimate)", [[D.drop.in_sample.household_all6.pts, C.accent2]],
    `about ${D.drop.in_sample.household_all6.pts.toFixed(0)} (${D.drop.in_sample.household_all6.ci[0].toFixed(0)} to ${D.drop.in_sample.household_all6.ci[1].toFixed(0)})`],
];
rows6.forEach(([lab, segs, val], k) => {
  const y = TOP + 0.58 + k * 0.68;
  s.addText(lab, { x: BX6, y, w: 7.7, h: 0.26, fontSize: 12.5, bold: true, color: C.text1, margin: 0, valign: "middle",
    isTextBox: true, objectName: `impact_row_${k}_label` });
  let x = BX6;
  segs.forEach(([v, col], j) => {
    s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.27, w: v * sc6, h: 0.34, fill: { color: col }, line: { color: "FFFFFF", width: 0.75 },
      objectName: `impact_row_${k}_seg_${j}` });
    x += v * sc6;
  });
  s.addText(val, { x: x + 0.1, y: y + 0.27, w: 2.2, h: 0.34, fontSize: 14, bold: true, color: C.text1, margin: 0, valign: "middle",
    isTextBox: true, objectName: `impact_row_${k}_value` });
});
[["News tone (Tier C, news headlines)", C.accent1], ["Reddit tone (exploratory)", C.accent6]].forEach(([t, col], j) => {
  const x = BX6 + j * 3.6, y = TOP + 3.98;
  s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.05, w: 0.2, h: 0.2, fill: { color: col }, line: { color: col }, objectName: `impact_key_${j}` });
  s.addText(t, { x: x + 0.3, y, w: 3.2, h: 0.3, fontSize: 12, color: C.text1, margin: 0, valign: "middle", isTextBox: true,
    objectName: `impact_key_${j}_text` });
});
// one line on why these bars are not subtracted on slide 10
s.addText(`Bars 3 to 5 come from models fit on 2010 to 2026 (in sample), so slide 10 does not subtract them. Media best estimates: news about ${Math.abs(D.media_contrib).toFixed(1)} (${Math.abs(D.media_no_h1.contrib).toFixed(1)} without household costs), Reddit about 0.`,
  { x: BX6, y: TOP + 4.31, w: 7.9, h: 0.4, fontSize: 10.5, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "impact_note" });
// right: how the media number is obtained, as three steps (as on slide 4), plus why household costs are in
const RX6 = 8.75, RW6 = 3.95;
s.addText("How we got the media number", { x: RX6, y: TOP - 0.08, w: RW6, h: 0.32, fontSize: 14, bold: true, color: C.text2,
  margin: 0, isTextBox: true, objectName: "impact_steps_head" });
const perPP = Math.abs(D.media_coef) / 100, ppChange = Math.round(100 * D.media_change);
const steps6 = [
  ["1", "One model, three blocks", "Sentiment on the economy, six household costs and news tone, 191 months from 2010 to 2026"],
  ["2", "Assume the link is causal", "That is, all of it runs from the news to people's mood, none from shared causes such as gas prices"],
  ["3", `1 pp darker news → ${perPP.toFixed(2)} points lower`, `News got ${ppChange} pp darker from 2019 to 2026: about ${Math.abs(D.media_contrib).toFixed(1)} point, at most ${NEWS.toFixed(1)}`],
];
steps6.forEach(([n, head, body], k) => {
  const y = TOP + 0.4 + k * 1.0;
  circleLabel(s, RX6, y, n, C.accent2, `impact_step_${n}`, 0.42, 13);
  s.addText(head, { x: RX6 + 0.55, y: y - 0.02, w: RW6 - 0.55, h: 0.32, fontSize: 13.5, bold: true, color: C.text1, margin: 0,
    valign: "middle", isTextBox: true, objectName: `impact_step_${n}_head` });
  s.addText(body, { x: RX6 + 0.55, y: y + 0.31, w: RW6 - 0.55, h: 0.6, fontSize: 11.5, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `impact_step_${n}_body` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: RX6, y: TOP + 3.45, w: RW6, h: 1.25, rectRadius: 0.08, fill: { color: C.background2 },
  line: { color: C.background2 }, objectName: "impact_why_box" });
s.addText([
  { text: "Why the news number is small: ", options: { bold: true, color: C.text1 } },
  { text: `news mostly reports pressures people already feel (prices, gas, rates), and mood moves first. Household costs carry those pressures, so they absorb most of the news effect: ${Math.abs(D.media_no_h1.contrib).toFixed(1)} without them, ${Math.abs(D.media_contrib).toFixed(1)} with them.`, options: { color: C.text2 } },
], { x: RX6 + 0.15, y: TOP + 3.5, w: RW6 - 0.3, h: 1.15, fontSize: 11.5, margin: 0, valign: "middle", isTextBox: true,
  objectName: "impact_why" });
takeaway(s, "There is an effect of negative news, but it still leaves a good part of the gap");   // Aditya's wording
s.addNotes(`RQ2: does negative news pull sentiment down? I fitted one model with the economy, six household costs and news ` +
  `tone, then assumed the link is fully causal, the most generous case for the media. Each percentage point darker news then ` +
  `lowers sentiment about ${(Math.abs(D.media_coef) / 100).toFixed(2)} points. The news got ${Math.round(100 * D.media_change)} points darker since 2019: about one point of the 40, ` +
  `at most ${(-D.media_ci[0]).toFixed(1)}, and with Reddit at most about 3. Leaving out household costs, which move with the news, gives at most ` +
  `about ${Math.round(-D.media_no_h1.ci[0])}, about ${Math.round(-D.media_no_h1.ci[0] - D.e3.ci_econ[0])} with Reddit. Either way it is small, and in the SF Fed news index mood moves first. In the same model, ` +
  `household costs account for about ${D.drop.in_sample.household_all6.pts.toFixed(0)} points, mostly housing: they absorb most of the news effect, because the news mostly reports those pressures.`);

// ---------- 7. mechanisms (RQ4)
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Impact" });
s.addText("Mechanisms : Which mental shortcuts can the data see?", { placeholder: "title" });   // title as Aditya set it
const W3 = 3.9;
s.addChart(pres.charts.BAR, [
  { name: "ICS change", labels: ["1 pp rise", "1 pp fall"], values: [D.neg_public.rise, D.neg_public.fall] },
], { x: 0.6, y: TOP, w: W3, h: 3.75, barDir: "col", ...chartText, chartColors: [HEX.accent3, HEX.accent5],
  invertedColors: [HEX.accent3, HEX.accent5], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
  valAxisMinVal: -8, valAxisMaxVal: 2, showLegend: false, showTitle: true,
  title: "Negativity bias: ICS change (points) per 1 pp move in inflation", titleFontSize: 13, titleColor: HEX.dk2, objectName: "neg_chart" });
s.addChart(pres.charts.LINE, [
  { name: "Worse off because of prices (% of people)", labels: D.worse_prices.years.map(String), values: D.worse_prices.values },
  { name: "Prices above their 2010s trend (%)", labels: D.worse_prices.years.map(String), values: D.prices_actual.level_gap },
  { name: "Inflation rate (% a year)", labels: D.worse_prices.years.map(String), values: D.prices_actual.pi },
], { x: 0.6 + W3 + 0.2, y: TOP, w: W3, h: 3.75, ...chartText, chartColors: [HEX.accent1, HEX.accent2, HEX.accent4], lineSize: 3,
  lineDataSymbol: "none", catAxisLabelFrequency: 4, valAxisMinVal: 0, valAxisMaxVal: 60, valAxisMajorUnit: 20,
  showLegend: true, legendPos: "b", showTitle: true,
  title: "Price level (exploratory): feeling worse off vs what prices did", titleFontSize: 13, titleColor: HEX.dk2, objectName: "prices_chart" });
s.addChart(pres.charts.LINE, [
  { name: "Democrats", labels: D.party.labels, values: D.party.dem },
  { name: "Republicans", labels: D.party.labels, values: D.party.rep },
], { x: 0.6 + 2 * (W3 + 0.2), y: TOP, w: W3, h: 3.75, ...chartText, chartColors: [HEX.accent5, HEX.accent3], lineSize: 3,
  lineDataSymbol: "circle", lineDataSymbolSize: 6, valAxisMinVal: 30, valAxisMaxVal: 100, showLegend: true, legendPos: "b",
  catAxisLabelFrequency: 2, showTitle: true, title: "Party (descriptive): ICS around the Nov 2024 election", titleFontSize: 13,
  titleColor: HEX.dk2, objectName: "party_chart" });
[
  "Asymmetry : A fall in inflation does not lift sentiment",   // Aditya's wording
  `Feeling worse off follows how high prices are (R² ${D.anchor_r2.price_level_gap}), not how fast they rise (R² ${D.anchor_r2.pi}).`,
  "Democrats -21.8, Republicans +31.8 points in two months, with unemployment and inflation flat.",
].forEach((t, i) => s.addText(t, { x: 0.6 + i * (W3 + 0.2), y: TOP + 3.85, w: W3, h: 0.85, fontSize: 13, color: C.text2,
  margin: 0, valign: "top", isTextBox: true, objectName: `mech_note_${i}` }));
takeaway(s, "The data can see inflation negativity, anchoring on the price level and party switching; none of it points to what people read.");
s.addNotes(`RQ4: which mental shortcuts can the data see? Three. Negativity bias: a 1-point rise in inflation lowers ` +
  `sentiment about ${Math.abs(D.neg_public.rise).toFixed(0)} points, but a 1-point fall does not lift it. The price level: the share worse off because of ` +
  `higher prices went from ${D.worse_prices_2019_2026[0]} percent in 2019 to about half. It follows the teal line, prices about ` +
  `${Math.round(D.prices_actual.level_gap.at(-1))} percent above their 2010s path, not the gray line, inflation, which is back near ${Math.round(D.prices_actual.pi.at(-1))} percent. And party: after the 2024 election Democrats fell 22 points and Republicans rose 32 in two months, ` +
  `with the economy flat. What I cannot see is any one reader's bias.`);

// ---------- 8. forecasting (RQ5)
pres.addSection({ title: "Forecasting" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Forecasting" });
s.addText("Forecasting : Does the news help predict sentiment?", { placeholder: "title" });   // title as Aditya set it
// one line on how the forecasts are made (out of sample) and what a household cost is, then two charts with plain names
s.addText([
  { text: "How: ", options: { bold: true, color: C.text1 } },
  { text: "each model is refit every month on past data only, then forecasts that month: 107 forecasts, Jan 2017 to Oct 2026, all out of sample. " +
    "Household costs: 3-year inflation, real income growth, mortgage rate, mortgage payment vs income, U-6 minus U-3, debt payments.", options: { color: C.text2 } },
], { x: 0.6, y: TOP - 0.08, w: 12.1, h: 0.5, fontSize: 12, margin: 0, valign: "top", isTextBox: true, objectName: "fc_how" });
const FCN = ["Economy only", "Economy + news", "Economy + household costs", "Economy + news + household costs"];
s.addChart(pres.charts.BAR, [
  { name: "Typical miss", labels: FCN, values: [D.rmse.m1, D.rmse.m2, D.rmse.m1b, D.rmse.m3] },
], { x: 0.6, y: TOP + 0.5, w: 5.9, h: 3.4, barDir: "bar", ...chartText, chartColors: [HEX.accent4, HEX.accent3, HEX.accent1, HEX.accent2],
  invertedColors: [HEX.accent4, HEX.accent3, HEX.accent1, HEX.accent2], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 16, valAxisMajorUnit: 4, catAxisOrientation: "maxMin", showLegend: false,
  showTitle: true, title: "Typical forecast miss (RMSE, index points)", titleFontSize: 13, titleColor: HEX.dk2,
  objectName: "rmse_chart" });
const M26 = D.mar26;
s.addChart(pres.charts.BAR, [
  { name: "March 2026", labels: ["Fixed 2010-19 model (slide 2)"].concat(FCN, ["Actual sentiment"]),
    values: [M26.modelE, M26.m1, M26.m2, M26.m1b, M26.m3, M26.actual] },
], { x: 6.8, y: TOP + 0.5, w: 5.9, h: 3.4, barDir: "bar", ...chartText,
  chartColors: [HEX.accent4, HEX.accent4, HEX.accent3, HEX.accent1, HEX.accent2, HEX.dk1],
  invertedColors: [HEX.accent4, HEX.accent4, HEX.accent3, HEX.accent1, HEX.accent2, HEX.dk1], showValue: true,
  dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25, catAxisOrientation: "maxMin",
  showLegend: false, showTitle: true, title: "Example: forecasts for March 2026 vs actual (index points)", titleFontSize: 13,
  titleColor: HEX.dk2, objectName: "mar26_chart" });
s.addText(`Adding news: misses ${Math.round(100 * (1 - D.rmse.m2 / D.rmse.m1))}% smaller. Adding household costs: ${Math.round(100 * (1 - D.rmse.m1b / D.rmse.m1))}% smaller`,   // Aditya's wording
  { x: 0.6, y: TOP + 4.0, w: 5.9, h: 0.75, fontSize: 13, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "fc_note" });
s.addText(`Refitting every month gets ${(M26.modelE - M26.m1).toFixed(0)} to ${(M26.modelE - M26.m3).toFixed(0)} points closer than the fixed 2010s model`,   // Aditya's wording
  { x: 6.8, y: TOP + 4.0, w: 5.9, h: 0.75, fontSize: 13, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "mar26_note" });
takeaway(s, "Only a little: news tone gives a small, borderline gain, while household costs cut forecast misses by a third.");
s.addNotes(`RQ5: does news help forecast sentiment? I re-fit each model every month on past data only and forecast 107 ` +
  `months from 2017. The economy alone misses by ${D.rmse.m1} points on average; adding news tone gets that to ${D.rmse.m2}, a ` +
  `borderline gain with p of ${D.cw_m1_m2}. Adding household costs instead gets it to ${D.rmse.m1b}, a third smaller. March 2026 shows ` +
  `it: actual sentiment was ${M26.actual.toFixed(1)}, the fixed 2010s model said ${Math.round(M26.modelE)}, and the updating models said ` +
  `${Math.round(M26.m3)} to ${Math.round(M26.m1)}. News moved the forecast ${(M26.m1 - M26.m2).toFixed(1)} points the right way and household costs ` +
  `${(M26.m1 - M26.m1b).toFixed(1)}, but every model was still far too high.`);

// ---------- 9. falsifiers (RQ6)
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Forecasting" });
s.addText("Falsifiers : What evidence would sink the media story?", { placeholder: "title" });   // title as Aditya set it
// condensed: one header line with the tally, then one short row per test (test, verdict chip, evidence), full width
s.addText([
  { text: "Seven tests set in advance: ", options: { bold: true, color: C.text1 } },
  { text: "if one is true, the media story weakens.", options: { color: C.text2 } },
], { x: 0.6, y: TOP - 0.05, w: 8.0, h: 0.4, fontSize: 15, margin: 0, valign: "middle", isTextBox: true, objectName: "fals_head" });
s.addText("1 true · 2 partly · 3 not true · 1 cannot tell", { x: 8.7, y: TOP - 0.05, w: 4.0, h: 0.4, fontSize: 13, bold: true,
  color: C.text2, align: "right", margin: 0, valign: "middle", isTextBox: true, objectName: "fals_tally" });
const VER = { True: [C.accent2, "True"], Partly: [C.accent1, "Partly"], False: [C.accent4, "Not true"], Open: [C.text2, "Cannot tell"] };
const fals = [
  ["F1", "News adds nothing to forecasts", "False", `News trims misses ${Math.round(100 * (1 - D.rmse.m2 / D.rmse.m1))}% (p = ${D.cw_m1_m2})`],
  ["F2", "Sentiment moves before the news", "Partly", "Yes for the SF Fed index, not for ours"],
  ["F3", "Coverage treats good and bad news alike", "Partly", "Jobs: yes. Inflation: no (p = 0.002)"],
  ["F4", "Household costs close half the gap", "False", `${D.f4_shares[1]}% at most`],
  ["F5", "Party mood moves before party media", "Open", "Monthly data cannot order them"],
  ["F6", "The web switch is as big as the gap", "False", `${(-D.mode_effect).toFixed(1)} points, ${D.mode_share}% of the gap`],
  ["F7", "Recall of price news follows the economy, not coverage", "True", `R² ${D.f7_r2[0].toFixed(2)} vs ${D.f7_r2[1].toFixed(2)}`],
];
const rowH = 0.52;
fals.forEach(([id, rule, v, res], i) => {
  const y = TOP + 0.5 + i * (rowH + 0.08);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.1, h: rowH, rectRadius: 0.06, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: `fals_${id}_row` });
  s.addText(id, { x: 0.75, y, w: 0.6, h: rowH, fontSize: 15, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `fals_${id}_id` });
  s.addText(rule, { x: 1.4, y, w: 5.6, h: rowH, fontSize: 15, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `fals_${id}_rule` });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.15, y: y + 0.09, w: 1.5, h: rowH - 0.18, rectRadius: 0.08, fill: { color: VER[v][0] },
    line: { color: VER[v][0] }, objectName: `fals_${id}_chip` });
  s.addText(VER[v][1], { x: 7.15, y: y + 0.09, w: 1.5, h: rowH - 0.18, fontSize: 12, bold: true, color: C.background1, align: "center",
    valign: "middle", margin: 0, isTextBox: true, objectName: `fals_${id}_verdict` });
  s.addText(res, { x: 8.85, y, w: 3.75, h: rowH, fontSize: 13, color: C.text2, valign: "middle", margin: 0, isTextBox: true, objectName: `fals_${id}_res` });
});
takeaway(s, "The tests that hold (timing, recall) point away from media as the main cause.");
s.addNotes("RQ6: what would sink the media story? I wrote seven falsifiers in advance. One holds clearly: what people " +
  "recall about bad price news fits the economy better than coverage. Two hold partly, three do not, but those mostly rule " +
  "out rival explanations, and one cannot be settled. The gap is also broad: every income, age and region group is 33 to 45 " +
  "points below its model, not just readers of negative outlets.");

// ---------- 10. putting it together: what explains the gap
pres.addSection({ title: "Conclusion" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusion" });
s.addText("Putting it together: what explains the 40-point gap", { placeholder: "title" });
const DR = D.drop;
// The gap must be out of sample (the brief: learn 2010-19, predict 2026), so the bar subtracts only the two pieces that need
// no model: Michigan's own web-vs-phone estimate and the party-mix comparison. News and household costs depend on which
// years a model learns from (0 in the 2010-19 model, about 1 and 19 in the 2010-2026 model), so they are listed as
// explanations of the rest, not subtracted. Data revisions are not a piece either: the 39.9 already uses the data people
// saw at the time (on final data the gap would be 41.0).
const measured = [["Web-interview switch", DR.web, C.accent4], ["Party mix of respondents", DR.party_mix, C.accent5]];
const meas = DR.gap - DR.rest;
s.addText(`The ${DR.gap}-point 2026 gap (index points): what we can subtract without a model, and what could explain the rest`,
  { x: 0.6, y: TOP - 0.05, w: 12.1, h: 0.35, fontSize: 13, color: C.text2, margin: 0, isTextBox: true, objectName: "drop_title" });
// one bar, drawn with shapes: the two survey pieces in solid colours, the rest light with a dashed edge
const BX = 0.6, BWD = 12.1, BY = TOP + 0.38, BHT = 0.7, sc = BWD / DR.gap;
let bx = BX;
measured.forEach(([n, v, col], k) => {
  const w = v * sc;
  s.addShape(pres.shapes.RECTANGLE, { x: bx, y: BY, w, h: BHT, fill: { color: col }, line: { color: "FFFFFF", width: 1 }, objectName: `drop_seg_${k}` });
  s.addText(v.toFixed(1), { x: bx, y: BY, w, h: BHT, fontSize: 15, bold: true, color: "FFFFFF", align: "center",
    valign: "middle", margin: 0, isTextBox: true, objectName: `drop_val_${k}` });
  bx += w;
});
const restX = bx, restW = DR.rest * sc;
s.addShape(pres.shapes.RECTANGLE, { x: restX, y: BY, w: restW, h: BHT, fill: { color: C.accent3, transparency: 78 },
  line: { color: C.accent3, width: 1.5, dashType: "dash" }, objectName: "drop_rest" });
s.addText(`${DR.rest.toFixed(1)} (range ${DR.rest_range[0]} to ${DR.rest_range[1]}): the suspects explain little of it`, { x: restX, y: BY, w: restW, h: BHT, fontSize: 16, bold: true,
  color: C.accent3, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "drop_rest_label" });
// brackets under the bar
const brk = (x, w, label, col, name) => {
  const y = BY + BHT + 0.12;
  s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: col, width: 1.5 }, objectName: `${name}_line` });
  s.addShape(pres.shapes.LINE, { x, y: y - 0.08, w: 0, h: 0.08, line: { color: col, width: 1.5 }, objectName: `${name}_l` });
  s.addShape(pres.shapes.LINE, { x: x + w, y: y - 0.08, w: 0, h: 0.08, line: { color: col, width: 1.5 }, objectName: `${name}_r` });
  s.addText(label, { x, y: y + 0.05, w, h: 0.32, fontSize: 13, bold: true, color: col, align: "center", margin: 0, isTextBox: true, objectName: `${name}_text` });
};
brk(BX, restX - BX - 0.05, `Survey method: about ${meas.toFixed(0)} points`, C.text2, "brk_meas");
brk(restX + 0.05, restW - 0.05, `The rest: suspects tested below`, C.accent3, "brk_rest");
// left: the two survey pieces, then why only these two are subtracted
const LY = BY + BHT + 0.62;
measured.forEach(([n, v, col], k) => {
  const y = LY + k * 0.36;
  s.addShape(pres.shapes.RECTANGLE, { x: BX, y: y + 0.07, w: 0.2, h: 0.2, fill: { color: col }, line: { color: col }, objectName: `drop_key_${k}` });
  s.addText(`${n}: ${v.toFixed(1)}`, { x: BX + 0.3, y, w: 3.5, h: 0.34, fontSize: 13, color: C.text1, margin: 0, valign: "middle",
    isTextBox: true, objectName: `drop_keytext_${k}` });
});
s.addText([
  { text: "Why only these two: ", options: { bold: true, color: C.text1 } },
  { text: "the brief asks for an out-of-sample gap (the model learns 2010-19, then predicts 2026). These two need no model. " +
    "News and household costs do, so they are explanations, not subtractions.", options: { color: C.text2 } },
], { x: BX, y: LY + 2 * 0.36 + 0.08, w: 3.6, h: 1.25, fontSize: 12, margin: 0, valign: "top", isTextBox: true, objectName: "drop_why" });
s.addText(`Before the gap: the economy explains ${DR.economy} of the ${DR.fall}-point fall since 2019.`, { x: BX, y: LY + 2 * 0.36 + 1.45,
  w: 3.6, h: 0.6, fontSize: 12, italic: true, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "drop_econ" });
// right: the suspects, tested fairly (E7): each is added to a model trained on 1978-2019 (2026 out of sample) and the
// drop in the 2026 gap is averaged over every order of adding them (Shapley), with 90% block-bootstrap ranges
const PX = 4.45, PW = 8.25;   // the right-hand area under the bar
const SU = D.suspects.strict_1978_2019, rg = (v) => `${minus(v.lo.toFixed(0))} to ${minus(v.hi.toFixed(0))}`;
const su10 = [["Borrowing costs", SU.closed.B], ["Price level", SU.closed.P5], ["Partisan mood", SU.closed.R], ["Inflation memory", SU.closed.R60]];
const suCol = (v) => (v.pts >= 0 ? HEX.accent2 : HEX.accent4);
s.addChart(pres.charts.BAR, [
  { name: "Points explained", labels: su10.map(([n, v]) => `${n} (${rg(v)})`), values: su10.map(([, v]) => v.pts) },
], { x: PX, y: LY - 0.1, w: 4.6, h: 3.2, barDir: "bar", ...chartText, chartColors: su10.map(([, v]) => suCol(v)),
  invertedColors: su10.map(([, v]) => suCol(v)), showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.0;-0.0",
  valAxisMinVal: -6, valAxisMaxVal: 10, valAxisMajorUnit: 2, catAxisOrientation: "maxMin", catAxisLabelPos: "low",
  showLegend: false, showTitle: true,
  title: `Points of the ${DR.rest.toFixed(1)} each suspect explains (90% range)`, titleFontSize: 13, titleColor: HEX.dk2, objectName: "su10_chart" });
const cards10 = [
  ["Tested fairly", `Each suspect is added to a model trained on 1978-2019 (its own 2026 gap: ${(-D.suspects.strict_base_gap).toFixed(1)}), so 2026 stays out of sample; credit is averaged over every order. Borrowing alone closes ${D.suspects.borrowing_alone.toFixed(1)}.`],
  [`About ${(DR.rest - SU.all.pts).toFixed(0)} stay unexplained`,
    `Together the suspects explain ${SU.all.pts.toFixed(1)}: the price level is about 0 and inflation memory pulls the other way, as people forgave the 1980s inflation. Partisan mood: at most ${D.suspects.partisan_bound.toFixed(0)} (Republicans, in power both times, fell ${D.suspects.in_party_fall.toFixed(1)}).`],
];
const CX = PX + 4.75, CW = PX + PW - CX;
cards10.forEach(([head, body], k) => {
  const yy = LY - 0.05 + (k === 0 ? 0 : 1.4), h = k === 0 ? 1.32 : 1.7;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: CX, y: yy, w: CW, h, rectRadius: 0.06, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: `su10_card_${k}_box` });
  s.addText(head, { x: CX + 0.15, y: yy + 0.06, w: CW - 0.3, h: 0.3, fontSize: 13.5, bold: true, color: C.text1, margin: 0,
    valign: "middle", isTextBox: true, objectName: `su10_card_${k}_head` });
  s.addText(body, { x: CX + 0.15, y: yy + 0.38, w: CW - 0.3, h: h - 0.44, fontSize: 11.5, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `su10_card_${k}_body` });
});
takeaway(s, `Survey method explains about ${meas.toFixed(0)} of the 40 points; tested fairly, the suspects add little, leaving about ${(DR.rest - SU.all.pts).toFixed(0)} unexplained.`);
s.addNotes(`So what explains the gap? The economy explains about 7 of the 45-point fall since 2019, which leaves the 40-point gap. ` +
  `The brief asks for an out-of-sample gap, so I subtract only what needs no model: Michigan's switch to web interviews, ` +
  `${DR.web} points, and the changing party mix of respondents, about ${DR.party_mix.toFixed(0)}. That leaves about ${DR.rest.toFixed(0)}. ` +
  `I then test the suspects fairly: each is added to a model trained on 1978 to 2019, with credit averaged over every order. ` +
  `Only borrowing costs help, about ${SU.closed.B.pts.toFixed(0)} points; the price level is about zero and inflation memory pulls the other way, because in the ` +
  `1980s people forgave inflation once it fell. Partisan mood is at most about ${D.suspects.partisan_bound.toFixed(0)}: Republicans, in power both times, still ` +
  `fell ${D.suspects.in_party_fall.toFixed(1)} points. So under the strict rule about ${(DR.rest - SU.all.pts).toFixed(0)} points stay unexplained pessimism.`);

// ---------- 11. the same accounting with the model trained on 2010-2025 (E6, exploratory)
// Same bar length and scale as slide 10 (the 39.9-point gap of the 2010-19 model). The first, faded segment is what
// training through 2025 removes; the rest is this model's 23-point gap, filled by adding each piece to the model in turn
// (web switch, household costs, news) plus the model-free party mix.
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusion" });
s.addText("Putting it together, trained to 2025: what fills the 2026 gap", { placeholder: "title" });
const E6 = D.e6;
s.addText(`A model trained on 2010-2025 (COVID months skipped) predicts ${E6.pred} for 2026, against ${D.ics2026} actual: a ${E6.gap}-point gap (index points)`,
  { x: 0.6, y: TOP - 0.05, w: 12.1, h: 0.35, fontSize: 13, color: C.text2, margin: 0, isTextBox: true, objectName: "e6_title" });
const segs6 = [["Closed by learning 2021-25", E6.absorbed, C.accent4, true], ["Web-interview switch", E6.web, C.accent4, false],
  ["Party mix of respondents", E6.party_mix, C.accent5, false], ["Household costs", E6.household, C.accent2, false],
  ["News tone", E6.news, C.accent1, false]];
let ex = BX;
segs6.forEach(([n, v, col, faded], k) => {
  const w = v * sc;
  s.addShape(pres.shapes.RECTANGLE, { x: ex, y: BY, w, h: BHT, fill: { color: col, transparency: faded ? 70 : 0 },
    line: { color: "FFFFFF", width: 1 }, objectName: `e6_seg_${k}` });
  if (w > 0.45) s.addText(faded ? `${v.toFixed(1)}: inflation now weighs about 3× more` : v.toFixed(1), { x: ex, y: BY, w, h: BHT, fontSize: 15,
    bold: true, color: faded ? C.text1 : "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `e6_val_${k}` });
  ex += w;
});
const e6RestX = ex, e6RestW = BX + BWD - ex;
s.addShape(pres.shapes.RECTANGLE, { x: e6RestX, y: BY, w: e6RestW, h: BHT, fill: { color: C.accent3, transparency: 78 },
  line: { color: C.accent3, width: 1.5, dashType: "dash" }, objectName: "e6_rest" });
s.addText(`${E6.rest.toFixed(1)}: covered by the suspects`, { x: e6RestX, y: BY, w: e6RestW, h: BHT, fontSize: 15, bold: true,
  color: C.accent3, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "e6_rest_label" });
const e6GapX = BX + E6.absorbed * sc;
brk(BX, e6GapX - BX - 0.05, "Gone once the model learns 2021-25", C.text2, "e6_brk_abs");
brk(e6GapX + 0.05, BX + BWD - e6GapX - 0.05, `This model's 2026 gap: ${E6.gap.toFixed(1)}`, C.accent3, "e6_brk_gap");
// left: what each piece fills, added to the model one after another
const e6keys = [[`Web-interview switch: ${E6.web.toFixed(1)}`, C.accent4], [`Party mix of respondents: ${E6.party_mix.toFixed(1)}`, C.accent5],
  [`Household costs: ${E6.household.toFixed(1)}`, C.accent2], [`News tone: ${E6.news.toFixed(1)}`, C.accent1]];
e6keys.forEach(([t, col], k) => {
  const y = LY + k * 0.36;
  s.addShape(pres.shapes.RECTANGLE, { x: BX, y: y + 0.07, w: 0.2, h: 0.2, fill: { color: col }, line: { color: col }, objectName: `e6_key_${k}` });
  s.addText(t, { x: BX + 0.3, y, w: 3.5, h: 0.34, fontSize: 13, color: C.text1, margin: 0, valign: "middle", isTextBox: true,
    objectName: `e6_keytext_${k}` });
});
s.addText([
  { text: "How: ", options: { bold: true, color: C.text1 } },
  { text: "each piece is added to the model in turn and the drop in the 2026 gap is read off; 2026 stays out of sample. " +
    "News adds little: inflation and household costs already carry what it reports.", options: { color: C.text2 } },
], { x: BX, y: LY + 4 * 0.36 + 0.08, w: 3.6, h: 1.1, fontSize: 12, margin: 0, valign: "top", isTextBox: true, objectName: "e6_how" });
const SU5 = D.suspects.trained_2010_2025;
const su11 = [["Inflation memory", SU5.closed.R60], ["Price level", SU5.closed.P5], ["Partisan mood", SU5.closed.R]];
s.addChart(pres.charts.BAR, [
  { name: "Points explained", labels: su11.map(([n, v]) => `${n} (${rg(v)})`), values: su11.map(([, v]) => v.pts) },
], { x: PX, y: LY - 0.1, w: 4.6, h: 3.2, barDir: "bar", ...chartText, chartColors: su11.map(([, v]) => suCol(v)),
  invertedColors: su11.map(([, v]) => suCol(v)), showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.0;-0.0",
  valAxisMinVal: -6, valAxisMaxVal: 10, valAxisMajorUnit: 2, catAxisOrientation: "maxMin", catAxisLabelPos: "low",
  showLegend: false, showTitle: true,
  title: `Points of the last ${E6.rest.toFixed(1)} each suspect explains (90% range)`, titleFontSize: 13, titleColor: HEX.dk2, objectName: "su11_chart" });
const cards6 = [
  [`Inflation now weighs about 3× more: ${E6.absorbed.toFixed(0)} points`,
    `Trained to 2025, 1 pp of inflation costs ${Math.abs(E6.pi_coef[1]).toFixed(1)} points of sentiment, not ${Math.abs(E6.pi_coef[0]).toFixed(1)}. Part of it is whatever rose with inflation.`],
  [`The suspects cover the last ${E6.rest.toFixed(1)}`,
    `Together ${SU5.all.pts.toFixed(1)} (range ${minus(SU5.all.lo.toFixed(0))} to ${SU5.all.hi.toFixed(0)}): people still react to the 2022 inflation peak and to prices that stayed high. Same fair test as slide 10.`],
];
cards6.forEach(([head, body], k) => {
  const yy = LY - 0.05 + k * 1.58, h = 1.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: CX, y: yy, w: CW, h, rectRadius: 0.06, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: `e6_card_${k}_box` });
  s.addText(head, { x: CX + 0.15, y: yy + 0.06, w: CW - 0.3, h: 0.5, fontSize: 13.5, bold: true, color: C.text1, margin: 0,
    valign: "top", isTextBox: true, objectName: `e6_card_${k}_head` });
  s.addText(body, { x: CX + 0.15, y: yy + 0.58, w: CW - 0.3, h: h - 0.64, fontSize: 11.5, color: C.text2, margin: 0, valign: "top",
    isTextBox: true, objectName: `e6_card_${k}_body` });
});
takeaway(s, `Trained to 2025, survey method, household costs and news fill ${(E6.gap - E6.rest).toFixed(0)} of the ${E6.gap.toFixed(0)} points; inflation memory and prices cover the rest.`);
s.addNotes(`Exploratory: what if the model also learns from 2021 to 2025? It still predicts 2026 out of sample, but now it ` +
  `expects ${E6.pred} instead of 91, so the gap falls from 40 to ${E6.gap.toFixed(0)} points. Adding each piece to this model in turn, ` +
  `the web switch fills about ${E6.web.toFixed(0)}, the party mix about ${E6.party_mix.toFixed(0)}, household costs about ${E6.household.toFixed(0)} and news almost nothing, ` +
  `since inflation and household costs already carry what the news reports. ` +
  `The last ${E6.rest.toFixed(1)} points are covered by the suspects in the same fair test: inflation memory about ${SU5.closed.R60.pts.toFixed(0)}, the price level ` +
  `about ${SU5.closed.P5.pts.toFixed(0)}.`);

// ---------- 12. implication
pres.addSection({ title: "Implication" });
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Implication" });
s.addText("Don't read record-low sentiment as a spending signal on its own", { placeholder: "title" });
s.addText([
  // first bullet (no spending signal, E1) removed by Aditya in PowerPoint; the title and notes still carry it
  { text: "The gap looks like pessimism about prices, not a fall in what households can spend", options: { bullet: true, breakLine: true } },
  { text: "In spending forecasts and consumer-risk models, put household costs in before news tone, and do not lean on the headline index alone", options: { bullet: true } },
], { placeholder: "body", fontSize: 18, paraSpaceAfter: 8 });
// "Practical Implication" tag and the lower takeaway, as Aditya set them in PowerPoint
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.8, y: 1.0, w: 2.27, h: 0.6, rectRadius: 0.08, fill: { color: C.background2 },
  line: { color: C.background2 }, objectName: "implication_tag_box" });
s.addText("Practical Implication", { x: 1.05, y: 1.0, w: 1.92, h: 0.6, fontSize: 15, bold: true, color: C.accent1, valign: "middle",
  margin: 0, isTextBox: true, objectName: "implication_tag" });
darkTakeaway(s, "Treat the record low as price-level pessimism, not a spending forecast.", 6.5);   // Aditya's wording, revised with him
const IMPL_NOTES = `So the one practical implication: do not read the record low as a spending signal on its own. In this sample ` +
  `neither sentiment nor the gap predicted real consumer spending one to three months ahead, which fits research showing ` +
  `partisan pessimism does not reach the wallet; it is a null with modest power. In a spending forecast or a consumer-credit ` +
  `model, put household-cost data in before news tone. The main limitations: the answer key is models plus my corrections, ` +
  `I used headlines only, and the media evidence is observational. Thank you.`;
s.addNotes(IMPL_NOTES);

// ---------- 13. thank you (added by Aditya in PowerPoint as a copy of slide 12, so it carries slide 12's notes)
s = pres.addSlide({ masterName: "THANKS_DARK", sectionTitle: "Implication" });
s.addText([{ text: "Thank ", options: { softBreakBefore: false } }, { text: "You !", options: { softBreakBefore: true } }], { placeholder: "title" });
s.addNotes(IMPL_NOTES);

// ---------- 15. backup: honourable mentions
pres.addSection({ title: "Backup" });
// ---------- 14. backup: Reddit (exploratory, moved to the backup on Aditya's request)
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
s.addText("Backup · Reddit : Does social media pull sentiment down?", { placeholder: "title" });
s.addChart(pres.charts.LINE, [
  { name: "Reddit net negativity (Tier C)", labels: D.e3.series.labels, values: D.e3.series.reddit },
  { name: "News net negativity (Tier C)", labels: D.e3.series.labels, values: D.e3.series.news },
], { x: 0.6, y: TOP, w: 7.9, h: CH, ...chartText, chartColors: [HEX.accent6, HEX.accent2], lineSize: 2, lineDataSymbol: "none",
  catAxisLabelFrequency: 1, catAxisLabelRotate: 0, valAxisMinVal: -0.2, valAxisMaxVal: 0.8, valAxisLabelFormatCode: "0.0",
  showLegend: true, legendPos: "b", displayBlanksAs: "gap", showTitle: true,
  title: "Share negative minus share positive, quarterly averages", titleFontSize: 13, titleColor: HEX.dk2, objectName: "reddit_chart" });
stats(s, 9.0, 3.8, [
  [D.e3.relevant.toLocaleString("en-US"), `relevant posts out of ${D.e3.posts.toLocaleString("en-US")}, scored by Tier C (median ${D.e3.median_month} a month)`, C.accent6],
  [`p = ${D.e3.p_econ}`, `economy only: ${minus(D.e3.coef_econ)} index points per 1.0 of Reddit net negativity; with household costs the sign flips (p = ${D.e3.p_h1})`, C.text1],
  [`≤ ${-D.e3.ci_h1[0]} pts`, `of the 39.9-point gap even if fully causal (90% bound, household costs in as for news); neither series moves first (p = ${D.e3.ty[0].toFixed(2)}, ${D.e3.ty[1].toFixed(2)})`, C.accent6],
], "e3");
takeaway(s, `No detectable link: even taken as causal, Reddit tone explains at most ${-D.e3.ci_h1[0]} of the 40 points (with a weak measure).`);
s.addNotes(`One extra question I added after the main results: does Reddit move sentiment the way RQ2 asks of news? ` +
  `Tier C scored all ${D.e3.posts.toLocaleString("en-US")} Reddit posts I collected. Reddit tone shows no detectable link to sentiment; the sign even flips ` +
  `once household costs are in, and even taken as causal it is at most about ${-D.e3.ci_h1[0]} of the 40 points. The caveat: it was not ` +
  `pre-registered, and Tier C reads Reddit tone poorly, which pulls any link toward zero.`);

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
s.addText("Backup: other checks that did not make the main story", { placeholder: "title" });
const hm = [
  ["Spending", `p = ${Math.min(...D.e1_p).toFixed(2)}-${Math.max(...D.e1_p).toFixed(2)}`, "sentiment and the gap do not predict real spending 1-3 months ahead"],
  ["Recall vs coverage", "r = 0.78", "people's recall of price news tracks coverage; for jobs only 0.15-0.29"],
  ["Minimal pairs", "654 / 654", "made-up items with known answers, all labelled right by Opus"],
  ["Party-name swaps", "8% = 8%", "tone changes as often as after a meaningless edit; source tags change nothing"],
  ["Test-retest", `κ ${D.retest_tone}`, "Opus tone on 150 items labelled twice in other batches"],
  ["Release days", "56% vs 24-28%", "jobs-day headlines negative after a 0.2+ pp unemployment rise vs when it fell or held"],
  ["Web interviews", `${minus(D.mode_gap)} pts`, `2026 gap at the old phone mode (6.6 points, ${D.mode_share}% of the gap)`],
  ["Party mix", `${minus(-(D.party_eq[0] - D.party_eq[1]).toFixed(0))} vs ${minus(-(D.party_eq[2] - D.party_eq[3]).toFixed(0))}`, "equal-weight party index vs ICS, 2017-19 to 2026 (index points): mix explains a few"],
  ["Midterm timing", minus(D.midterm[2].toFixed(1)), `2026 Jun-Oct change in the gap (points), like other years (${minus(D.midterm[1].toFixed(1))})`],
  ["Data variants", `${minus(D.variants_range[0])} to ${minus(D.variants_range[1])}`, "2026 gap with CPI, core PCE, yearly GDP, revised or start-of-month data"],
  ["Placebo shifts", `${D.placebo_hits} of 6`, "news shifted 1-5 years out of line still 'wins': the 6 of 6 grid is weak evidence"],
  ["Look-ahead fix", "0.037 → 0.053", "news forecast p once Tier C is re-trained month by month on past labels only"],
];
const GW = 2.9, GH = 1.45, GXp = 0.17, GYp = 0.12;
hm.forEach(([head, big, lab], k) => {
  const x = 0.6 + (k % 4) * (GW + GXp), y = TOP + Math.floor(k / 4) * (GH + GYp);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: GW, h: GH, rectRadius: 0.08, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: `hm_${k}_box` });
  s.addText(head, { x: x + 0.15, y: y + 0.08, w: GW - 0.3, h: 0.3, fontSize: 12, bold: true, color: C.text2, margin: 0, isTextBox: true, objectName: `hm_${k}_head` });
  s.addText(big, { x: x + 0.15, y: y + 0.36, w: GW - 0.3, h: 0.45, fontSize: 21, bold: true, color: C.accent2, fontFace: THEME.headFontFace,
    margin: 0, isTextBox: true, objectName: `hm_${k}_value` });
  s.addText(lab, { x: x + 0.15, y: y + 0.82, w: GW - 0.3, h: 0.6, fontSize: 11, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: `hm_${k}_label` });
});
takeaway(s, "Every side check points the same way: a real, broad gap that news does not explain.");
s.addNotes("Backup slide for questions. These checks did not make the main story but support it. Sentiment and the gap do " +
  "not forecast spending. People's recall of price news tracks coverage, but recall moves first. The coder passed every " +
  "minimal pair, swapping party names changes tone no more than a meaningless edit, and re-labelling gives the same tone. " +
  "Jobs-day headlines turn negative only after real rises in unemployment. The survey's web switch, the changing party mix, " +
  "election timing and six ways of measuring the economy all leave most of the gap in place. The forecast grid's 6 of 6 is " +
  "weak evidence because shifted news also wins, and fixing a look-ahead in Tier C moved the news forecast p from 0.037 to 0.053.");

// ---------- 16. backup: Tier C
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
s.addText("Backup: how Tier C was trained and checked", { placeholder: "title" });
const tcNames = { relevant: "relevance", tone: "tone", "topic:inflation_up": "inflation up", "topic:inflation_down": "inflation down",
  "topic:prices_high": "prices high", "topic:layoffs": "layoffs", "topic:hiring": "hiring" };
const tcRows = D.tierc.rows;
s.addChart(pres.charts.BAR, [
  { name: "Training labels (fit)", labels: tcRows.map((x) => tcNames[x.name]), values: tcRows.map((x) => x.train) },
  { name: "Unseen Opus labels (5-fold CV)", labels: tcRows.map((x) => tcNames[x.name]), values: tcRows.map((x) => x.cv) },
  { name: "Gold labels (never trained on)", labels: tcRows.map((x) => tcNames[x.name]), values: tcRows.map((x) => x.gold) },
], { x: 0.6, y: TOP, w: 8.1, h: CH, barDir: "col", barGrouping: "clustered", ...chartText,
  chartColors: [HEX.accent4, HEX.accent5, HEX.accent1], valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0.0",
  showLegend: true, legendPos: "b", showTitle: true, title: "Macro-F1 by classifier (1 = perfect; no gold score for inflation down)",
  titleFontSize: 13, titleColor: HEX.dk2, objectName: "tierc_chart" });
stats(s, 9.2, 3.6, [
  [D.tierc.n_train.toLocaleString("en-US"), "Opus-labelled items it learned from (TF-IDF + logistic regression); gold items never used", C.accent2],
  [`r = ${D.tierc.r_opus_q}`, `quarterly net negativity vs Opus's own labels, 50 quarters ("prices high" r = ${D.tierc.r_opus_q_prices}); not independent, as it learned from Opus`, C.accent2],
  ["0.48 → 0.59", "cross-validated tone F1 from 450 to 3,811 training labels: more labels, better", C.accent1],
], "tierc");
takeaway(s, "Low training error, good on topics and relevance, weakest on tone, and it agrees with Opus over time.");
s.addNotes("Backup slide. Tier C is a TF-IDF plus logistic regression classifier. Input: the text of one headline or post. " +
  "Output: a label. It learned from 8,173 items Opus had labelled; the 450 gold items were never used. On its own training " +
  "labels it scores 0.86 to 0.96, so the training error is low. On items it has not seen it scores 0.59 to 0.85 in " +
  "cross-validation and 0.61 to 0.88 on the gold set: good on relevance and topics, weakest on tone. More labels help. And by " +
  "quarter its net negativity correlates 0.64 with Opus's own series, so it gives the same answer over time.");

// ---------- 17. backup: the project as a flowchart
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
s.addText("Backup: the project from brief to hand-in", { placeholder: "title" });
const flow = [
  ["The question", "Why is Michigan sentiment far below the economy before the midterms? H1 pressures, H2 media, H3 measurement; RQ1 to RQ6.", C.accent4],
  ["Plan before tests", "Plan checked by verification agents; tests, signs and falsifiers pre-registered before any model, coding or test.", C.accent6],
  ["Data", "Economy as published by day 14 of each month (ALFRED); 602,189 headlines from 34 outlets; 50,926 Reddit posts.", C.accent5],
  ["Measuring", "Codebook with benchmarks; Claude Opus labels 9,373 items blind; Tier C, trained on Opus labels, scores every headline.", C.accent2],
  ["Testing", `Economy-only model: 2026 gap ${minus(D.gap2026.toFixed(1))} index points, ${D.share_explained.toFixed(0)}% of the fall explained. Bias, impact, forecast and falsifier tests.`, C.accent3],
  ["Building", "Figures, dashboard, this deck, the 12-page report and the notebook, all rebuilt from the saved outputs.", C.accent1],
  ["Checking", "Fresh reviewer agents recompute every number; each fix is a recorded note, then everything after it is rebuilt.", C.accent6],
  ["Validating the coder", `Answer key: Sonnet and Haiku passes plus my corrections, Fable settles ${D.n_disputed} items. Opus macro-F1 ${D.f1_opus_range[0].toFixed(2)} to ${D.f1_opus_range[1].toFixed(2)}.`, C.accent2],
  ["Hand-in", "Report, deck and repo; the dashboard's update plan covers data after the Oct 12 cutoff.", C.accent4],
];
const BW = 3.55, BH = 1.4, GX = 0.725, GY = 0.25, X0 = 0.6, Y0 = TOP;
const pos = (k) => { const r = Math.floor(k / 3), c = k % 3; return { x: X0 + (r === 1 ? 2 - c : c) * (BW + GX), y: Y0 + r * (BH + GY), r }; };
flow.forEach(([title, body, col], k) => {
  const { x, y } = pos(k);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: BW, h: BH, rectRadius: 0.08, fill: { color: C.background2 },
    line: { color: "D5DBE3", width: 0.75 }, objectName: `flow_${k + 1}_box` });
  circleLabel(s, x + 0.15, y + 0.12, String(k + 1), col, `flow_${k + 1}`, 0.4, 13);
  s.addText(title, { x: x + 0.65, y: y + 0.08, w: BW - 0.8, h: 0.48, bold: true, fontSize: 15, color: C.text1, valign: "middle",
    margin: 0, isTextBox: true, objectName: `flow_${k + 1}_title` });
  s.addText(body, { x: x + 0.18, y: y + 0.58, w: BW - 0.36, h: BH - 0.64, fontSize: 11, color: C.text2, valign: "top",
    margin: 0, isTextBox: true, objectName: `flow_${k + 1}_body` });
});
const arrow = (o, name) => s.addShape(pres.shapes.LINE, Object.assign({ line: Object.assign({ color: "7A8699", width: 1.75 }, o.line) }, o.box, { objectName: name }));
for (let k = 0; k < flow.length - 1; k++) {
  const a = pos(k), b = pos(k + 1);
  if (a.r !== b.r) arrow({ box: { x: a.x + BW / 2, y: a.y + BH + 0.03, w: 0, h: GY - 0.06 }, line: { endArrowType: "triangle" } }, `flow_arrow_${k + 1}`);
  else if (b.x > a.x) arrow({ box: { x: a.x + BW + 0.1, y: a.y + BH / 2, w: GX - 0.2, h: 0 }, line: { endArrowType: "triangle" } }, `flow_arrow_${k + 1}`);
  else arrow({ box: { x: b.x + BW + 0.1, y: a.y + BH / 2, w: GX - 0.2, h: 0 }, line: { beginArrowType: "triangle" } }, `flow_arrow_${k + 1}`);
}
takeaway(s, "Rules first, tests second, checks last; anything added after the main results is marked exploratory.");
s.addNotes("Backup slide. It shows the order of the work: the brief, a plan that was checked and pre-registered before any " +
  "data, real-time economic data and the media corpus, the AI measurement and Tier C, the tests behind each research " +
  "question, the deliverables, a checking round by fresh reviewers whose fixes were logged and rebuilt, and then the answer " +
  "key that grades the coder: Sonnet and Haiku labelled every item separately, I corrected labels I disagreed with in both, " +
  "and Fable settled the items where they still differed. The answer key only grades the coder, so it could not shape the findings.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  const applyPath = process.env.APPLY_THEME;
  if (applyPath && fs.existsSync(applyPath)) {
    const { applyTheme } = require(applyPath);
    await applyTheme(OUT, THEME);
  }
  // keep the build time out of the file's properties
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
  const core = await zip.file("docProps/core.xml").async("string");
  zip.file("docProps/core.xml", core.replace(/\s*<dcterms:(created|modified)[^>]*>[^<]*<\/dcterms:\1>/g, ""));
  fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log("wrote", OUT);
})();
