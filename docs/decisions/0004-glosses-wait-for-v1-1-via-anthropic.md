# 0004 — Glosses wait for v1.1 and are generated through the Anthropic API

**Date:** not dated in the handover note; the glosses were generated on 2026-09-25
**Status:** accepted

## What was decided

Three things, recorded together in the handover note. The English glosses and
example sentences wait for v1.1 rather than holding up v1.0. They are generated
through the Anthropic API rather than OpenAI. The API key lives only in Jim's
`~/.zshrc` as `ANTHROPIC_API_KEY`: it is never written into the repository and the
full key is never pasted into a chat.

## Why

v1.0 was complete as a frequency list without glosses, and waiting would have
delayed it for weeks. Keeping the key in the shell profile means no code path can
read it from a file that might be committed by accident.

## What it costs

v1.0 shipped with empty gloss fields and therefore no reverse flashcards, which the
CHANGELOG lists as a known issue. The glosses cost $24.95 to generate and are one
model's answers on one day rather than a reference work, so unlike the lists they
are not reproducible byte for byte.
