# EP Spoken Frequency

**Stamp:** business
**Started:** 2026-09-12 (this repository; an earlier unpublished list from April 2026
is archived at tag `v0-april-2026`)

## Overview

A word-frequency list of spoken European Portuguese, built from the Portugal-tagged
half of the OpenSubtitles 2018 corpus — 118 million lines of film and television
subtitles, 637 million words. The published list is the 10,000 commonest entries,
ranked, with a part of speech, a raw count and a rate per million. It ships with a
ready-to-import Anki flashcard deck of twenty 500-word subdecks.

The point of it is that existing Portuguese frequency lists are either Brazilian,
built from writing rather than speech, or both. This one is dialogue only and
European only, which makes it a useful complement to Mark Davies's dictionary
rather than a replacement — Davies is edited and peer-reviewed; this is a
hobbyist's subtitle list, and the README says so plainly.

The repository is public under `professorcdp`. Code is MIT, data is CC BY-SA 4.0.

## Expected output

The ranked lists in `out/` (ranks 1–5000 and 5001–10000, as TSV and CSV), the Anki
package `out/EP_Spoken_Frequency.apkg`, and `out/glosses.tsv` — one English meaning
and one real corpus sentence per entry. Everything is rebuilt from the corpus by a
single command, and the same inputs produce byte-identical output.

A Substack essay comparing this list against Davies is drafted but lives outside
this repository, because the comparison draws on private reference data.

## Requirements

Must have:

- Every number reproducible from the corpus by `python -m scripts.build`, with no
  hand-editing of the published files
- Human decisions kept in `eval/` as files the pipeline reads, never as code edits
- A quality gate that fails the build on any unaccounted duplicate entry
- Honest documentation of what the list is not (inferred from the README's tone,
  which Jim set deliberately)

Nice to have:

- Example sentences taken verbatim from the corpus rather than invented
- Native-speaker review of the entries a learner meets first

## Assumptions

Subtitle dialogue is a reasonable stand-in for speech, with the distortions the
README lists. The tagger (Stanza) is right often enough to be worth using with a
dictionary check over it — measured at 98.5% on a hand-checked sample of 332 words.
Learners will study in frequency order, which is why the deck is split into bands
of 500.

## Out of scope

Not an academic corpus, not a dictionary, and not a course. No audio, no
pronunciation, no grammar notes. Brazilian Portuguese is filtered out rather than
marked. The Davies extraction stays in a separate private repository permanently.

## Open questions

1. How Davies describes his own spoken sub-corpus — the essay's central claim
   depends on it and nobody has checked it against his introduction. Must be
   settled before publishing.
2. Whether the 200 sampled gloss rows below rank 500 get human review: Jim, a third
   tutor pass, or not at all.
3. Whether to announce v1.0 to learners now or wait for v1.1 (Jim's call).
4. Whether a separate "methods" essay follows the comparison one.
5. Whether `nova`'s remaining 112,548 occurrences should move to `novo` — the tag
   vote that split them was 26–24, and the proper-noun side is inflated by
   *Nova Iorque*, which already has its own entry.

## Current status

v1.0.0 has been public since 2026-09-24 and is unchanged apart from the clone URL
after the repository moved to the `professorcdp` organisation.

Work since then is v1.1.0 preparation, described in the CHANGELOG's "Unreleased"
section: English glosses and corpus example sentences for all 10,000 entries
(generated in one batch run for $24.95), a native-speaker tutor's first-pass review
of the top 500, and a run of tokenizer and lemma fixes found along the way — glued
enclitic clusters, contraction parts of speech, `são` wrongly counted as a noun
instead of a form of *ser*.

Not yet done: the glossed deck. The deck in `out/` is still the v1.0 one with empty
gloss fields. The tutor's second pass (the 243 top-500 rows missed because of a
paging bug, now fixed) has not been requested yet, and the plan is to fold it in
before rebuilding the deck and tagging v1.1.0.
