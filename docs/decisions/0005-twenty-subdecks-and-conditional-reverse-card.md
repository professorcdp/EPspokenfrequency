# 0005 — Twenty subdecks of 500, and a reverse card only once there is a gloss

**Date:** not dated in the handover note; the deck was restructured on 2026-09-23
(commit `92939db`)
**Status:** accepted

## What was decided

The Anki package holds twenty subdecks of 500 words rather than two of 5,000. The
English-to-Portuguese card is wrapped in a condition on the gloss field, so it only
exists for words that have a meaning filled in.

## Why

Learners work through the list in frequency order, and a 5,000-card deck is hard to
pace. A reverse card with a blank front is useless, so Anki is told not to make one.

## What it costs

Twenty decks are more to scroll past in Anki's deck list. The card templates are
also harder to reason about, because whether a note has one card or two depends on
its contents.
