# 0014 — Each release has its own package timestamp, pinned in config

**Date:** 2026-10-23
**Status:** accepted

## What was decided

`output.anki.apkg.timestamp` in `config.yaml` carries one value per release —
1.0.0 was 2026-09-22, 1.1.0 is 2026-10-23 — rather than one fixed value for
every release. Old values are listed in `previous_timestamps`, and a test
refuses a release that reuses one or that is not newer than the last.

## Why

genanki writes that timestamp as every note's modification time, and Anki's
"Update notes: If newer" compares it against the copy already in the
collection. With the value frozen at 2026-09-22 the file was never newer than
anything, so "If newer" updated nothing at all — not an edited note, not an
untouched one. The only option that did anything was "Always", which overwrites
everything. A deck that cannot be corrected is the worse failure of the two, and
it was invisible: the build looked right and the file imported cleanly.

The value stays pinned in the config rather than read from the clock, so a
rebuild of the same release still produces the same bytes. That was the point of
freezing it in the first place; the mistake was freezing it across releases
rather than within one.

## What it costs

A step that is easy to forget. Every release must bump the value by hand, and
must never reuse one, or "If newer" quietly goes back to doing nothing. The test
is what keeps that from happening silently, and the config comment says it in
the place someone preparing a release will be looking.
