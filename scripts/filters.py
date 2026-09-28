"""Step 4: BP exclusions and the proper-noun filter.

README: "BP-leaning lemmas excluded (...).  Proper-noun leaks filtered via
OOV heuristic (see `dropped_proper_nouns.txt`)."

The BP list is reproduced verbatim for the stage 1 baseline, `cara`
included -- it is ordinary EP for "face" and was excluded in error, so its
removal is a stage 2 fix rather than a silent correction here.

The proper-noun heuristic could not be recovered (see config.yaml), so it
is reconstructed around the signal that actually separates names from
words: how often a token appears capitalized away from the start of a line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from scripts.tokenizer import strip_diacritics


@dataclass
class FilterLog:
    """What each filter removed, and why -- everything dropped is logged."""

    bp_excluded: list[tuple[str, str]] = field(default_factory=list)
    proper_nouns: list[tuple[str, int, float, str]] = field(default_factory=list)
    foreign: list[tuple[str, int, str]] = field(default_factory=list)
    short: list[tuple[str, int, str]] = field(default_factory=list)

    def dropped_lemmas(self) -> set[str]:
        return ({w for w, _ in self.bp_excluded}
                | {w for w, _, _, _ in self.proper_nouns}
                | {w for w, _, _ in self.foreign}
                | {w for w, _, _ in self.short})


def bp_exclusion_set(cfg: dict[str, Any]) -> set[str]:
    """The BP exclusion list for the configured stage.

    Stage 2 removes the entries listed in fixes.bp_exclusion_removals and,
    when fixes.bp_after_folding is on, also excludes unaccented variants --
    which is how `voce` survived the original filter while `você` did not.
    """
    listed = set(cfg["filters"]["bp_exclusions"])
    if cfg["run"]["stage"] < 2:
        return listed
    listed -= set(cfg["fixes"].get("bp_exclusion_removals", ()))
    if cfg["fixes"].get("bp_after_folding"):
        listed |= {strip_diacritics(w) for w in listed}
    return listed


def is_fragment(lemma: str, cfg: dict[str, Any], in_dictionary: Callable[[str], bool]) -> bool:
    """A 1-2 letter lemma that is neither a PT word nor a listed
    interjection: ã, nã, ra, sa and similar subtitle fragments."""
    st = cfg["filters"]["short_tokens"]
    if len(lemma) > st["max_length"]:
        return False
    return not in_dictionary(lemma) and lemma not in set(st["interjections"])


def is_english_plural(
    lemma: str, in_dictionary: Callable[[str], bool], in_english: Callable[[str], bool]
) -> bool:
    """zombies, chips, t-shirts: absent from the PT dictionary, and an
    English plural of an English word.  For a hyphenated form the last part
    is tested (t-shirts -> shirts / shirt)."""
    if not lemma.endswith("s") or len(lemma) < 4 or in_dictionary(lemma):
        return False
    last = lemma.rsplit("-", 1)[-1]
    return in_english(last) and (in_english(last[:-1]) or in_english(last[:-2]))


def proper_noun_decisions(cfg: dict[str, Any]) -> tuple[set[str], set[str]]:
    """(keep, drop) from the human proper-noun review file."""
    import csv
    from pathlib import Path

    if cfg["run"]["stage"] < 2 or not cfg["fixes"].get("proper_noun_review"):
        return set(), set()
    path = Path(cfg["filters"]["proper_nouns"]["keep_file"])
    if not path.is_file():
        return set(), set()
    keep: set[str] = set()
    drop: set[str] = set()
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            decision = (r.get("decision") or "").strip()
            if decision == "keep":
                keep.add(r["lemma"].strip())
            elif decision == "drop":
                drop.add(r["lemma"].strip())
    return keep, drop


def reading_cap_ratios(
    joint_splits: Mapping[str, Any],
    cap_counts: Mapping[str, int],
    noninitial_counts: Mapping[str, int],
    min_votes: int = 3,
    min_share: float = 0.10,
) -> dict[str, float]:
    """Capitalisation measured over a lemma's proper-noun reading alone.

    The plain ratio is the share of a *surface's* non-line-initial
    occurrences that are capitalized, across all of its readings, and for a
    surface that is both a common word and a name it is dominated by the
    common word: `são` is the third person plural of *ser* a million times
    and the São of São Paulo a few thousand, so it reads 0.02 and no
    capitalisation threshold can ever see the name in it.

    Where the per-occurrence splitter has divided a surface between readings,
    the name reading can be measured on its own: the capitalized occurrences
    over the occurrences the PROPN votes claim.

    Three conditions, because the statistic is worthless without them. The
    PROPN reading must have at least ``min_votes`` votes and ``min_share`` of
    the surface's votes, and the capitals must *fit inside* it. Without those
    a single stray PROPN tag collapses the denominator and the ratio saturates
    at 1.0: `dado`, `estado`, `soldado`, `espada` and `fora` all came out at
    1.00 and were dropped as names. When the capitals do not fit, they belong
    to some other reading, which means capitalisation is not diagnostic here
    and the plain ratio stands.

        são   0.02 over everything -> 0.21 for the name reading
        nova  0.40 over everything -> 0.76

    Both are short of a name (john and maria sit at 1.00), which is the
    answer: what is left of `são` and `nova` after the split is mostly the
    common word the tagger mislabelled, not the place.
    """
    caps: dict[str, float] = {}
    claimed: dict[str, float] = {}
    votes_for: dict[str, int] = {}
    for surface, votes in joint_splits.items():
        total = sum(votes.values())
        if not total:
            continue
        propn = {lemma: n for (lemma, upos), n in votes.items() if upos == "PROPN"}
        noninitial = noninitial_counts.get(surface, 0)
        for lemma, n in propn.items():
            if n < min_votes or n / total < min_share:
                continue
            claimed[lemma] = claimed.get(lemma, 0.0) + noninitial * (n / total)
            caps[lemma] = caps.get(lemma, 0.0) + cap_counts.get(surface, 0)
            votes_for[lemma] = votes_for.get(lemma, 0) + n
    return {lemma: caps[lemma] / claimed[lemma]
            for lemma in claimed
            if claimed[lemma] > 0 and caps[lemma] <= claimed[lemma]}


def is_proper_noun(
    lemma: str,
    count: int,
    cap_ratio: float,
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
) -> tuple[bool, str]:
    """Decide whether a lemma is a proper-noun leak.  Returns (drop, reason)."""
    pn = cfg["filters"]["proper_nouns"]
    if not pn.get("enabled"):
        return False, ""
    if count < pn.get("min_count", 1):
        return False, ""

    stage2 = cfg["run"]["stage"] >= 2 and cfg["fixes"].get("extended_proper_nouns")
    threshold = (
        pn["stage2_cap_ratio_threshold"] if stage2 else pn["cap_ratio_threshold"]
    )
    known = in_dictionary(lemma)

    if cap_ratio >= threshold:
        # Stage 1 keeps the original's OOV requirement, so a capitalized word
        # the dictionary knows (jack, mary) survives -- as it did originally.
        if stage2 or not known:
            return True, f"cap_ratio={cap_ratio:.2f}" + ("" if known else ", oov")
    return False, ""


def apply(
    lemma_counts: Mapping[str, int],
    cap_ratios: Mapping[str, float],
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
    in_english: Callable[[str], bool] | None = None,
) -> tuple[dict[str, int], FilterLog]:
    """Run both filters.  Returns the surviving counts and a log."""
    log = FilterLog()
    bp = bp_exclusion_set(cfg)
    keep, reviewed_drop = proper_noun_decisions(cfg)
    interjections = (set(cfg["filters"]["short_tokens"]["interjections"])
                     if cfg["run"]["stage"] >= 2 and cfg["fixes"].get("short_token_rule")
                     else set())
    kept: dict[str, int] = {}

    for lemma, count in lemma_counts.items():
        if lemma in bp:
            log.bp_excluded.append((lemma, "bp_exclusion"))
            continue
        if (cfg["run"]["stage"] >= 2 and cfg["fixes"].get("short_token_rule")
                and is_fragment(lemma, cfg, in_dictionary)):
            log.short.append((lemma, count, "short_token"))
            continue
        if (cfg["run"]["stage"] >= 2 and cfg["fixes"].get("english_plurals_foreign")
                and in_english is not None
                and is_english_plural(lemma, in_dictionary, in_english)):
            log.foreign.append((lemma, count, "english_plural"))
            continue
        # A listed interjection is by definition not a name. They are prone
        # to false positives: capitalization is measured away from the start
        # of a line but not of a sentence, and interjections usually open
        # one (iá: 98% capitalized).
        if lemma in interjections or lemma in keep:
            kept[lemma] = count
            continue
        if lemma in reviewed_drop:
            log.proper_nouns.append((lemma, count, cap_ratios.get(lemma, 0.0), "review_decision"))
            continue
        drop, reason = is_proper_noun(
            lemma, count, cap_ratios.get(lemma, 0.0), cfg, in_dictionary
        )
        if drop:
            log.proper_nouns.append((lemma, count, cap_ratios.get(lemma, 0.0), reason))
            continue
        kept[lemma] = count

    log.proper_nouns.sort(key=lambda t: (-t[1], t[0]))
    log.foreign.sort(key=lambda t: (-t[1], t[0]))
    log.short.sort(key=lambda t: (-t[1], t[0]))
    log.bp_excluded.sort()
    return kept, log


def fold_diacritics(
    counts: Mapping[str, int],
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
) -> tuple[dict[str, int], list[tuple[str, str, int, int, str, bool]]]:
    """Stage 2 fixes (a) and (a'): fold accent variants of one word together.

    Lemmas are grouped by their accent-stripped spelling.  Within a group,
    a lemma folds into the group's most frequent lemma when that one is at
    least ``fixes.diacritic_fold_ratio`` times as frequent:

      (a)  an unaccented lemma (nao -> não, numero -> número), on frequency
           alone -- fixes.diacritic_folding;
      (a') a lemma with a wrong or Brazilian accent (näo -> não, prêmio
           -> prémio), whenever it is absent from the PT dictionary, with no
           ratio -- fixes.accent_variant_folding.  The dictionary test is
           what keeps pôr/por, quê/que, dê/de and avô/avó apart: the
           accented member of each is a real word.  Feminine -ã nouns are
           exempt (cirurgiã is not a misspelling of cirurgia).

    This runs on lemma counts, after lemmatization, so the classic minimal
    pairs cannot meet here: está, é and dá have already become estar, ser
    and dar.  A fold always moves counts towards the commoner form, so
    `exactamente` can never be folded into a one-off typo.

    Returns the folded counts and a log of (from, into, from_count,
    into_count, kind, from_is_dictionary_word).
    """
    fixes = cfg["fixes"]
    unaccented = fixes.get("diacritic_folding", False)
    variants = fixes.get("accent_variant_folding", False)
    if not (unaccented or variants):
        return dict(counts), []
    ratio = fixes.get("diacritic_fold_ratio", 20)

    groups: dict[str, list[str]] = {}
    for word in counts:
        groups.setdefault(strip_diacritics(word), []).append(word)

    redirect: dict[str, str] = {}
    log: list[tuple[str, str, int, int, str, bool]] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        head = sorted(members, key=lambda w: (-counts[w], w))[0]
        for word in members:
            if word == head:
                continue
            is_word = in_dictionary(word)
            if strip_diacritics(word) == word:
                # (a) unaccented: frequency ratio only, as decided.
                if not unaccented or counts[head] < ratio * counts[word]:
                    continue
                kind = "unaccented"
            else:
                # (a') wrong/Brazilian accent: no ratio -- the dictionary
                # test is the safeguard (pôr, quê, dê are words and stay).
                # A feminine in -ã is its own noun, not a misspelling of the
                # -a word: cirurgiã is a surgeon, cirurgia is surgery.
                if not variants or is_word:
                    continue
                if word.endswith("ã") and head.endswith("a"):
                    continue
                kind = "accent_variant"
            redirect[word] = head
            log.append((word, head, counts[word], counts[head], kind, is_word))

    folded: dict[str, int] = {}
    for word, count in counts.items():
        target = redirect.get(word, word)
        folded[target] = folded.get(target, 0) + count

    log.sort(key=lambda t: (-t[2], t[0]))
    return folded, log
