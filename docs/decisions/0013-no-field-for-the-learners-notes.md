# 0013 — The deck ships no field for the learner's own notes

**Date:** 2026-10-23
**Status:** accepted

## What was decided

The note type carries no field for a learner to write in. A `My_Notes` field
was built and then removed before release. The CHANGELOG tells learners how to
add a field of their own, and what it costs them.

## Why

Anki cannot merge fields on import. Its "Update notes" options are Never, If
newer and Always: "Always" overwrites every field of every matched note, and
"If newer" overwrites every field of each note it updates. Neither can keep one
field back.

So a field this package ships can be erased by a later release, without warning,
along with whatever the learner typed into it. A field the learner adds
themselves cannot be — but only because changing the note type stops Anki
updating those notes at all.

That leaves no arrangement in which a field we ship is a safe place to write.
Offering one anyway would be inviting people to put work somewhere we would
later overwrite, which is worse than offering nothing: this project does not
ship a guarantee it cannot keep.

## What it costs

A learner who wants to annotate must add the field themselves, through Tools →
Manage Note Types → Fields, which is a step most will not find on their own.
Having done it, they stop receiving updates to those notes: a later release will
add new words but leave their existing ones as they are. The deck is therefore
less useful out of the box than one with a notes field, and the trade is
explained in the CHANGELOG rather than solved.

Reverses the earlier plan to ship `My_Notes`, taken after reading Anki's
documented import rules. See [0014](0014-a-package-timestamp-per-release.md).
