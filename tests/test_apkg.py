"""The Anki package: stable ids, stable GUIDs, reverse cards only with glosses."""

from __future__ import annotations

import sqlite3
import tempfile
import zipfile
from pathlib import Path

import genanki

from scripts import build_apkg


def test_ids_are_never_regenerated(release_cfg):
    """Anki identifies the note type and decks by these numbers. Changing
    them makes a re-import create a second note type and second decks."""
    a = release_cfg["output"]["anki"]["apkg"]
    assert a["model_id"] == 1179315797
    assert [d["id"] for d in a["decks"]] == [
        2068073358, 1644245857, 1345053726, 1181939655, 1443946357, 1360713097,
        2105631544, 1709690318, 1546293187, 2089242372, 1374366428, 1142449800,
        1774535697, 1783859346, 1580005185, 2079134348, 1421632181, 1814710621,
        1954409756, 1890686391]


def test_decks_tile_the_whole_range(release_cfg):
    """Twenty decks of 500, contiguous and in order, named to sort."""
    decks = release_cfg["output"]["anki"]["apkg"]["decks"]
    assert len(decks) == 20
    assert [(d["lo"], d["hi"]) for d in decks] == [(i * 500 + 1, i * 500 + 500)
                                                   for i in range(20)]
    assert [d["name"].split("::")[-1] for d in decks][:2] == ["01 · 1–500", "02 · 501–1000"]
    assert decks[-1]["name"].endswith("20 · 9501–10000")
    assert len({d["id"] for d in decks}) == 20


def test_guid_depends_on_lemma_and_pos_only():
    """Pinned: a re-import updates notes only if GUIDs never change."""
    assert build_apkg.note_guid("o", "det") == "HjlLt~;vi{"
    assert build_apkg.note_guid("a", "det") != build_apkg.note_guid("a", "prep")


def test_reverse_card_only_with_a_gloss(release_cfg):
    """Card 2's front is wrapped in the Gloss_EN conditional, so a note with no
    gloss generates no reverse card. From 1.1 every note has one, but the
    conditional stays: it is what makes the deck safe to ship half-glossed."""
    m = build_apkg.model(release_cfg)
    bare = genanki.Note(model=m, fields=["1", "o", "det", "", "", "", "0", "1", "1", "", ""])
    glossed = genanki.Note(model=m, fields=["1", "o", "det", "the", "", "", "0", "1", "1", "", ""])
    assert [c.ord for c in bare.cards] == [0]
    assert [c.ord for c in glossed.cards] == [0, 1]


def test_the_note_type_fields_are_frozen(release_cfg):
    """Anki matches fields by position, so this list changing breaks re-import
    for anyone already studying the deck. Frozen from 1.1.0."""
    assert build_apkg.FIELDS == [
        "Rank", "Lemma_PT", "POS", "Gloss_EN", "Example_PT", "Example_EN",
        "Is_MWE", "Raw_Freq", "Freq_per_million", "My_Notes", "Gloss_Source"]


GLOSS_HEADER = ("rank\tlemma\tpos\tis_mwe\tfreq_per_million\tpos_share"
                "\tgloss\texample_pt\texample_en\tflags\tsource\n")


def _tiny_corpus(tmp_path):
    """Four published rows and a gloss for each, as the deck now requires."""
    from scripts import config as config_mod

    header = "rank\tlemma\tis_mwe\tpos\traw_freq\tfreq_per_million\n"
    (tmp_path / "ep_spoken_top5000.tsv").write_text(
        header + "1\to\t0\tdet\t100\t1.0\n2\ta\t0\tdet\t90\t0.9\n3\ta\t0\tprep\t80\t0.8\n",
        encoding="utf-8")
    (tmp_path / "ep_spoken_5001_10000.tsv").write_text(
        header + "5001\tfulano\t0\tnoun\t5\t0.1\n", encoding="utf-8")
    (tmp_path / "glosses.tsv").write_text(
        GLOSS_HEADER
        + "1\to\tdet\t0\t1.0\t\tthe\tO cão.\tThe dog.\t\tmodel\n"
        + "2\ta\tdet\t0\t0.9\t\tthe (f.)\tA casa.\tThe house.\tvulgar\tmodel\n"
        + "3\ta\tprep\t0\t0.8\t\tto\t\t\tuncertain name-like\toverride-chosen\n"
        + "5001\tfulano\tnoun\t0\t0.1\t\tso-and-so\t\t\t\tmodel\n",
        encoding="utf-8")
    (tmp_path / "gloss_review.tsv").write_text(
        "lemma\tpos\ttutor_verdict\no\tdet\tgood\na\tprep\t\n", encoding="utf-8")
    return config_mod.with_overrides(release_cfg_of(tmp_path), {})


def release_cfg_of(tmp_path):
    from pathlib import Path as _P

    from scripts import config as config_mod

    return config_mod.with_overrides(
        config_mod.load(_P(__file__).resolve().parents[1] / "config.yaml"),
        {"paths.eval_dir": str(tmp_path)})


def test_package_from_band_files(tmp_path):
    cfg = _tiny_corpus(tmp_path)
    res = build_apkg.build(cfg, tmp_path)
    counts = {name.split("::")[-1]: n for name, n in res["notes"].items() if n}
    assert counts == {"01 · 1–500": 3, "11 · 5001–5500": 1}
    with zipfile.ZipFile(res["path"]) as z:
        z.extract("collection.anki2", tmp_path)
    db = sqlite3.connect(tmp_path / "collection.anki2")
    # every note is glossed, so every note has both cards
    assert db.execute("select count(*) from cards").fetchone()[0] == 8
    tags = db.execute("select tags from notes where flds like '1\x1fo\x1f%'").fetchone()[0]
    assert "freq::0001-0500" in tags and "pos::det" in tags


