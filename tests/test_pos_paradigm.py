"""The paradigm verb test for the POS column (#22, `dever`).

`verb_lemmas` asks only the bare infinitive, so a nominalised infinitive
took the whole verb with it: `dever` published at rank 68 as a noun with
the verb's count, every one of its 857 VERB tags vetoed.

The table below is the sibling survey from #22, re-run against the shipped
tag cache. It is the real guard on the threshold: it pins which lemmas the
new test rescues and -- more importantly -- which plain nouns it must leave
alone. `.cache/` is not in the repository, so the cache-backed tests skip
when it is absent; the hand-built ones always run.
"""

from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import pos

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "occurrences_8dd3b3a082fa3f21.json.gz"

# lemma -> is it a verb for the POS column, once the paradigm is read?
# "verb" rows gain a verb reading; "noun" rows must not.
SIBLINGS = {
    # the five real paradigms the veto was hiding
    "dever": True, "jantar": True, "colher": True, "colar": True, "tremer": True,
    # arguable: a real verb exists but too few inflected forms are tagged.
    # Left as they are rather than loosened until something asks for them.
    "tender": False, "amanhecer": False, "piscar": False, "regular": False,
    "disciplinar": False,
    # plain nouns and adjectives that merely end -ar/-er/-ir. The veto was
    # right about every one of these, and must stay right.
    "ar": False, "mar": False, "par": False, "sir": False, "açúcar": False,
    "repórter": False, "bazar": False, "auxiliar": False, "bilhar": False,
    "pestanejar": False, "per": False, "coxear": False, "pulsar": False,
    "descarrilar": False,
}


@pytest.fixture(scope="module")
def tags():
    if not CACHE.is_file():
        pytest.skip(f"{CACHE.name} not present (the corpus caches are not committed)")
    with gzip.open(CACHE, "rt", encoding="utf-8") as fh:
        return {k: [tuple(x) for x in v] for k, v in json.load(fh).items()}


@pytest.fixture(scope="module")
def is_verb_for_pos(tags, release_cfg):
    return pos.paradigm_verb_lemmas(
        tags, pos.verb_lemmas(tags), release_cfg["pos"]["verb_paradigm_min_surfaces"])


def test_the_table_is_the_whole_sibling_survey():
    """24 lemmas: 5 rescued, 19 left alone."""
    assert len(SIBLINGS) == 24
    assert sum(SIBLINGS.values()) == 5


@pytest.mark.parametrize("lemma,expected", sorted(SIBLINGS.items()))
def test_sibling_verb_reading(is_verb_for_pos, lemma, expected):
    assert is_verb_for_pos(lemma) is expected


def test_dever_is_the_case_that_prompted_this(tags, is_verb_for_pos):
    """The bare infinitive says noun 43 to verb 7, and said so alone."""
    votes = Counter(u for _, u, _ in tags["dever"])
    assert votes["NOUN"] == 43 and votes["VERB"] == 7
    assert pos.verb_lemmas(tags)("dever") is False
    assert is_verb_for_pos("dever") is True


def test_the_veto_was_discarding_the_whole_paradigm(tags):
    """857 VERB votes across the inflected forms, every one dropped.

    Counted the way `aggregate` counts: an occurrence whose lemma is
    neither the surface's majority lemma nor the surface itself is skipped
    before `consistent` ever sees it, which is why this is 857 and not the
    860 occurrences that merely mention *dever*.
    """
    is_verb = pos.verb_lemmas(tags)
    vetoed = 0
    for surface, occs in tags.items():
        agreed = pos.majority(Counter(l for l, _, _ in occs))
        for lemma, upos, _ in occs:
            if lemma != agreed and lemma != surface:
                continue
            if lemma == "dever" and upos in ("VERB", "AUX") and not pos.consistent(
                    surface, lemma, upos, is_verb, frozenset()):
                vetoed += 1
    assert vetoed == 857


def test_real_verbs_are_unaffected(is_verb_for_pos):
    for lemma in ("ser", "falar", "precisar", "poder", "dizer"):
        assert is_verb_for_pos(lemma) is True


def test_it_only_ever_adds(tags, is_verb_for_pos):
    """No lemma may lose its verb reading: the new test is a superset, so
    the only entries that can move are ones the veto was suppressing."""
    is_verb = pos.verb_lemmas(tags)
    for lemma in {l for occs in tags.values() for l, _, _ in occs}:
        if is_verb(lemma):
            assert is_verb_for_pos(lemma) is True


def test_a_stray_mistag_is_not_a_paradigm():
    """`mar` collects `mando`, `marque`, `mudasses` -- five surfaces, no
    shared stem. Without the stem rule the sea becomes a verb."""
    tags = {
        "mar": [("mar", "NOUN", "")] * 50,
        "mando": [("mandar", "VERB", "")] * 4 + [("mar", "VERB", "")],
        "marque": [("marcar", "VERB", "")] * 4 + [("mar", "VERB", "")],
        "marquei": [("marcar", "VERB", "")] * 4 + [("mar", "VERB", "")],
        "marchamos": [("marchar", "VERB", "")] * 4 + [("mar", "VERB", "")],
        "mudasses": [("mudar", "VERB", "")] * 4 + [("mar", "VERB", "")],
    }
    f = pos.paradigm_verb_lemmas(tags, pos.verb_lemmas(tags), 4)
    assert f("mar") is False


def test_a_shared_stem_with_enough_forms_is_a_paradigm():
    tags = {
        "tremer": [("tremer", "NOUN", "")] * 30 + [("tremer", "VERB", "")] * 20,
        "tremem": [("tremer", "VERB", "")] * 5,
        "tremeu": [("tremer", "VERB", "")] * 5,
        "tremia": [("tremer", "VERB", "")] * 5,
        "tremiam": [("tremer", "VERB", "")] * 5,
    }
    f = pos.paradigm_verb_lemmas(tags, pos.verb_lemmas(tags), 4)
    assert f("tremer") is True
    assert pos.paradigm_verb_lemmas(tags, pos.verb_lemmas(tags), 5)("tremer") is False


def test_minority_readings_do_not_count():
    """A surface whose majority lemma is something else never votes in
    `aggregate`, so it must not count towards a paradigm either."""
    tags = {
        "pasmar": [("pasmar", "NOUN", "")] * 50,
        **{f"pasma{i}": [("outro", "VERB", "")] * 4 + [("pasmar", "VERB", "")]
           for i in range(6)},
    }
    f = pos.paradigm_verb_lemmas(tags, pos.verb_lemmas(tags), 4)
    assert f("pasmar") is False


def test_the_flag_and_threshold_are_config(release_cfg):
    assert release_cfg["fixes"]["paradigm_verb_pos"] is True
    assert release_cfg["pos"]["verb_paradigm_min_surfaces"] == 4


def test_stage_one_leaves_it_off(cfg):
    """Stage 1 must keep reproducing the April baseline."""
    assert cfg["fixes"]["paradigm_verb_pos"] is False
