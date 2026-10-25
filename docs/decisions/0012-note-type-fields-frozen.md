# 0012 — The note type's field list is frozen from 1.1.0

**Date:** 2026-10-23
**Status:** accepted

## What was decided

The Anki note type's ten fields — Rank, Lemma_PT, POS, Gloss_EN, Example_PT,
Example_EN, Is_MWE, Raw_Freq, Freq_per_million, Gloss_Source — are fixed from
1.1.0 onwards. Nothing is added to them, removed from them or reordered within
them again. Anything further goes in a new note type.

## Why

Anki matches a note's fields by position, not by name. Change the list and a
re-import no longer lines up with the notes a learner already has: Anki
generally stops updating them at all, so a later release adds new words but
leaves the existing ones untouched, glosses and corrections included.

1.1.0 is the release that adds the glosses, so it is the last point at which
the shape can change without cost — nobody can yet have review history on a
glossed deck. Freezing it here means every release after this one can actually
reach the people studying it.

## What it costs

Anything the deck might want later — audio, a hint field, a second
translation — cannot be added to this note type. It would need a new one, which
means a separate import and no shared history with this deck. That is a real
limit, accepted because the alternative is a deck that silently stops updating
for the people who use it most.

See [0013](0013-no-field-for-the-learners-notes.md), which is why there is no
field here for a learner's own writing, and
[0014](0014-a-package-timestamp-per-release.md), without which updates could
not reach anyone anyway.
