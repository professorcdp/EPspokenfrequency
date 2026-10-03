# Context from the Cowork advisor

Written 2026-10-03 by the Cowork advisor chat, which is being retired. The repository's own files (README.md, CHANGELOG.md, DATA_SOURCES.md, eval/README.md, reports/) are the record of *what was built and why*; this file holds only what is not in them: the working arrangement, where things stand, decisions that were made in conversation, and tasks only Jim can do. Items I could not verify from the files are marked **(unsure)**.

_Edited on 2026-10-03 before it was committed: the links to Jim's claude.ai pages were removed, and the description of the private repository's contents shortened, because this repository is public. Nothing else was changed._

## Overview

Two repositories, both now under the `professorcdp` GitHub organisation (transferred from `jamminalley` on 2026-10-02 per the latest README commit; I did not take part in the transfer).

`EPspokenfrequency` (public, MIT for code, CC BY-SA 4.0 for data) is the spoken European Portuguese frequency list built from the OPUS OpenSubtitles v2018 `pt` corpus, with the Anki deck. v1.0.0 was released 2026-09-24. Work since then is towards v1.1.0, whose headline is English glosses and corpus example sentences for all 10,000 entries, human-checked for the top 500.

`ptfreqlist` (private) holds the Davies reference data (`out/deck_master.tsv`, which may not be redistributed) and the `comparison/` package that compares Davies against the spoken v1.0.0 list. It stays private permanently; only aggregate numbers and a handful of ranks may be quoted in public writing.

The division of labour until now: Jim runs the coding work in a VS Code Claude Code chat (the "dev chat", Opus 5 model), pastes its reports here, and this chat acted as advisor — drafting prompts for the dev chat, reviewing its reports, building web review pages for human checks, maintaining a task tracker, and writing the Substack essay draft. The dev chat is the only one that commits. The replacement for this chat is a Claude Code `/advisor` session.

## Current status

v1.0.0 is public and unchanged since release except for the README clone URL. The post-release commits (through 5acb170, then the README URL fix 1732f51) are all v1.1 preparation and are described in CHANGELOG `Unreleased`.

The glosses exist for all 10,001 rows (`out/glosses.tsv`) and the native-speaker tutor's first-pass verdicts are applied (250 counted rows: 236 good, 13 fix, 1 wrong). The deck in `out/EP_Spoken_Frequency.apkg` is still the v1.0 deck without glosses. The last prompt I gave the dev chat asked it to *prepare* the glossed deck build ("Stage C": glosses, `My_Notes` and `Gloss_Source` fields, README and CHANGELOG 1.1.0 draft) without committing the deck or tagging, so that the tutor's second pass can be folded in first. Whether the dev chat finished that preparation I do not know **(unsure)** — check with it.

The tutor has reviewed 257 of the top 500 gloss rows. The remaining 243 were skipped because of a paging bug in the first review page (default "unreviewed" filter plus Next button skipped every other block of 40). The bug is fixed on the page; she has not yet been asked to do the second pass **(unsure whether Jim has contacted her)**.

The Substack essay ("Two Kinds of Spoken Portuguese") is drafted in a Claude Docs working document and awaits Jim's editing pass. The two Substack-styled figures exist as PNGs (`ptfreqlist/comparison/out/substack/`, also delivered in the chat as fig1_register_check.png and fig2_rank_scatter.png with @2x versions) and are marked in the draft by bracketed placeholders, not embedded.

## Decisions

Made in conversation, in roughly chronological order. Dates approximate to the week.

Mid-September: the April 2026 list was never publicised, so there are no compatibility obligations to it; it is archived as `v0-april-2026` and mentioned in writing only lightly ("before Fable came out"). Jim prefers to wait for a complete, right version rather than release early.

The spoken list is the priority; Davies is kept only for the comparison.

Licensing: Jim said he was "fine with the more restrictive licence", which became the MIT/CC BY-SA split.

Glosses wait for v1.1 rather than going into v1.0. Anthropic API chosen over OpenAI for gloss generation. The key lives only in `~/.zshrc` as `ANTHROPIC_API_KEY`; it is never in the repo and the full key is never pasted into a chat.