def test_the_gloss_fills_the_fields(tmp_path):
    cfg = _tiny_corpus(tmp_path)
    res = build_apkg.build(cfg, tmp_path)
    with zipfile.ZipFile(res["path"]) as z:
        z.extract("collection.anki2", tmp_path)
    db = sqlite3.connect(tmp_path / "collection.anki2")
    flds = {f.split("\x1f")[1] + "/" + f.split("\x1f")[2]: f.split("\x1f")
            for (f,) in db.execute("select flds from notes")}
    o = flds["o/det"]
    assert len(o) == len(build_apkg.FIELDS)
    assert o[3] == "the" and o[4] == "O cão." and o[5] == "The dog."
    assert o[9] == ""                                   # My_Notes is the learner's
    assert o[10] == cfg["gloss"]["source_labels"]["model"]
    assert flds["a/prep"][10] == cfg["gloss"]["source_labels"]["override-chosen"]
    assert flds["a/prep"][4] == "" and flds["a/prep"][5] == ""   # no example


def test_flag_and_reviewed_tags(tmp_path):
    cfg = _tiny_corpus(tmp_path)
    res = build_apkg.build(cfg, tmp_path)
    assert res["flags"] == {"name-like": 1, "uncertain": 1, "vulgar": 1}
    assert res["reviewed"] == 1
    with zipfile.ZipFile(res["path"]) as z:
        z.extract("collection.anki2", tmp_path)
    db = sqlite3.connect(tmp_path / "collection.anki2")
    tags = {f.split("\x1f")[1] + "/" + f.split("\x1f")[2]: t
            for f, t in db.execute("select flds, tags from notes")}
    assert "flag::vulgar" in tags["a/det"]
    assert "flag::uncertain" in tags["a/prep"] and "flag::name-like" in tags["a/prep"]
    assert "gloss::reviewed" in tags["o/det"]
    assert "gloss::reviewed" not in tags["a/prep"]       # blank verdict is not reviewed
    assert "flag::" not in tags["o/det"]


def test_a_published_row_without_a_gloss_stops_the_build(tmp_path):
    """Better no deck than notes with an empty front on card 2."""
    import pytest

    cfg = _tiny_corpus(tmp_path)
    (tmp_path / "glosses.tsv").write_text(
        GLOSS_HEADER + "1\to\tdet\t0\t1.0\t\tthe\t\t\t\tmodel\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        build_apkg.build(cfg, tmp_path)
    assert "no gloss" in str(exc.value)


# -- the deck that actually ships --------------------------------------------

OUT = Path(__file__).resolve().parents[1] / "out"


def _shipped_notes():
    """(fields, tags) for every note in out/EP_Spoken_Frequency.apkg."""
    import pytest

    apkg = OUT / "EP_Spoken_Frequency.apkg"
    if not apkg.is_file():
        pytest.skip("the deck has not been built")
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(apkg) as z:
        z.extract("collection.anki2", tmp)
    db = sqlite3.connect(tmp / "collection.anki2")
    notes = [(f.split("\x1f"), t.split())
             for f, t in db.execute("select flds, tags from notes")]
    cards = db.execute("select count(*) from cards").fetchone()[0]
    return notes, cards


def test_every_shipped_note_is_glossed():
    notes, cards = _shipped_notes()
    assert len(notes) == 10_000
    assert all(len(f) == len(build_apkg.FIELDS) for f, _ in notes)
    assert all(f[3].strip() for f, _ in notes), "a note with no gloss"
    assert all(f[10].strip() for f, _ in notes), "a note with no Gloss_Source"
    assert not any(f[9].strip() for f, _ in notes), "My_Notes is the learner's space"


def test_every_shipped_note_has_a_reverse_card():
    """Card 2 exists exactly where Gloss_EN is filled, which is now everywhere."""
    notes, cards = _shipped_notes()
    glossed = sum(1 for f, _ in notes if f[3].strip())
    assert cards == len(notes) + glossed == 20_000


def test_shipped_tags_match_the_glosses_and_the_review():
    import csv as _csv
    from collections import Counter

    notes, _ = _shipped_notes()
    tags = Counter(t for _, ts in notes for t in ts if t.startswith(("flag::", "gloss::")))
    with (OUT / "glosses.tsv").open(encoding="utf-8", newline="") as fh:
        want = Counter(f"flag::{f}" for r in _csv.DictReader(fh, delimiter="\t")
                       for f in r["flags"].split())
    with (OUT.parent / "eval" / "gloss_review.tsv").open(encoding="utf-8", newline="") as fh:
        reviewed = sum(1 for r in _csv.DictReader(fh, delimiter="\t")
                       if (r.get("tutor_verdict") or "").strip())
    assert {k: v for k, v in tags.items() if k.startswith("flag::")} == dict(want)
    assert tags["gloss::reviewed"] == reviewed == 500


def test_shipped_notes_keep_the_original_tags():
    """1.1 adds tags; it removes none, or a learner's saved searches break."""
    notes, _ = _shipped_notes()
    for fields, tags in notes[:50]:
        assert any(t.startswith("freq::") for t in tags)
        assert any(t.startswith("freq500::") for t in tags)
        assert any(t.startswith("freq1000::") for t in tags)
        assert any(t.startswith("pos::") for t in tags)
        assert "source::opensubtitles_ep_v2018" in tags
        assert "variety::EP" in tags and "register::spoken" in tags
