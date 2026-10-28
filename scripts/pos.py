"""Published part of speech, from Stanza's tags.

Stanza tags every sampled sentence of every frequent word in one pass
(scripts/occurrence.py). A lemma's POS comes from those tags:

  * a word whose lemma is not split contributes the tags of the sentences
    where Stanza's lemma is the majority lemma or the word itself -- `casa`
    tagged VERB is `casar`, and must not make the noun `casa` a verb, but
    `a` read as the article *o* and as the preposition *a* is still `a`;
  * a word split across lemmas (participles, fomos) already carries a
    (lemma, POS) pair per sentence, and those pairs are used directly.

Each word's corpus count is divided across POS in proportion to its tags,
exactly as a split word's count is divided across lemmas, and the shares
are summed per lemma. The majority POS is published. A secondary POS
becomes an entry of its own when it holds at least `pos.split_min_share`
of the lemma's count and at least `pos.split_min_votes` tagged sentences;
otherwise its share joins the majority. A lemma with no tagged evidence
(contractions, whose tokens Stanza expands, and the low-frequency tail)
falls back to the rule heuristic.

Stanza's tag and lemma for one sentence do not always agree -- `consigo`
comes back as lemma *conseguir* tagged ADV (it read the pronoun), `conta`
as *contar* tagged NOUN, `mais` as NOUN in 19 of 50 sentences. A tag is
only counted when it is consistent with its lemma:
  * a VERB/AUX tag needs a verb lemma;
  * any other tag on a verb lemma counts only for the infinitive itself
    (a nominalised infinitive: *o poder*, *o jantar*);
  * a function word (the closed-class table) cannot be a noun or a verb.
A verb lemma is infinitive-shaped and not tagged mainly as a noun or
adjective in its own sentences, so `lugar` and `mulher` are not verbs --
except that for the POS column the rest of the paradigm is asked too, or a
nominalised infinitive takes the whole verb with it (`dever`; see
`paradigm_verb_lemmas`).
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Mapping, Sequence

from scripts.occurrence import apportion


def map_upos(upos: str, cfg: dict[str, Any], lemma: str | None = None) -> str:
    """UD tag -> the list's POS. A conjunction tag on a word from
    pos.always_prep counts as prep (UD tags "para fazer" as SCONJ)."""
    mapped = cfg["pos"]["upos_map"].get(upos, "unk")
    if mapped == "conj" and lemma is not None and lemma in cfg["pos"].get("always_prep", ()):
        return "prep"
    return mapped


def majority(votes: Counter) -> str | None:
    if not votes:
        return None
    top = max(votes.values())
    return sorted(k for k, v in votes.items() if v == top)[0]


_VERB_TAGS = ("VERB", "AUX")
_NOMINAL_TAGS = ("NOUN", "PROPN", "ADJ")


def verb_lemmas(tags: Mapping[str, Sequence[tuple[str, str, str]]]):
    """Predicate: is this lemma a verb? Infinitive-shaped, and not tagged
    mainly as a noun or adjective where it occurs as a surface itself."""
    nominal: set[str] = set()
    for surface, occs in tags.items():
        upos = majority(Counter(u for _, u, _ in occs))
        if upos in _NOMINAL_TAGS:
            nominal.add(surface)

    def is_verb(lemma: str) -> bool:
        return lemma.endswith(("ar", "er", "ir", "ôr")) and lemma not in nominal
    return is_verb


def paradigm_verb_lemmas(
    tags: Mapping[str, Sequence[tuple[str, str, str]]],
    is_verb,
    min_surfaces: int,
):
    """A verb test for the POS column that reads the whole paradigm.

    `verb_lemmas` asks one question of one surface: is the bare infinitive
    tagged as a noun or adjective? For *dever* the answer is yes -- in
    subtitles a bare `dever` is usually *o dever*, "the duty", 43 of 50
    sampled sentences -- so the lemma was ruled out as a verb and all 857
    VERB tags on `devo`, `deve`, `devia`, `deveria` ... were thrown away by
    `consistent`. Nothing survived but the noun, and the commonest modal
    verb in the language was published as a noun at rank 68 carrying the
    verb's whole count.

    A nominalised infinitive is a real thing, so the answer is not to drop
    the test but to ask the rest of the paradigm as well. A lemma is a verb
    here when it is infinitive-shaped and its VERB/AUX tags come from at
    least `min_surfaces` distinct *inflected* surfaces -- a conjugated form
    is evidence of a verb in a way the infinitive alone is not, because the
    infinitive is the one form that is also a noun.

    Two conditions keep a mistag from passing as a paradigm:

      * only a surface whose own majority lemma is this lemma counts. A
        stray minority reading would never reach `aggregate` anyway, since
        it drops occurrences whose lemma is neither the majority nor the
        surface itself. Without this, `mar` collects `mando`, `marque` and
        `mudasses` and reads as a verb.
      * the surface must begin with the infinitive's stem, and the stem
        must be at least three characters. This is what separates `tremer`
        (`tremem`, `tremeu`, `tremia`, `tremiam`) from `mar`, whose stem is
        the single letter `m`.

    The result is only ever *more* permissive than `is_verb`: a lemma that
    already passes still passes, so no lemma can lose its verb reading, and
    the only entries that can move are ones the veto was suppressing. The
    cost of the stem rule is that a suppressed irregular verb is not
    rescued (`disse` does not begin `diz`), which leaves today's answer
    rather than risking a new wrong one.

    This is for the POS column alone. `verb_lemmas` still decides lemma
    resolution and `consistent_shape`, so neither the lemma map nor the
    ser/ir split moves.
    """
    paradigm: dict[str, set[str]] = {}
    for surface, occs in tags.items():
        agreed = majority(Counter(lemma for lemma, _, _ in occs))
        if agreed is None or agreed == surface:
            continue
        stem = agreed[:-2] if agreed.endswith(("ar", "er", "ir", "ôr")) else agreed
        if len(stem) < 3 or not surface.startswith(stem):
            continue
        if any(u in _VERB_TAGS for lemma, u, _ in occs if lemma == agreed):
            paradigm.setdefault(agreed, set()).add(surface)

    def is_verb_for_pos(lemma: str) -> bool:
        if is_verb(lemma):
            return True
        return (lemma.endswith(("ar", "er", "ir", "ôr"))
                and len(paradigm.get(lemma, ())) >= min_surfaces)
    return is_verb_for_pos


def consistent(surface: str, lemma: str, upos: str, is_verb, closed) -> bool:
    if upos in _VERB_TAGS:
        return is_verb(lemma) and lemma not in closed
    if is_verb(lemma):
        return surface == lemma
    if lemma in closed and upos in ("NOUN", "PROPN"):
        return False
    return True


def consistent_shape(surface: str, lemma: str, upos: str, is_verb, closed) -> bool:
    """Does the tag agree with the shape of the lemma? Used when deciding
    which lemma an occurrence belongs to, rather than what part of speech a
    word has.

    Same rule as `consistent` without one clause: that one also vetoes a
    VERB/AUX tag whose lemma is a function word, which is right for the POS
    column -- a preposition tagged VERB is noise -- but wrong here, because
    *ser*, *ter*, *ir* and *este* are closed-class and inflected words at the
    same time. With the veto, all 45 AUX votes saying `são` is a form of *ser*
    were thrown away and the 5 that read it as the name *São* decided the
    lemma, publishing 1.1 million occurrences of "they are" as a noun.
    """
    if upos in _VERB_TAGS:
        return is_verb(lemma)
    if is_verb(lemma):
        return surface == lemma
    if lemma in closed and upos in ("NOUN", "PROPN"):
        return False
    return True


def aggregate(
    surface_counts: Mapping[str, int],
    tags: Mapping[str, Sequence[tuple[str, str, str]]],
    joint: Mapping[str, Counter],
    headword_of_surface: Callable[[str], str],
    headword_of_lemma: Callable[[str], str],
    cfg: dict[str, Any],
    closed: frozenset[str] = frozenset(),
    stats: dict[str, int] | None = None,
    is_verb: Callable[[str], bool] | None = None,
) -> tuple[dict[str, Counter], dict[str, Counter]]:
    """Count-weighted POS shares and raw tag votes, per final lemma.

    ``joint`` maps a split surface to Counter{(lemma, upos): votes}.
    ``headword_of_surface`` gives the published headword of an unsplit
    surface, and ``headword_of_lemma`` the headword a split surface's
    per-sentence lemma ends up under (both through conventions, closure
    and accent folding).
    """
    weighted: dict[str, Counter] = {}
    raw: dict[str, Counter] = {}
    if is_verb is None:
        is_verb = verb_lemmas(tags)

    def add(lemma: str, pos_votes: Counter, count: int) -> None:
        w = weighted.setdefault(lemma, Counter())
        r = raw.setdefault(lemma, Counter())
        for pos, share in apportion(count, pos_votes).items():
            w[pos] += share
        r.update(pos_votes)

    for surface in sorted(surface_counts):
        count = surface_counts[surface]
        if surface in joint:
            cells: dict[str, Counter] = {}
            for (lemma, upos), n in joint[surface].items():
                cells.setdefault(lemma, Counter())[map_upos(upos, cfg, lemma)] += n
            by_lemma = Counter({lemma: sum(c.values()) for lemma, c in cells.items()})
            for lemma, share in apportion(count, by_lemma).items():
                add(headword_of_lemma(lemma), cells[lemma], share)
            continue
        occs = tags.get(surface) or ()
        if not occs:
            continue
        agreed = majority(Counter(lemma for lemma, _, _ in occs))
        votes: Counter = Counter()
        for lemma, upos, _ in occs:
            # A sentence counts if Stanza's lemma is the majority lemma or
            # the word itself: `a` is lemmatized *o* as an article and *a*
            # as a preposition, and both readings belong to the entry `a`.
            if lemma != agreed and lemma != surface:
                continue
            if consistent(surface, lemma, upos, is_verb, closed):
                votes[map_upos(upos, cfg, lemma)] += 1
            elif stats is not None:
                stats["inconsistent"] = stats.get("inconsistent", 0) + 1
        if stats is not None:
            stats["counted"] = stats.get("counted", 0) + sum(votes.values())
        if votes:
            add(headword_of_surface(surface), votes, count)
    return weighted, raw


def contraction_pos(cfg: dict[str, Any]) -> dict[str, str]:
    """form -> published POS for every contraction (fixes.contraction_pos).

    Stanza expands a contraction into its two words before tagging, so the
    surface token itself collects almost no consistent evidence: the tags
    that survive are noise, and the words with none at all fall through to
    the rule heuristic, which answers `unk`. A decided answer per form is
    both more accurate and more useful than 81 independent guesses.

    The answer follows what the contraction contracts, not the paradigm it
    sits in: preposition + article or demonstrative is a determiner (`do`,
    `nas`, `deste`), preposition + pronoun is a pronoun (`dele`, `comigo`,
    `disso`), preposition + adverb of place is an adverb (`daqui`).
    """
    rule = cfg["pos"].get("contraction_pos")
    if not (cfg["fixes"].get("contraction_pos") and rule):
        return {}
    forms = cfg["conventions"].get("contractions", {}).get("forms", ())
    named = {form: pos for pos, group in rule.items() if pos != "default"
             for form in group}
    return {form: named.get(form, rule["default"]) for form in forms}


def assign(
    lemma: str,
    count: int,
    weighted: Mapping[str, Counter],
    raw: Mapping[str, Counter],
    cfg: dict[str, Any],
    fallback: Callable[[str], str],
    contractions: Mapping[str, str] | None = None,
) -> list[tuple[str, int]]:
    """[(pos, count)] for one lemma: one row, or one per well-supported POS.

    Shares below the split thresholds join the majority POS. The lemma's
    final count is divided in proportion to the kept POS shares. A
    contraction is never split and never asks the tagger.
    """
    if contractions and lemma in contractions:
        return [(contractions[lemma], count)]
    shares = weighted.get(lemma)
    if not shares or sum(shares.values()) == 0:
        return [(fallback(lemma), count)]
    total = sum(shares.values())
    votes = raw.get(lemma, Counter())
    main = majority(shares)
    kept = Counter({main: 0})
    for pos, w in shares.items():
        target = pos
        if pos != main and (w / total < cfg["pos"]["split_min_share"]
                            or votes.get(pos, 0) < cfg["pos"]["split_min_votes"]):
            target = main
        kept[target] += w
    parts = apportion(count, kept)
    return sorted(parts.items(), key=lambda kv: (-kv[1], kv[0]))
