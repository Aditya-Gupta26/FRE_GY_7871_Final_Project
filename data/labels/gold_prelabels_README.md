# Gold pre-labels: Sonnet 5.5 (pass A) and Haiku 5.5 (pass B)

How the files `gold_prelabels_sonnet_part{0-4}.jsonl` and `gold_prelabels_haiku_part{0-4}.jsonl` were made.

- **Why:** I couldn't find other people to annotate. So each annotator pass is one model's labels plus my corrections (see below). The two models are different from the Opus coder being validated, and each ran in its own separate context.
- **Models:**
  - Pass A: Claude Sonnet 5.5 (`claude-sonnet-5-5`).
  - Pass B: Claude Haiku 5.5 (`claude-haiku-5-5`).
  - Each run reported its model ID itself.
- **Prompt:** `prompts/annotator.md` (sha256 prefix `d5761cf7e12ef2ba`). The only change is that the guide's path points to the copy in each run's folder. The guide is `LABELLING_GUIDE.md` v1.1, unchanged.
- **Isolation:**
  - Ten separate runs: five per model, one per 90-item sheet part.
  - Each run had a folder holding only the prompt, the guide and its own sheet (item ids and text, no date, no outlet).
  - Each run was told not to open anything else. No run saw another run's labels or the Opus coder's codes.
  - Labels were by judgement only, with no code or keyword rules. One Sonnet run used a shell command only to write its file and count the lines.
- **Checks:** all 900 labels passed `src.coded.validate`, complete and in sheet order, with no re-sends.
- **Agreement before my corrections**, Sonnet vs Haiku over the 450 items:
  - Cohen's κ:

    | Field | κ |
    |---|---|
    | relevant | 0.74 |
    | tone | 0.76 |
    | emotional | 0.89 |
    | price frame | 0.87 |
    | unit frame | 0.57 |
    | time frame | 0.72 |
    | attribution target | 0.76 |
    | attribution direction | 0.78 |

  - 177 of 450 items differ on at least one field.
  - Sonnet marks 44.9% of items relevant and Haiku 57.3%.
- **My corrections:** 12 items in pass A and 15 in pass B, each with its reason, in `data/labels/human/human_verified_{A,B}.jsonl` (the review tool is `data/labels/human/review_tool.html`, built by `scripts/06d_human_label_tool.py`). The files record the corrected items only. Every other label stays as the model gave it (`src/gold.py` combines them).
- **Adjudication:**
  - After my corrections the passes still differed on 163 items. `scripts/06c_make_adjudication.py` wrote them out with the two labels in seeded random order and no names.
  - Claude Fable 5.1 (`claude-fable-5-1`; `prompts/adjudicator.md`, sha256 prefix `e9d71867980ee338`) decided each one. It ran as two separate subagents (90 and 73 items), each seeing only the prompt, the guide and its sheet. The output is `gold_adjudicated_{0,1}.jsonl`, with a reason per item.
  - On the second sheet the adjudicator first treated single-employer job news as relevant, citing the guide's tone example. It was asked to recheck those items against the guide's relevance rule ("a single company's news with no wider economic point" is not relevant): five changed to not relevant, and one stayed relevant because its text ties the closure to the federal layoffs.
  - Final adjudication: pass A's label on 94 items, pass B's on 55, a mix of the two on 11, and on 3 items a value neither pass had.
- **Agreement after my corrections** (pass A vs pass B, κ): 0.60 to 0.90. That's higher than before because one person corrected both passes, so the report uses the figure before my corrections, above.
