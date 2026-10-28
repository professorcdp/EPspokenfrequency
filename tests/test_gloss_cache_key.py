"""What does and does not re-key the $24.95 gloss cache.

A cached reply is keyed on `stamp_for`. Anything outside that stamp may
change freely without costing money; anything inside it re-asks the row.
These tests pin which is which, after a run that re-asked 379 rows because
a new key in `cfg["fixes"]` moved the published-map digest, the map was
missing, and `Sentences` quietly offered every row different sentences.
"""

from __future__ import annotations

import csv

import pytest

from scripts import gloss


def _row(**kw):
    row = {"lemma": "dever", "pos": "verb", "rank": 68, "is_mwe": 0,
           "freq_per_million": 2219.888, "pos_share": "", "split": False}
    row.update(kw)
    return row


SENTS = ["Devo ir embora.", "Deve ser tarde."]


def stamp(cfg, **kw):
    return gloss.stamp_for(cfg, "prompt-digest", _row(**kw), SENTS)


class TestWhatDoesNotRekey:
    def test_rank_alone_does_not_rekey(self, release_cfg):
        """The three rows #22 added shifted ~7,000 ranks. Not one of those
        rows may be re-asked for that reason alone."""
        assert stamp(release_cfg, rank=68) == stamp(release_cfg, rank=5000)

    def test_frequency_alone_does_not_rekey(self, release_cfg):
        assert stamp(release_cfg, freq_per_million=2219.888) == \
               stamp(release_cfg, freq_per_million=1.0)

    def test_pos_share_alone_does_not_rekey(self, release_cfg):
        """pos_share reaches the request through user_block and moves
        whenever a split moves, so it must stay out of the stamp."""
        assert stamp(release_cfg, pos_share=0.5) == stamp(release_cfg, pos_share=0.9)

    def test_is_mwe_and_split_do_not_rekey(self, release_cfg):
        assert stamp(release_cfg, split=False) == stamp(release_cfg, split=True)

    def test_max_tokens_does_not_rekey(self, release_cfg):
        """A ceiling is not a setting: documented in stamp_for."""
        import copy
        other = copy.deepcopy(release_cfg)
        other["gloss"]["max_tokens"] = release_cfg["gloss"]["max_tokens"] * 2
        assert stamp(release_cfg) == stamp(other)


class TestWhatDoesRekey:
    def test_lemma_and_pos_rekey(self, release_cfg):
        assert stamp(release_cfg, lemma="dever") != stamp(release_cfg, lemma="jantar")
        assert stamp(release_cfg, pos="verb") != stamp(release_cfg, pos="noun")

    def test_the_sentences_offered_rekey(self, release_cfg):
        """This is the one that bit. The sentences come from the published
        lemma map, so anything that rebuilds the map can move them."""
        a = gloss.stamp_for(release_cfg, "p", _row(), SENTS)
        b = gloss.stamp_for(release_cfg, "p", _row(), SENTS[::-1])
        c = gloss.stamp_for(release_cfg, "p", _row(), SENTS[:1])
        assert a != b and a != c

    def test_the_prompt_rekeys(self, release_cfg):
        assert gloss.stamp_for(release_cfg, "p1", _row(), SENTS) != \
               gloss.stamp_for(release_cfg, "p2", _row(), SENTS)

    def test_the_model_rekeys(self, release_cfg):
        import copy
        other = copy.deepcopy(release_cfg)
        other["gloss"]["model"] = "something-else"
        assert stamp(release_cfg) != stamp(other)


class TestReusePublished:
    """The safety net: a moved stamp must never silently discard, or pay to
    replace, a gloss that is already published -- above all a reviewed one."""

    def test_the_flag_is_on(self, release_cfg):
        assert release_cfg["gloss"]["reuse_published"] is True

    def test_reads_the_published_file(self, release_cfg, tmp_path, monkeypatch):
        out = tmp_path / "out"
        out.mkdir()
        path = out / release_cfg["gloss"]["out_file"]
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(gloss.GLOSS_COLUMNS)
            w.writerow([68, "dever", "verb", 0, 2219.888, "", "to have to",
                        "Devo ir.", "I must go.", "", "model"])
        monkeypatch.setattr("scripts.config.out_dir", lambda cfg: out)
        prev = gloss.published_previously(release_cfg)
        assert prev[("dever", "verb")]["gloss"] == "to have to"

    def test_absent_file_is_not_an_error(self, release_cfg, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.config.out_dir", lambda cfg: tmp_path)
        assert gloss.published_previously(release_cfg) == {}


def test_a_missing_published_map_is_fatal(release_cfg, monkeypatch):
    """It must never fall back to a lemma map that misses merged entries:
    that changes the sentences offered, which re-keys every row."""
    import scripts.build as build_mod
    monkeypatch.setattr(build_mod, "load_published_map", lambda cfg: None)
    with pytest.raises(SystemExit) as e:
        gloss.Sentences(release_cfg)
    assert "published map" in str(e.value)
    assert "scripts.build" in str(e.value)
