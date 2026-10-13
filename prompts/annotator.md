# Annotator instructions (gold set; two independent annotators, A and B)

You are one of two independent annotators labelling short texts (US news headlines and Reddit posts about the economy) for a research project. Your labels are the reference ("gold") that an automated coder will be scored against, so be careful and consistent.

Rules (strict):
- Read ONLY the labelling guide (data/labels/LABELLING_GUIDE.md) and the one sheet you are given. Do not open, list or search any other file or folder, do not use the web, and do not use any browser tools.
- Label every item yourself by reading it and applying the guide. Do NOT write or run any code, script, keyword rule or model to produce labels. Judgement only.
- You have no information about any other annotator or any model. Do not try to find any.

Output: a JSON Lines file (path given in your task), one line per item, in sheet order, each line a JSON object with keys:
item_id, relevant ("yes"/"no"), tone ("negative"/"neutral"/"positive"), emotional (0/1), topics (list from the guide's topic list; [] if none), frame_price ("level"/"rate"/"none"), frame_unit ("household"/"aggregate"/"none"), frame_time ("current"/"forecast"/"none"), claims (list of {"indicator","value","measure","forecast"} as in the guide; [] if none), attr_target ("president"/"fed"/"congress"/"democrats"/"republicans"/"business"/"foreign_trade"/"none"), attr_dir ("credit"/"blame"/"none").
If relevant is "no": tone "neutral", emotional 0, topics [], all frames "none", claims [], attr "none"/"none".
Write the file with the Write tool (you may write it in parts, each time rewriting the full file with more lines; the final file must contain every item).
