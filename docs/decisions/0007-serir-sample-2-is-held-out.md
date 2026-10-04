# 0007 — ser/ir sample 2 is held out and the rule may not be tuned on it

**Date:** not dated in the handover note; sample 2 was added on 2026-09-22
**Status:** accepted

## What was decided

For the seven disputed rows of sample 1, Jim accepted the advisor's and the LLM
informant's labels. Sample 2, labelled by the native-speaker teacher (99 of 100
rows, one abstention), is the held-out test set, and the *ser*/*ir* rule may never
be tuned against it.

## Why

A rule tuned on the set used to score it reports its own training accuracy, which
means nothing. Keeping one sample untouched is what makes the published figure an
honest estimate.

## What it costs

A known weakness cannot be fixed with the best evidence available for it: the rule
mistakes *lá fora* for a destination, visible in sample 2, and any fix has to be
validated on a fresh sample instead. It also means the honest held-out score
(93.2%) is lower than the development score (95.9%), which looks worse in the
README.