Anki deck: 20 subdecks of 500 rather than 2 of 5,000. Card 2 (EN→PT) is conditional on a gloss being present.

The tutor (a native-speaker Portuguese teacher) remains anonymous; credit only as "a native-speaker Portuguese teacher". She was offered named credit on the gloss review and has not asked for it **(unsure)**.

Ser/ir: Jim accepted the advisor's and the LLM informant's labels on the seven disputed rows of sample 1; sample 2 (tutor-labelled, 99/100, one abstention) is the held-out test set and the rule may not be tuned on it.

Lemmatisation conventions in `eval/conventions.md` were adopted on the advisor's recommendation ("I'll go with your recommendations").

Gloss review: a verdict recorded against an earlier gloss text does not count as reviewed (hence 250 not 257). Where the tutor supplied a Portuguese example without English, the English is written by us and the row's note says so.

Essay: open with the motivation (YouTube "ten words you need" videos, corpus linguistics, Davies as the gold standard), then the finding; charts restyled for Substack, orange `#FF6719` used for marks only, never for text, because it fails contrast.

On the 200 sampled gloss rows below rank 500 (optional for the tutor): the advisor recommended shipping v1.1 with human review on the top 500 only and saying so. Jim has not decided **(unsure)**.

## Open questions

How Davies describes his own spoken sub-corpus. The essay's thesis is that the subtitle list tracks Davies's *fiction* register (correlation with his `+f` flag 0.73) rather than his *spoken* register (`+s` 0.55). The draft infers how his spoken component was collected; nobody has checked this against the dictionary's introduction. It is an open comment in the essay doc and must be settled before publishing.

Whether to review the 200 sampled gloss rows (Jim himself, a tutor third pass, or not at all).

How re-imported tutor verdicts from pass 2 should be matched. The dev chat reordered `eval/gloss_review.tsv` after the review page was built, so verdicts must be matched by lemma + POS, not by row id. Eight rows whose gloss was regenerated between page build and import are flagged stale and should be shown to her again.

