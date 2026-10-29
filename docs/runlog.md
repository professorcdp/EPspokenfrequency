# Runlog

Newest first. One entry per working session: what changed, which issues it touched,
and what comes next. The CHANGELOG records what shipped; this records what happened.

## 2026-10-28 (night, later) — how Davies actually built his corpus

#14 is settled from the source rather than inferred. Jim checked the
introduction to Davies & Preto-Bay (2008) — Table 1 and pp. 2, 6–8 — and the
answer is recorded in the issue. The scan is his privately and **stays out of
this repository**, page images included; only the facts are written down.

Three things we had wrong or had never established:

- **The spoken register is 10% of the corpus, not a quarter.** 2.0M words of
  20M, and only 1.0M from Portugal. That million is 0.437M of recorded
  informal conversation (CORDIAL-SIN, CRPC, Português Falado) and 0.563M of
  **interviews transcribed in newspapers and magazines**, screened for
  colloquial forms such as *pra*. Broadcasts are not mentioned anywhere, so
  the essay must stop implying them.
- **The registers are not balanced.** Fiction, newspaper and academic are 6M
  each; spoken is 2M. Each is half Portugal, half Brazil, nearly all of it
  1970–2000 and mostly the 1990s.
- **Davies does not rank by frequency.** Each register is weighted equally
  whatever its size, and within a register the score is half log frequency and
  half range — the spread across 100 blocks of 200,000 words. An evenly
  distributed word can outrank a commoner one. The ±s/f/n/a flags are
  relative too: top or bottom 10% of a register against the others.

`README.md` claimed his corpus was "balanced across registers", which is
simply false, and said nothing at all about how he orders entries, which left
a reader free to assume frequency ranks. The comparison table now carries the
real proportions and a new **Ordering** row, and a paragraph under it spells
out that his spoken register is mostly interview speech reaching him through
print while this list is dramatic dialogue end to end — so a disagreement
between the two lists is usually that difference in kind, not an error.

