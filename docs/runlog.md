# Runlog

Newest first. One entry per working session: what changed, which issues it touched,
and what comes next. The CHANGELOG records what shipped; this records what happened.

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