Whether to announce v1.0 to learners now or wait for v1.1 **(Jim's call)**.

Whether a separate "methods" Substack post follows the comparison essay (floated, not decided).

## Known issues

`_to_delete/` at the repo root is gitignored and holds temp files (`page_rows.json`) from the advisor's work; it can be deleted.

The advisor's commits from the Cowork sandbox left git lock files (`.git/HEAD.lock`, `index.lock`, `maintenance.lock`, `tmp_obj_*`) because the sandbox could not delete. They were removed in 5acb170; none are present now, but if the dev chat sees a stale lock, that is the origin.

The two `pt`-corpus residues the dev chat and tutor noticed: subtitle lines are deduplicated and interleaved, so adjacent lines are *not* reliably the same scene. Context shown on review pages therefore sometimes makes no sense; the tutor remarked on this. Any future page that shows context should say so.

Capitalised OCR errors such as `lgreja`, `lnglês` (lowercase L for capital I) exist in the corpus; they were checked and are not in the published list, but the pattern is worth a test if the tokenizer changes **(unsure whether a test exists)**.

The Anki launcher install failed once on Jim's Windows machine; choosing a specific Anki version rather than the launcher worked. Jim tests decks on Windows, not on his Mac.

Three stale local folders are mounted in Cowork: `Development--ptfreqlist` is the live private repo (origin professorcdp/ptfreqlist); `Portuguese--ptfreqlist` is the old Dropbox copy (origin jamminalley/ptfreqlist, last commit 840b363) and `ptfreqlist` is empty. The old Dropbox folder could be archived or removed so nobody works in it by mistake.

## Next steps

In order: (1) Jim asks the tutor for pass 2 on the "Gloss Check" page (243 remaining top-500 rows), and sends her the 13 English translations we wrote for her example sentences so she can confirm them. (2) Her pasted answers are merged by lemma + POS into `eval/gloss_review.tsv` and `eval/gloss_overrides.tsv`. (3) Dev chat applies them, runs Stage C, rebuilds the deck with glosses, `My_Notes` and `Gloss_Source`, updates README and CHANGELOG to 1.1.0, Jim imports the deck on Windows to test, then tag v1.1.0 and release. (4) Jim edits the essay, settles the Davies spoken-corpus question, inserts the two figures, publishes on Substack. (5) Optionally announce v1.0/v1.1 to learners and write the methods post.

## Jim-only tasks

Liaison with the tutor (WhatsApp; a Portuguese message template for the ser/ir round was provided and can be adapted), including any thanks or payment arrangement, which I know nothing about.

Testing Anki decks on the Windows machine.

Managing the API key and any further Batch API spending (the gloss run cost $24.95).

Editing and publishing the Substack essay; deciding on named vs anonymous credit if the tutor ever asks; deciding when to go public.

Approving each release (the dev chat drafts README/CHANGELOG; Jim approves before the tag).

Business-account work (GitHub `professorcdp`, Substack) happens in Jim's business Chrome profile.

## How I like to work on this project

This heading records what Jim asked for, as he stated it.

Always say where a shell command runs: which app (Terminal, VS Code dev chat) and which folder. This was a standing instruction after an early mistake.

Jim does not want to do review work inside VS Code or by editing TSVs; he prefers an HTML review page he can click through, with answers that can be copied out as text. Pages for Jim can use the artifact database; pages for the tutor use browser localStorage plus a "Copy answers" button producing one line per item (for example `g007 um fix | ex: ... | note: ...`), because she must not need an account.

Jim pastes the dev chat's reports into the advisor chat for a second opinion, and wants prompts for the dev chat written out in full, ready to paste.

Honest caveats over marketing: the README says this is a hobbyist's subtitle list, not an academic corpus; the essay says the same.

Prose rather than bullet lists in documents and essays; Jim edits drafts himself after a first draft is written for him.

Decisions about the tutor's time are Jim's; the advisor proposes the size of each round and Jim decides.

## Background worth keeping

Review pages built for this project, all under Jim's claude.ai account and listed in his artifact gallery (the links are deliberately not recorded here, because this repository is public and two of the pages are shared by link so the tutor can use them without an account): EP Spoken Frequency Tracker (task tracker, database-backed; ids `d…` for dev-chat tasks, `j…` for Jim's); Lemma Gold Review; Proper-Noun Filter Review; Ser or Ir Review (Jim's copy, sample 1); Ser ou Ir? (tutor's page, sample 2); Gloss Review (Jim's, db-backed); Gloss Check for Learners (tutor's page, 500 + 200 rows, localStorage, paging bug fixed); the essay draft "Two Kinds of Spoken Portuguese" (a Claude Docs document). These keep working after Cowork loses folder access; they do not depend on the repo.

Reviewer instruction documents delivered in the chat and not in the repo: `gloss_check_instructions.md` (for the tutor, English), `whatsapp_para_a_professora.md` (Portuguese and English message for the ser/ir round). The ser/ir informant prompt *is* in the repo (`eval/ser_ir_informant_prompt.md`).

The Davies comparison's central numbers for the essay: the spoken list correlates with Davies's fiction flag at 0.73 and his spoken flag at 0.55; fallers that carry `+s` are civic vocabulary (política, sociedade, literatura); climbers are interpersonal (querido, teu, desculpa, tu). The reading is "two kinds of spoken": broadcast/interview speech versus dramatic dialogue. Figures were made with `python -m comparison.compare --style substack` in the ptfreqlist folder **(unsure of the exact flag spelling; see comparison/charts.py)**.

The tutor's first-pass transcription into `eval/gloss_review.tsv` was done by the advisor from pasted WhatsApp text and one row (`g424 chefe good`) was dropped in transcription; all affected verdicts were "good", so nothing changed, but the raw paste is not in the repo. If pass 2 is pasted again, keep the raw text in `eval/` or `_to_delete/` before merging.

The 400-word lemma gold set was hand-labelled in this chat because the sandbox could not install simplemma; the labels are Jim's final word in `eval/lemma_gold.tsv`.

Davies register-flag extraction (`ptfreqlist/scripts/extract_flags.py`) reads the source PDF; neither the PDF nor `deck_master.tsv` may leave the private repo.

Memory notes about this project also live in Jim's Claude memory (`/areas/ptfreqlist.md`) and will be visible to the new advisor if memory is shared.
