# Adjudicator instructions (gold set)

Two annotators labelled the same texts with the labelling guide and disagreed on at least one field for each item in your sheet. You decide the final label for every field of every item.

Rules (strict):
- Read ONLY the labelling guide (data/labels/LABELLING_GUIDE.md) and the one adjudication sheet you are given (JSON Lines: item_id, text, label_1, label_2; the two labels are in random order and you are not told who made which). Do not open any other file, do not use the web, do not use browser tools, and do not write or run code.
- For each item, read the text and the guide, then give the final label for ALL fields. You may pick label_1's value, label_2's value, or (rarely, only if both are clearly wrong under the guide) a third value. Add a one-line "reason" naming the field(s) you decided and why.

Output: a JSON Lines file (path given in your task), one line per item in sheet order, with keys item_id, relevant, tone, emotional, topics, frame_price, frame_unit, frame_time, claims, attr_target, attr_dir, reason (same value rules as the guide; if relevant is "no", tone neutral, emotional 0, topics [], frames none, claims [], attr none/none).
