# Runlog

Newest first. One entry per working session: what changed, which issues it touched,
and what comes next. The CHANGELOG records what shipped; this records what happened.

## 2026-10-23 — Two corrections to the round-two write-up

Documentation only. The CHANGELOG had said she went back over the rest of the top
500 in round two; she did not. Of the 498 lines, 245 were round-one answers her
browser still held and copied out again, and only 253 were new. The override
paragraph described two kinds and thirteen rows, which the merge left behind: it
now describes the 29 rows in four kinds and says where each row's English came
from. `eval/README.md` had no account of the override kinds at all, so it gained
a short one, including `override-english`.

## 2026-10-18 — Round two merged; the top 500 is reviewed (#7, #8, #9, #10)

Her round-two answers arrived and are saved verbatim in
`eval/gloss_review_round2_raw.txt`, committed on its own before anything parsed
them. 512 lines, all parsing: 498 verdicts (476 good, 21 fix, 1 wrong) and 13
confirm answers (12 ok, 1 corrected). Nothing in the optional band below rank 500.

**The top 500 is now reviewed in full: 500 of 500 — 478 good, 21 fix, 1 wrong.**
The two rows without a round-two line already carried a round-one verdict and
correctly showed as done on the page.

Her `note` field carried three different things, settled with Jim before merging
rather than guessed at. Six "fix" lines were round-one state resurfacing — the
page sets the verdict to "fix" when a sentence is clicked, and her browser still
held the old answers — so those recorded a verdict and changed nothing else. Four
notes were corrected English, which the merge rules did not cover; they became a
new kind of override that replaces the translation while the Portuguese stays the
corpus line (`override-english`, and `apply_override` had to learn to do that).
Five notes were corrected Portuguese and became `override-edited`, including
`trás`, where she put back the accent the subtitle had dropped, and `dever`, which
had no example at all until she supplied one.

Overrides are now 29 rows. Gates pass, 294 tests pass, nothing regenerated through
the API.

## 2026-10-15 — Her first-round answers carried in the page (#7)

The review page no longer depends on her opening it in the same browser. Each row
now carries the verdict she gave in round one — 247 of them, being the 257 in
`eval/gloss_review.tsv` less the ten re-opened — and `st()` falls back to it when
the browser has nothing stored, so the filters, the progress bar and "Jump to first
unreviewed" all count those rows as done. On a fresh browser the bar opens at 247
of 500, with 253 left: the 243 she never saw plus the ten that changed.

Copy answers is unchanged and still reads the browser's own store, so an embedded
verdict is never copied back as though she had just given it. If she re-rates one
of those rows, her new answer is stored and copied as usual.

One repair alongside: a row marked Good never showed a coloured edge, because the
script writes the class `v-good` while the stylesheet only knew `v-ok`. Barely
visible before; with 243 rows now opening as good it would have looked as though
nothing was marked.

## 2026-10-15 — Gloss review page, round two (#7, #8, #9)

Republished the tutor's "Gloss Check for Learners" page to the same URL, so her
link and the answers saved in her browser keep working. 700 rows refreshed from
the current glosses, ten re-opened with an Updated chip because their text changed
after she rated them, and a new "Your sentences" section with the thirteen examples
she chose or edited, for her to check the English we wrote for them.

Counting against the previous page: 33 rows changed, 10 of them never reviewed and
23 already carrying a verdict. Of those 23, thirteen are her own edits and seven
were already flagged, which leaves three that nobody had noticed — `encontrar`,
`deste` and `pegar`. Issue #8 said eight rows; the real number is ten.

Two small repairs on the way through: the Find box had never filtered anything, and
two offered sentences carried an undecodable byte from the corpus, which would have
shown as a black diamond on a card had she picked one. No published gloss is
affected.

## 2026-10-04 — Decision records, and a label for Jim's own tasks

Wrote the eleven decision records skipped during the adoption, one per paragraph of
the "Decisions" section of `docs/context-from-cowork.md`. Two are not settled and
say so rather than reading as decided: 0006 cannot confirm whether the reviewer was
offered named credit, and 0011 is open because Jim has not decided it (issue #15).
Only 0001 carries a date from the note itself; the rest say they are undated, with a
commit date from git history where one pins the decision.

Added the `jim` label and applied it to the ten issues only he can do — #7, #8, #9,
#12, #18 and the five questions — so `gh issue list --label jim` is his own list.

## 2026-10-04 — Adopted 2nd brain workflow

Added `PROJECT.md`, `CLAUDE.md`, this runlog and `docs/decisions/`, and set up
GitHub Issues for tracking: the seven type and priority labels, and issues #7-#21
covering the next steps and open questions carried over from the Cowork advisor.
Nothing existing was changed apart from four safety lines appended to `.gitignore`.
No decision records written yet; the template is in place for them.

The retired Cowork advisor's handover note was committed first, as
`docs/context-from-cowork.md` (commit `6799387`), with the links to Jim's claude.ai
pages removed because this repository is public.

Next: ask the tutor for her second pass on the 243 remaining top-500 gloss rows,
then fold her answers in before rebuilding the deck with glosses and tagging
v1.1.0.