This strengthens the essay (#18) rather than threatening it. Its thesis — that
the subtitle list tracks Davies's fiction register (0.73) better than his
spoken one (0.55) — now has a documented mechanism behind it instead of a
guess.

Issues touched: #14 (closed).

**Next:** the essay itself, #18.

## 2026-10-28 (night) — v1.1.0 released

Tagged and published. `v1.1.0` is an annotated tag on commit `3c502e2`, the
commit that filled today's date into the CHANGELOG heading where
"(unreleased; date filled in at the tag)" had stood since the notes were
drafted. Main and the tag are pushed; the three commits that had been sitting
unpushed — the release assets, the #22 paradigm fix, the reviewer's sign-off —
went up with it, and #22 closed on the push as its commit message said it
would.

The GitHub release carries **five** assets: `EP_Spoken_Frequency.apkg`, the
two list TSVs, `glosses.tsv` and `SHA256SUMS.txt`. The notes are the
CHANGELOG's 1.1.0 section with the import warning lifted to the top as a
quoted block, because anyone holding the 1.0 deck has to delete all twenty of
its decks before importing and that must not be something they find in
paragraph forty. v1.0.0 was not touched: still three assets, still its
original publish time.

Verified rather than assumed. Before the tag: working tree clean, 358 tests
passing, `out/SHA256SUMS.txt` checking out against the committed `out/` files.
After the release: all five assets downloaded again from GitHub into an empty
folder, `shasum -a 256 -c SHA256SUMS.txt` returning OK on all four, and each
downloaded file compared byte-for-byte against its committed copy. The reason
for the belt and braces is that a private project now pins `glosses.tsv` from
this tag and verifies it by SHA-256, so the published hashes are a contract.

Also opened **#24** (chore, priority: later): the gloss cache keeps one
response per lemma+pos, so a re-ask overwrites the original with no history
anywhere. That is what let the 2026-10-28 incident destroy 379 original
responses, 86 of them on rows a native speaker had passed a verdict on.
Nothing published was lost, because the repair republished from
`out/glosses.tsv` — but the cache cost $24.95 and should not be destructible
by a routine re-ask. The issue proposes keeping superseded responses, either
appended inside the file or moved to a `superseded/` sibling, and explicitly
does not fix it now.

#13 is closed. Issues touched: #13 (closed), #22 (closed on push), #24 (new).

**Next:** nothing is announced. Whether anyone is told about v1.1.0 is #19,
and the Substack essay is #18. The deferred `jurar` bug is #23.

## 2026-10-28 (evening) — the reviewer signed off `dever` as a verb

The one gap the #22 fix left is closed. `dever` (verb) — "must; should; to
owe", *Deve estar tudo escondido.* — was sent to the native-speaker teacher
and came back approved, so `eval/gloss_review.tsv` records `good` for it and
the top 500 is **500 of 500 again: 479 good, 20 fix, 1 wrong**. The deck's
`gloss::reviewed` tag is back to 500, verified by reading the shipped `.apkg`.

This is the only verdict in the file with no raw paste behind it: rounds one
and two have `gloss_review_round2_raw.txt`, this one arrived on its own and was
entered by hand. `eval/README.md` says so, rather than letting it pass as part
of round two. Her original verdict, given on `dever` as a *noun*, stays in the
round-two raw text, and the noun example she wrote stays commented out in
`gloss_overrides.tsv`.

Nothing else moved: ser/ir fingerprint unchanged, gold 98.49%, every fatal
gloss gate passing, 358 tests.

## 2026-10-28 (later) — `dever` fixed, and a cache re-key that cost $1.69

**Fixes #22.** The POS column now reads the whole paradigm
(`fixes.paradigm_verb_pos`): a lemma the bare-infinitive test rejects still
counts as a verb when its VERB/AUX tags come from at least four distinct
inflected surfaces sharing its stem. The stem rule is what keeps `mar`, whose
stem is the single letter `m`, from collecting `mando` and `marque`. The test
can only add a verb reading, and it is used for the POS column alone, so
lemma resolution and the ser/ir split do not move — the rebuilt published map
came out **byte-identical** to the old one and the ser/ir fingerprint is
unchanged.

Six rows moved and nothing else: `dever` noun 68 → verb 68, `jantar` and
`colar` and `tremer` each split into noun + verb, `dorme` intj → verb,
`dormias` noun → verb. Exactly three counts changed, each losing precisely
what its new verb row gained. `presunção`, `bipolar` and `cicatrizar` were
pushed off the foot of the list by the three new rows; the other 7,083
differences are pure rank displacement. `dever` does **not** split — the noun
is 1.9% of its occurrences, far under `pos.split_min_share` — so the ~26,600
uses of *o dever* sit inside the verb row, and `colher` keeps one noun row for
the same reason at 24.5%. Jim chose to drop the reviewer's `dever` noun
override rather than force a split; it is commented out in
`eval/gloss_overrides.tsv`, to be restored verbatim if a noun row returns. The
top 500 is now **499 reviewed: 478 good, 20 fix, 1 wrong**, with `dever` (verb)
the one unchecked entry. `dever` (verb) glossed "must; should; to owe".

**The expensive part.** Adding one key under `fixes:` re-keyed
`published_map_path()`, whose digest covers `cfg["fixes"]`. The build that
would have written the map for the new digest had aborted inside
`build_apkg.py` on a missing gloss, so no map existed, and `Sentences` quietly
fell back to a lemma map that misses merged entries. That changed the
sentences offered to **every** row, and the sentences are part of the cache
stamp — so `--retry` set off to re-ask all 10,000. Jim stopped it at 379
completed calls, **$1.69**. The diagnosis that rank and frequency re-key the
cache is wrong: they are in the request but deliberately not in `stamp_for`,
which is now pinned by tests.

Those 379 responses **overwrote** their originals — the cache filename is
keyed on lemma + pos with the stamp inside — and 223 of them held a different
answer from what was published, 86 on rows carrying a native-speaker verdict.
Nothing published actually changed: `out/glosses.tsv` never moved, and after
the repair a full regeneration altered **zero** rows, reviewed or otherwise.
The 379 stay in `cache/gloss/`, unused: the published row wins over them.

Three defences, all tested. A missing published map is now a fatal error in
`scripts/gloss.py` instead of a silent fallback. `build_apkg.py` records a
missing gloss in `emit.MISSING_GLOSSES` rather than raising, as `emit.py`
already did, so a build always writes the deck, the reports, the published map
and `SHA256SUMS.txt` before failing — the same mid-build abort the 2026-10-23
review caught in one file and missed in the other. And `gloss.reuse_published`
republishes the existing row when a stamp moves under an unchanged entry,
counted as a `reused` gate (377 rows this run) and never silent. A new
`--plan` lists what `--retry` would send, without calling the API; the final
retry was 4 rows and $0.03.

Issue #23 opened for `jurar` (rank 618, published as a noun because two stray
votes on `juro` carry 65,701 occurrences). Left for a later release: every fix
for it reaches into lemma resolution. 358 tests pass.

## 2026-10-28 — `dever` diagnosed, pairs checked, glosses added to the release assets

Three things for the downstream project that wants to pin our glosses, and one
bug found doing it.

`dever` publishes at rank 68 as a noun with the verb's frequency. The cause is
`verb_lemmas` in `scripts/pos.py`, which decides verb-ness from the bare
infinitive alone: `dever` as a surface is tagged NOUN 43 times to VERB 7,
because *o dever* is what a bare `dever` usually is, so the lemma is marked
nominal and all **857 VERB votes across 36 inflected surfaces** are vetoed.
Nothing survives but 48 noun votes, so the entry cannot even split. Same family
as the `são` bug: a correct tag thrown out by a consistency rule. 24 siblings
exist; sorted by how many distinct surfaces lost votes, only five have a real
paradigm behind them and thirteen are genuine nouns where the rule works. A
second mechanism turned up alongside — `jurar` (618), where the dominant surface
`juro` keeps two stray votes that carry 65,701 occurrences. Issue #22 has the
cause, the sibling counts and the cost; **not fixed, Jim decides before the tag.**
A fix in `pos.py` does not re-key the ser/ir digest, so no rescore, but it can
still move the fingerprint if it touches `verb_lemmas`.

