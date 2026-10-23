"""Build out/EP_Spoken_Frequency.apkg, the ready-to-import Anki package.

One note type, "Portuguese (EP) – Spoken Frequency", with the enrichable
field set, and twenty subdecks of 500 words, numbered so they sort in rank
order (`01 · 1–500` … `20 · 9501–10000`). Two card templates:

  Card 1  PT -> EN  every note
  Card 2  EN -> PT  only when Gloss_EN is filled in: its front is wrapped
                    in {{#Gloss_EN}}...{{/Gloss_EN}}, and Anki does not
                    generate a card whose front renders empty. The lists
                    ship without glosses, so no reverse cards exist yet.

Stability across releases. The note type and deck ids live in config.yaml
and are never regenerated. Each note's GUID is derived from its lemma and
POS, so importing a later release over this one updates the matching notes
(new ranks, counts, tags) instead of adding duplicates, and keeps a
learner's review history.

Run by `python -m scripts.build` after the lists are written, or alone:
    python -m scripts.build_apkg
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

# FROZEN FROM 1.1.0. Anki matches a note's fields by position, so adding,
# removing or reordering any of these breaks a re-import for everyone who has
# already studied the deck. Gloss_Source was the last field added, in 1.1.0,
# and the list does not change again; anything further goes in a new note type.
#
# There is deliberately no field here for the learner's own writing. Anki
# cannot merge fields on import: "Always" overwrites every field, and "If
# newer" overwrites every field of each note it updates. So any field this
# package ships can be erased by a later release, and a field the learner adds
# themselves cannot be -- because a changed note type stops Anki updating those
# notes at all. A place to write that we would overwrite is worse than no
# place, so the deck ships none and the README says how to add one.
FIELDS = ["Rank", "Lemma_PT", "POS", "Gloss_EN", "Example_PT", "Example_EN",
          "Is_MWE", "Raw_Freq", "Freq_per_million", "Gloss_Source"]

FRONT_PT = """<div class="lemma">{{Lemma_PT}}</div>
<div class="pos">{{POS}}</div>"""

BACK_PT = """{{FrontSide}}
<hr id="answer">
{{#Gloss_EN}}<div class="gloss">{{Gloss_EN}}</div>{{/Gloss_EN}}
{{#Example_PT}}<div class="example pt">{{Example_PT}}</div>{{/Example_PT}}
{{#Example_EN}}<div class="example en">{{Example_EN}}</div>{{/Example_EN}}
<div class="footer">#{{Rank}} · {{Freq_per_million}} per million words{{#Gloss_Source}} · {{Gloss_Source}}{{/Gloss_Source}}</div>"""

# The whole front sits inside the Gloss_EN conditional: with no gloss the
# front is empty and Anki generates no card.
FRONT_EN = """{{#Gloss_EN}}<div class="gloss prompt">{{Gloss_EN}}</div>
<div class="pos">{{POS}}</div>{{/Gloss_EN}}"""

# The part of speech is already on this card: FrontSide carries it above the
# rule, so repeating it below would print it twice.
BACK_EN = """{{FrontSide}}
<hr id="answer">
<div class="lemma">{{Lemma_PT}}</div>
{{#Example_PT}}<div class="example pt">{{Example_PT}}</div>{{/Example_PT}}
{{#Example_EN}}<div class="example en">{{Example_EN}}</div>{{/Example_EN}}
<div class="footer">#{{Rank}} · {{Freq_per_million}} per million words{{#Gloss_Source}} · {{Gloss_Source}}{{/Gloss_Source}}</div>"""

CSS = """.card {
  font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 20px;
  line-height: 1.4;
  text-align: center;
  color: #1f2328;
  background: #ffffff;
  padding: 1.2em 1em;
}
.lemma { font-size: 2.2em; font-weight: 600; }
.pos { font-size: 0.8em; color: #6e7781; margin-top: 0.2em; letter-spacing: 0.03em; }
.gloss { font-size: 1.2em; margin: 0.6em 0; }
.gloss.prompt { font-size: 1.6em; }
.example { font-size: 0.95em; margin: 0.4em auto; max-width: 32em; }
.example.en { color: #57606a; font-style: italic; }
.footer { margin-top: 1.4em; font-size: 0.7em; color: #8c959f; }
hr#answer { border: none; border-top: 1px solid #d0d7de; margin: 0.9em 0; }
.nightMode .card, .night_mode .card { color: #e6edf3; background: #0d1117; }
.nightMode .pos, .night_mode .pos, .nightMode .footer, .night_mode .footer { color: #8b949e; }
.nightMode .example.en, .night_mode .example.en { color: #a8b1bb; }
@media (max-width: 480px) { .card { font-size: 18px; } .lemma { font-size: 2em; } }
"""


def model(cfg: dict[str, Any]):
    import genanki

    acfg = cfg["output"]["anki"]
    return genanki.Model(
        acfg["apkg"]["model_id"],
        acfg["notetype"],
        fields=[{"name": f} for f in FIELDS],
        templates=[
            {"name": "Card 1 (PT → EN)", "qfmt": FRONT_PT, "afmt": BACK_PT},
            {"name": "Card 2 (EN → PT)", "qfmt": FRONT_EN, "afmt": BACK_EN},
        ],
        css=CSS,
        sort_field_index=0,
    )


def note_guid(lemma: str, pos: str) -> str:
    """Stable across releases: the same word in the same POS is the same
    note, whatever its rank or count."""
    import genanki

    return genanki.guid_for("ep-spoken-frequency", lemma, pos)


def published_glosses(cfg: dict[str, Any], out_dir: Path) -> dict[tuple[str, str], dict]:
    """out/glosses.tsv keyed by lemma and POS, the same key the GUID uses.

    Every published row has a gloss, so a missing one means the glosses and
    the lists have come apart -- a rebuild that moved a lemma or a part of
    speech without the glosses being regenerated. The deck refuses to build
    rather than ship notes with an empty front on card 2.
    """
    path = out_dir / cfg["gloss"]["out_file"]
    if not path.is_file():
        raise SystemExit(
            f"{path} not found. Build it with python -m scripts.gloss --report, "
            "which writes it from cache/gloss/ without calling the API.")
    with path.open(encoding="utf-8", newline="") as fh:
        return {(r["lemma"], r["pos"]): r for r in csv.DictReader(fh, delimiter="\t")}


def reviewed_entries(cfg: dict[str, Any]) -> set[tuple[str, str]]:
    """Entries a native speaker has given a verdict on, for the gloss::reviewed
    tag. Absent review file means no claim, not an error."""
    path = Path(cfg["paths"]["eval_dir"]) / cfg["gloss"]["review"]["file"]
    if not path.is_file():
        return set()
    with path.open(encoding="utf-8", newline="") as fh:
        return {(r["lemma"], r["pos"]) for r in csv.DictReader(fh, delimiter="\t")
                if (r.get("tutor_verdict") or "").strip()}


def build(cfg: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Write the .apkg from the band TSVs in out_dir. Returns note counts."""
    import genanki

    from scripts.emit import build_tags

    acfg = cfg["output"]["anki"]
    pcfg = acfg["apkg"]
    mdl = model(cfg)
    glosses = published_glosses(cfg, out_dir)
    reviewed = reviewed_entries(cfg)
    labels = cfg["gloss"].get("source_labels", {})
    missing: list[tuple[str, str]] = []
    n_reviewed = 0
    flag_counts: dict[str, int] = {}
    decks = [genanki.Deck(d["id"], d["name"]) for d in pcfg["decks"]]
    by_rank = sorted(zip(pcfg["decks"], decks), key=lambda t: t[0]["lo"])
    seen: set[str] = set()

    def deck_for(rank: int) -> "genanki.Deck":
        for spec, deck in by_rank:
            if spec["lo"] <= rank <= spec["hi"]:
                return deck
        raise ValueError(f"rank {rank} falls outside every deck in config")

    for spec in cfg["output"]["files"]:
        with (out_dir / f"{spec['stem']}.tsv").open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                key = (row["lemma"], row["pos"])
                guid = note_guid(*key)
                if guid in seen:
                    raise ValueError(f"duplicate note (lemma, pos): {row['lemma']!r}, {row['pos']!r}")
                seen.add(guid)
                rank = int(row["rank"])
                g = glosses.get(key)
                if g is None:
                    missing.append(key)
                    continue
                flags = g["flags"].split() if g["flags"] else []
                for f in flags:
                    flag_counts[f] = flag_counts.get(f, 0) + 1
                is_reviewed = key in reviewed
                n_reviewed += is_reviewed
                deck_for(rank).add_note(genanki.Note(
                    model=mdl,
                    fields=[row["rank"], row["lemma"], row["pos"],
                            g["gloss"], g["example_pt"], g["example_en"],
                            row["is_mwe"], row["raw_freq"], row["freq_per_million"],
                            labels.get(g["source"], g["source"])],
                    tags=build_tags(rank, row["pos"], cfg, flags=flags,
                                    reviewed=is_reviewed).split(),
                    guid=guid,
                    sort_field=row["rank"],
                ))

    if missing:
        raise SystemExit(
            f"{len(missing)} published row(s) have no gloss, so the deck was not "
            f"written: " + ", ".join(f"{l} ({p})" for l, p in missing[:8]) + ".\n"
            "An entry that has never been glossed needs python -m scripts.gloss "
            "--retry, which calls the API and costs money. If these were glossed "
            "before and a rebuild moved their lemma or part of speech, "
            "--report alone may be enough.")

    path = out_dir / pcfg["file"]
    genanki.Package(decks).write_to_file(str(path), timestamp=pcfg["timestamp"])
    return {"path": str(path), "bytes": path.stat().st_size,
            "notes": {d.name: len(d.notes) for d in decks},
            "reviewed": n_reviewed, "flags": dict(sorted(flag_counts.items()))}


def main() -> None:
    import argparse

    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description="Build the Anki .apkg from out/.")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    cfg = config_mod.load(args.config)
    res = build(cfg, config_mod.out_dir(cfg))
    print(f"{res['path']}: {res['bytes']:,} bytes")
    for name, n in res["notes"].items():
        print(f"  {name}: {n:,} notes")


if __name__ == "__main__":
    main()