Checked 81 lemma+POS pairs the other project needs: 80 exactly as asked, the one
exception being `dever`. Between v1.0.0 and now, 240 pairs differ — 120 gone, 120
new, which is precisely the 120 notes Jim's Windows import added over 1.0. They
are 62 contraction retags, 51 glued-enclitic rows dropped, 4 other drops, and 58
new tail lemmas.

`out/glosses.tsv` joins the release assets, and `out/SHA256SUMS.txt` now covers
all four. The build writes the sums after the assets exist, so they describe what
the pipeline produced rather than what someone pasted in; `output.release_assets`
in `config.yaml` says which files count. Five tests, 311 passing.

Nothing tagged, nothing released, nothing pushed.

## 2026-10-24 — Three decision records, and an honest line about losing history

Documentation only. The CHANGELOG's import entry said the note type had two new
fields; it has one. Its claim that nothing is lost by deleting the 1.0 decks was
wrong — the review history on them goes, and there is no way to carry it across
a changed note type. It now says so, and says that 1.0 was never announced, so
few people if any are affected.

Decision records 0012 (the field list is frozen), 0013 (no field for the
learner's own notes) and 0014 (a package timestamp per release) record what the
review settled, each with what it costs.

## 2026-10-23 (review)

**Reviewed:** 9257dff..464adf0

**Verdict:** one must-fix, and it was right. The deck shipped a `My_Notes`
field for the learner's own writing together with a package timestamp frozen
at 2026-09-22. Anki writes that timestamp as every note's modification time
and "Update notes: If newer" compares against it, so the frozen value made
"If newer" a no-op — no correction could ever reach anyone — while "Always"
would erase whatever a learner had typed. The field could not be kept safe
either way.

**Findings:**

1. (must) `My_Notes` plus the frozen timestamp — a field we invite people to
   write in that a later release silently overwrites, and a deck that cannot
   be corrected at all. The 1.0.0 CHANGELOG had deferred exactly this to 1.1.
2. (should) `emit.py` exited mid-build on a missing gloss, leaving the later
   lists, the deck and every report unwritten.
3. (should) `scripts/README.md` still said the build neither reads nor writes
   `out/glosses.tsv`; it reads it, and `eval/gloss_review.tsv` too.
4. (should) `override-english` rows carried no Portuguese, so the reviewer's
   English was paired with whatever the cache happened to hold.
5. (could) The `de` override read "written by hand" though its example is the
   model's corpus line, and `eval/README.md` said such rows have no example.
6. (could) A test used `tempfile.mkdtemp()` and never cleaned up.
7. (could) The "no gloss" errors told the reader to run `--report`, which
   cannot help an entry that has never been glossed.

**Fixed:** all seven.

1. Checked Anki's documented import rules first. Because Anki cannot merge
   fields, and because a note type the learner has changed stops being
   updated at all, there is no arrangement in which a shipped field is safe
   for their writing. `My_Notes` is removed, and the CHANGELOG says how to add
   your own field and what it costs. The timestamp is now one per release
   (1.1.0 = 2026-10-23), pinned in config so the build stays reproducible,
   with `previous_timestamps` and a test that a release never reuses one.
2. Missing glosses are collected in `emit.MISSING_GLOSSES` and `build.py`
   fails on them at the end, beside the quality gate, so the reports are
   written first.
3. Corrected.
4. The four rows now record their Portuguese, `apply_override` checks the pair
   matches (after tidying, since the file holds the sentence as a reader sees
   it), and a new fatal gate `override_pair` counts any that do not. It caught
   two on its first run — both the subtitle dash, which is what showed the
   comparison needed tidying rather than the data needing changing.
5. The label is now "gloss settled by hand" and `eval/README.md` says these
   rows leave the example alone, whatever it is, including none (`caseiro`).
6. Uses `tmp_path`.
7. The messages now say that a never-glossed entry needs `--retry` and an API
   call, and that `--report` is enough only when a rebuild moved an entry.

**Deferred:** nothing.

Deck rebuilt: 10 fields, 10,000 notes, 20,000 cards, 5.9 MB. Every list, count
and rank byte-identical to before the review. 306 tests pass. Closes #11.

## 2026-10-23 — The glossed deck (#11)

All 10,000 notes carry their gloss, so every one now has a reverse card: 20,000
cards against 1.0.0's 10,000, and 5.9 MB against 3.5 MB. `My_Notes` and
`Gloss_Source` are added at the end of the note type, which is frozen from here
— Anki matches fields by position, so another change would break re-import.

Snapshotted `out/` and `reports/` first and diffed after: the only files that
moved are the `.apkg`, the two *enrichable* TSVs and the deck's byte count in
`build_stats.json`. Every list, count and rank is byte-identical, and the
*minimal* TSVs are untouched.

Tags: everything 1.0.0 set is still set, plus `flag::` per gloss flag and
`gloss::reviewed` on the 500 reviewed notes. Four new tests read the shipped
`.apkg` itself rather than a fixture, so the artifact is pinned and not just the
code that writes it. 302 tests pass.

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
