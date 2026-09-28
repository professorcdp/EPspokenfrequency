"""English glosses and example sentences for the published rows (v1.1).

For each of the 10,000 rows in ``out/`` this asks Claude for three things:
a gloss of one to three senses, one example sentence **taken verbatim from
the corpus**, and an English translation of that sentence. The model never
writes the Portuguese: it is given up to twenty real corpus lines
containing the entry and must return one of them unchanged, or nothing.
That is the whole point of the design -- a frequency list of spoken
Portuguese should illustrate itself with sentences people actually said,
and an invented sentence would be unverifiable.

    python -m scripts.gloss --dry-run        # 50 stratified rows -> eval/
    python -m scripts.gloss --submit         # all 10,000 via the Batch API
    python -m scripts.gloss --collect        # batch results -> out/glosses.tsv

The key is read from the environment (``ANTHROPIC_API_KEY``) and nowhere
else; it is never written to disk or into a report. The run aborts with a
message if it is missing.

Everything a response depends on -- model, prompt text, the sentences that
were offered -- is hashed into ``cache/gloss/`` beside the raw response, so
a rerun re-sends only what actually changed and two vintages of gloss can
never be mixed in one file. The cache is gitignored; ``out/glosses.tsv``
is committed.

Where the sentences come from. Pass 2 of the build keeps a digest-selected
sample of corpus lines for each of the 70,000 most frequent surface forms
(``scripts/bigrams.py``), and the lemma map says which forms belong to
which entry. Both are read from ``.cache/``, so this script needs the
corpus only in the sense that a build must already have run; it never
touches ``data/``. For a multi-word entry the phrase is matched over
*tokenized* lines, because a split enclitic (``ver lo``) is a pair of
tokens that never appears as text.

The map it reads is the one the build itself published -- backend, gate,
conventions, closure and accent folds resolved into one surface -> entry
lookup, written to ``.cache/`` by ``scripts.build``. An entry whose forms
are all rarer than the 70,000th type still has no sampled sentence; those
are rescued by one targeted pass over the corpus, picking lines by the same
digest rule pass 2 uses, cached in ``.cache/`` like any other pass.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from collections import Counter
from typing import Any, Callable, Iterable, Sequence

# Prices per million tokens, Anthropic first-party API, checked 2026-09-24.
# Only used to report what a run cost or would cost.
PRICES = {"claude-opus-5": (5.00, 25.00)}
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10
BATCH_MULTIPLIER = 0.50

FLAGS = ("vulgar", "bp-leaning", "archaic", "name-like", "uncertain")

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "gloss": {"type": "string"},
        "example_pt": {"type": "string"},
        "example_en": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string", "enum": list(FLAGS)}},
    },
    "required": ["gloss", "example_pt", "example_en", "flags"],
    "additionalProperties": False,
}

COLUMNS = ("rank", "lemma", "pos", "is_mwe", "freq_per_million", "pos_share",
           "gloss", "example_pt", "example_en", "flags")
# out/glosses.tsv says where each row came from; Stage C publishes it as the
# Gloss_Source field. The review file deliberately does not: its columns are
# an input to whoever is reading it, so they stay put. An overridden row is
# named in eval/gloss_overrides.tsv and counted in the gate report.
GLOSS_COLUMNS = COLUMNS + ("source",)
REVIEW_COLUMNS = COLUMNS + ("problem", "repaired", "attempts", "n_sentences",
                            "sentences_offered")

_DASHES = ("-", "\u2013", "\u2014")
_QUOTE_PAIRS = (('"', '"'), ("\u201c", "\u201d"), ("\u00ab", "\u00bb"),
                ("\u2018", "\u2019"), ("'", "'"))


def tidy(text: str) -> str:
    """Presentation only: drop a subtitle's leading dialogue dash and the
    quotation marks around a whole line.

    This runs after the verbatim check, never before it. The sentence stored
    in cache/gloss/ and checked against what was sent is the corpus line
    exactly as the corpus has it; what a card shows is that line without the
    dash that only means "a second speaker" and the quotes that only mean
    "this line is a quotation". A quote inside the line is left alone, and
    so is an unmatched one.
    """
    out = text.strip()
    changed = True
    while changed and out:
        changed = False
        for dash in _DASHES:
            if out.startswith(dash) and not out[len(dash):].lstrip().startswith(dash):
                out, changed = out[len(dash):].lstrip(), True
        for lo, hi in _QUOTE_PAIRS:
            if len(out) > 1 and out.startswith(lo) and out.endswith(hi):
                inner = out[len(lo):-len(hi)]
                if lo not in inner and hi not in inner:
                    out, changed = inner.strip(), True
    return out or text.strip()


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# -- the rows to gloss -------------------------------------------------------


def load_rows(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """The published rows, in rank order, with the POS share of split words."""
    from scripts import config as config_mod

    out_dir = config_mod.out_dir(cfg)
    rows: list[dict[str, Any]] = []
    for spec in cfg["output"]["files"]:
        path = out_dir / f"{spec['stem']}.tsv"
        if not path.is_file():
            raise SystemExit(f"{path} not found: run python -m scripts.build first")
        with path.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                rows.append({"rank": int(r["rank"]), "lemma": r["lemma"],
                             "pos": r["pos"], "is_mwe": r["is_mwe"] == "1",
                             "raw_freq": int(r["raw_freq"]),
                             "freq_per_million": r["freq_per_million"]})
    rows.sort(key=lambda r: r["rank"])

    totals: dict[str, int] = {}
    parts: dict[str, int] = {}
    for r in rows:
        totals[r["lemma"]] = totals.get(r["lemma"], 0) + r["raw_freq"]
        parts[r["lemma"]] = parts.get(r["lemma"], 0) + 1
    for r in rows:
        r["split"] = parts[r["lemma"]] > 1
        r["pos_share"] = r["raw_freq"] / totals[r["lemma"]] if r["split"] else 1.0
    return rows


def load_overrides(cfg: dict[str, Any],
                   rows: Sequence[dict[str, Any]] | None = None) -> dict[tuple[str, str], dict]:
    """eval/gloss_overrides.tsv: a reviewer's answer, beating the model's.

    The same shape as the other human-decision files in eval/ -- the pipeline
    reads the decision instead of being edited to match it. Only the fields a
    row fills in are taken, so a row can replace the gloss, the example, or
    both. A row that matches nothing published is an error: a typo in a lemma
    must not fail silently.
    """
    path = Path(cfg["paths"]["eval_dir"]) / cfg["gloss"]["overrides_file"]
    if not path.is_file():
        return {}
    out: dict[tuple[str, str], dict] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        body = [line for line in fh
                if line.strip() and not line.lstrip().startswith("#")]
    for row in csv.DictReader(body, delimiter="\t"):
        key = ((row.get("lemma") or "").strip(), (row.get("pos") or "").strip())
        if not key[0]:
            continue
        if key in out:
            raise SystemExit(f"{path}: {key[0]} ({key[1]}) is listed twice")
        out[key] = {k: (row.get(k) or "").strip()
                    for k in ("gloss", "example_pt", "example_en", "note", "source")}
        out[key]["source"] = out[key]["source"] or "override"
    if rows is not None:
        published = {(r["lemma"], r["pos"]) for r in rows}
        unknown = sorted(k for k in out if k not in published)
        if unknown:
            raise SystemExit(
                f"{path}: no published row for "
                + ", ".join(f"{l} ({p})" for l, p in unknown))
    return out


def apply_override(parsed: dict[str, Any], over: dict[str, str]) -> dict[str, Any]:
    """Take the fields the reviewer filled in, and nothing else."""
    out = dict(parsed)
    if over.get("gloss"):
        out["gloss"] = over["gloss"]
        out.pop("error", None)
    if over.get("example_pt"):
        out["example_pt"] = over["example_pt"]
        out["example_en"] = over.get("example_en", "")
    out["flags"] = [f for f in out.get("flags", ()) if f != "uncertain"]
    return out


# -- example sentences -------------------------------------------------------


# -- a targeted corpus pass, for entries pass 2 never sampled ---------------
#
# Pass 2 keeps sampled lines for the 70,000 most frequent surface forms, and
# for a multi-word entry only the lines that happen to contain the whole
# phrase. A handful of published entries fall outside both, and rather than
# gloss those from the headword alone they get one pass of their own, over
# the same corpus, choosing lines by the same rule.

_SCAN_TOK = None
_SCAN_SINGLES: frozenset[str] = frozenset()
_SCAN_PHRASES: tuple[tuple[str, ...], ...] = ()
_SCAN_FILTER = None
_SCAN_K = 0
_SCAN_SEED = 0


def _scan_init(tok_cfg: dict[str, Any], singles: frozenset[str],
               phrases: tuple[str, ...], prefilter: tuple[str, ...],
               k: int, seed: int) -> None:
    import re

    from scripts.tokenizer import Tokenizer

    global _SCAN_TOK, _SCAN_SINGLES, _SCAN_PHRASES, _SCAN_FILTER, _SCAN_K, _SCAN_SEED
    _SCAN_TOK = Tokenizer(dict(tok_cfg, lowercase=True))
    _SCAN_SINGLES = singles
    _SCAN_PHRASES = tuple(tuple(p.split()) for p in phrases)
    # One regex over the whole line rejects the great majority of the corpus
    # without tokenizing it. For a phrase the term is its rarest word, not
    # the phrase itself: a phrase whose tokens are only adjacent after
    # enclitic splitting never appears in the text as written.
    terms = sorted(set(singles) | set(prefilter), key=len, reverse=True)
    _SCAN_FILTER = re.compile("|".join(re.escape(t) for t in terms)) if terms else None
    _SCAN_K, _SCAN_SEED = k, seed


def _scan_chunk(lines: list[str]) -> dict[str, list[tuple[int, str]]]:
    """The best K lines per wanted surface or phrase in one chunk."""
    import heapq
    from collections import defaultdict

    from scripts.bigrams import _ctx_digest

    out: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for line in lines:
        if _SCAN_FILTER is None or not _SCAN_FILTER.search(line.lower()):
            continue
        sentence = line.strip()
        toks = _SCAN_TOK.tokenize(line)
        for token in set(toks) & _SCAN_SINGLES:
            out[token].append((_ctx_digest(_SCAN_SEED, token, sentence), sentence))
        for parts in _SCAN_PHRASES:
            n = len(parts)
            if any(toks[i:i + n] == list(parts) for i in range(len(toks) - n + 1)):
                key = " ".join(parts)
                out[key].append((_ctx_digest(_SCAN_SEED, key, sentence), sentence))
    return {t: heapq.nsmallest(_SCAN_K, v) for t, v in out.items()}


def scan_corpus(cfg: dict[str, Any], singles: Iterable[str],
                phrases: Iterable[str], prefilter: Iterable[str],
                k: int) -> dict[str, list[str]]:
    """Sample corpus lines for surfaces and phrases pass 2 did not keep.

    Selection is the same pure function of content pass 2 uses -- the K
    smallest BLAKE2b digests of (seed, key, line) -- so a rescued entry's
    sentences are drawn exactly as every other entry's were, and the result
    does not depend on how many workers ran. Cached like any other pass.
    """
    import gzip
    import heapq
    import multiprocessing as mp
    from collections import defaultdict

    from scripts import corpus

    singles, phrases = frozenset(singles), tuple(sorted(set(phrases)))
    if not singles and not phrases:
        return {}
    cache = Path(cfg["paths"]["cache_dir"]) / (
        f"gloss_rescue_{digest(str(k), cfg['corpus']['path'], *sorted(singles), *phrases)}"
        ".json.gz")
    if cache.is_file():
        _log(f"  rescue: reusing cache {cache}")
        with gzip.open(cache, "rt", encoding="utf-8") as fh:
            return json.load(fh)

    _log(f"  rescue: one corpus pass for {len(singles)} surfaces and "
         f"{len(phrases)} phrases pass 2 never sampled")
    best: dict[str, list[tuple[int, str]]] = defaultdict(list)
    started = time.monotonic()
    with mp.get_context("spawn").Pool(
        processes=cfg["run"]["workers"], initializer=_scan_init,
        initargs=(cfg["tokenizer"], singles, phrases, tuple(sorted(set(prefilter))),
                  k, cfg["run"]["seed"]),
    ) as pool:
        for i, part in enumerate(pool.imap(_scan_chunk, corpus.chunks(cfg), chunksize=1), 1):
            for key, cands in part.items():
                best[key] = heapq.nsmallest(k, best[key] + cands)
            if i % 100 == 0:
                _log(f"    rescue chunk {i:5d}  {len(best)} of "
                     f"{len(singles) + len(phrases)} keys seen "
                     f"({time.monotonic() - started:.0f}s)")
    out = {key: [line for _, line in sorted(v)] for key, v in best.items()}
    cache.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache, "wt", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, sort_keys=True)
    _log(f"  rescue: {sum(len(v) for v in out.values()):,} lines for {len(out)} keys "
         f"in {time.monotonic() - started:.0f}s")
    return out


class _CacheOnlyBackend:
    """Stands in for the lemmatizer so the cached map can be reused without
    loading Stanza. Glossing must never lemmatize anything itself."""

    def lemmatize_types(self, types, contexts=None):  # pragma: no cover
        raise SystemExit(
            "no cached lemma map for this config in .cache/: run "
            "python -m scripts.build first (the glosses reuse its caches)"
        )


class Sentences:
    """Corpus lines that may be offered as an example, per published row."""

    def __init__(self, cfg: dict[str, Any]) -> None:
        from scripts import bigrams as bigrams_mod
        from scripts import build as build_mod
        from scripts import counts as counts_mod
        from scripts import lemmas as lemmas_mod
        from scripts import serir as serir_mod
        from scripts.tokenizer import Tokenizer

        self.cfg = cfg
        self.scfg = cfg["gloss"]["sentences"]
        self._in_dictionary = lemmas_mod.in_dictionary

        build_cfg = build_mod.effective_config(cfg)
        uni = counts_mod.load(build_cfg)
        if uni is None:
            raise SystemExit("no cached unigram counts in .cache/: run "
                             "python -m scripts.build first")
        bg = bigrams_mod.load(build_cfg)
        if bg is None:
            raise SystemExit("no cached pass-2 contexts in .cache/: run "
                             "python -m scripts.build first")
        self.contexts = bg.contexts
        self.counts = uni.counts
        self.rescued: dict[str, list[str]] = {}
        self.tok = Tokenizer(dict(build_cfg["tokenizer"], lowercase=True))

        # What the build actually published each surface under: the whole
        # chain resolved into one lookup. Falling back to the raw lemma map
        # would miss every surface that reached its entry through a
        # convention, the closure or an accent fold.
        lemma_map = build_mod.load_published_map(build_cfg)
        if lemma_map is None:
            _log("  warning: no published map in .cache/ (build predates it); "
                 "falling back to the lemma map, which misses merged entries")
            lemma_map = lemmas_mod.build_lemma_map(
                build_cfg, sorted(uni.counts), bg.contexts, backend=_CacheOnlyBackend()
            )
        self.build_cfg = build_cfg
        joint = frozenset(serir_mod.FORMS) if self.scfg.get("exclude_joint_serir") else frozenset()
        self.by_lemma: dict[str, list[str]] = {}
        for surface, lemma in lemma_map.items():
            if lemma in ("ser", "ir") and surface in joint:
                continue
            self.by_lemma.setdefault(lemma, []).append(surface)
        _log(f"  sentences: {len(self.contexts):,} sampled types, "
             f"{len(self.by_lemma):,} lemmas with surfaces")

    def surfaces_of(self, row: dict[str, Any]) -> set[str]:
        """The inflected forms this entry is published from."""
        return set(self.by_lemma.get(row["lemma"], ())) | {row["lemma"]}

    def contains(self, row: dict[str, Any]) -> Callable[[str], bool]:
        """Does a sentence actually contain this entry? A phrase has to be
        there as adjacent tokens; a word, as any of its inflected forms."""
        if row["is_mwe"]:
            parts = row["lemma"].split()

            def check(text: str) -> bool:
                toks = self.tok.tokenize(text)
                return any(toks[i:i + len(parts)] == parts
                           for i in range(len(toks) - len(parts) + 1))
        else:
            forms = self.surfaces_of(row)

            def check(text: str) -> bool:
                return bool(set(self.tok.tokenize(text)) & forms)
        return check

    # -- candidates ---------------------------------------------------------

    def _phrase_lines(self, phrase: str) -> list[str]:
        """Lines whose *tokens* contain the phrase, from either constituent's
        sample. Matching on text would miss a split enclitic."""
        parts = phrase.split()
        n = len(parts)
        found: list[str] = []
        for word in dict.fromkeys(parts):
            for line in self.contexts.get(word, ()):
                toks = self.tok.tokenize(line)
                if any(toks[i:i + n] == parts for i in range(len(toks) - n + 1)):
                    found.append(line)
        return found

    def candidates(self, row: dict[str, Any]) -> list[str]:
        if row["is_mwe"]:
            lines = list(self.rescued.get(row["lemma"], ())) or self._phrase_lines(row["lemma"])
        else:
            surfaces = set(self.by_lemma.get(row["lemma"], ())) | {row["lemma"]}
            lines = [l for s in sorted(surfaces) for l in self.contexts.get(s, ())]
        return list(dict.fromkeys(lines))

    def rescue(self, rows: Sequence[dict[str, Any]]) -> int:
        """Give the entries pass 2 never sampled their own corpus pass.

        An entry ends up here when every one of its inflected forms is rarer
        than the 70,000th type, so the sampled-context pass skipped all of
        them. Rather than gloss those from the headword alone, they get the
        same treatment as everything else, one scan later.
        """
        missing = [r for r in rows if not self.candidates(r)]
        if not missing:
            return 0
        singles: set[str] = set()
        phrases: set[str] = set()
        prefilter: set[str] = set()
        for row in missing:
            if row["is_mwe"]:
                phrases.add(row["lemma"])
                # Pre-filter on the phrase's rarest word: the commonest one
                # would make the scan tokenize half the corpus.
                prefilter.add(min(row["lemma"].split(),
                                  key=lambda w: self.counts.get(w, 0)))
            else:
                singles.update(self.by_lemma.get(row["lemma"], ()))
                singles.add(row["lemma"])
        _log(f"  {len(missing)} entries have no sampled sentence: "
             f"{', '.join(r['lemma'] for r in missing[:8])}"
             f"{' ...' if len(missing) > 8 else ''}")
        found = scan_corpus(self.build_cfg, singles, phrases, prefilter,
                            self.scfg["max_per_row"] * 4)
        for key, lines in found.items():
            if " " in key:
                self.rescued[key] = lines
            else:
                self.contexts[key] = list(dict.fromkeys(
                    list(self.contexts.get(key, ())) + lines))
        still = [r for r in missing if not self.candidates(r)]
        _log(f"  rescued {len(missing) - len(still)} of {len(missing)}"
             + (f"; no corpus line found for {', '.join(r['lemma'] for r in still)}"
                if still else ""))
        return len(missing) - len(still)

    # -- filtering ----------------------------------------------------------

    def _all_caps(self, line: str) -> bool:
        letters = [c for c in line if c.isalpha()]
        return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.6

    def _proper_noun_share(self, line: str) -> float:
        words = line.split()
        if not words:
            return 0.0
        n = 0
        for i, w in enumerate(words):
            bare = w.strip("«»\"'()[[]]¿?!.,:;-–—…")
            if i and bare[:1].isupper() and not self._in_dictionary(bare.lower()):
                n += 1
        return n / len(words)

    def _edge_ellipsis(self, line: str) -> bool:
        s = line.strip()
        return s.startswith(("...", "…")) or s.endswith(("...", "…", "-", "–", "—"))

    def _clean(self, line: str, strict: bool) -> bool:
        words = line.split()
        if self.scfg.get("drop_all_caps") and self._all_caps(line):
            return False
        if self._proper_noun_share(line) > self.scfg["max_proper_noun_share"]:
            return False
        if not strict:
            return bool(words)
        if not self.scfg["min_words"] <= len(words) <= self.scfg["max_words"]:
            return False
        if self.scfg.get("drop_ellipsis_edges") and self._edge_ellipsis(line):
            return False
        return True

    def choose(self, row: dict[str, Any]) -> list[str]:
        """Up to ``max_per_row`` lines, shortest first.

        Three tiers, each used only when the one before it leaves the entry
        with nothing: the full filters; then length and mid-sentence edges
        relaxed; then no filter at all. The last tier matters for words that
        live in shouted or sung lines -- `hmm`, `mayday`, `heil` -- where
        every sampled line is upper case. Offering the model a poor line is
        not the same as publishing one: it can still decline, and the review
        file shows which entries were given nothing better.
        """
        cands = self.candidates(row)
        for strict in (True, False, None):
            kept = cands if strict is None else [l for l in cands if self._clean(l, strict)]
            if kept:
                break
        kept.sort(key=lambda l: (len(l.split()), len(l), l))
        return kept[: self.scfg["max_per_row"]]


# -- the request -------------------------------------------------------------


def system_prompt(cfg: dict[str, Any]) -> str:
    """The prompt text, with the file's explanatory header stripped."""
    text = Path(cfg["gloss"]["prompt_path"]).read_text(encoding="utf-8")
    _, _, body = text.partition("\n---\n")
    if not body.strip():
        raise SystemExit(f"{cfg['gloss']['prompt_path']}: no prompt after the '---' header")
    return body.strip() + "\n"


def digest(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def user_block(row: dict[str, Any], sentences: Sequence[str]) -> str:
    lines = [f"lemma: {row['lemma']}",
             f"pos: {row['pos']}",
             f"rank: {row['rank']} of 10000",
             f"frequency: {row['freq_per_million']} per million words"]
    if row["is_mwe"]:
        lines.append("this entry is a multi-word expression")
    if row["split"]:
        lines.append(f"share: this pos accounts for {row['pos_share']:.0%} of "
                     f"the occurrences of {row['lemma']}; the list holds the "
                     f"other reading as its own row")
    if sentences:
        lines.append("")
        lines.append("corpus sentences (copy one of these verbatim, or none):")
        lines += [f"{i}. {s}" for i, s in enumerate(sentences, 1)]
    else:
        lines.append("")
        lines.append("corpus sentences: none available for this entry; leave "
                     "example_pt and example_en empty.")
    return "\n".join(lines)


def request_params(cfg: dict[str, Any], prompt: str, row: dict[str, Any],
                   sentences: Sequence[str]) -> dict[str, Any]:
    """The Messages request, identical for the dry run and the batch: the dry
    run must exercise the shape the full run will send."""
    g = cfg["gloss"]
    params: dict[str, Any] = {
        "model": g["model"],
        "max_tokens": g["max_tokens"],
        "system": [{"type": "text", "text": prompt,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_block(row, sentences)}],
        "output_config": {"effort": g["effort"],
                          "format": {"type": "json_schema", "schema": SCHEMA}},
    }
    if g.get("thinking") == "adaptive":
        params["thinking"] = {"type": "adaptive"}
    elif g.get("thinking") == "disabled":
        params["thinking"] = {"type": "disabled"}
    return params


# -- the response cache ------------------------------------------------------


def _safe(text: str) -> str:
    keep = "".join(c if (c.isalnum() or c in "-_") else "_" for c in text)
    return keep[:48] or "_"


def cache_file(cfg: dict[str, Any], row: dict[str, Any]) -> Path:
    """One file per lemma + POS, named so a human can find it."""
    key = f"{row['lemma']}\x00{row['pos']}"
    return (Path(cfg["gloss"]["cache_dir"])
            / f"{_safe(row['lemma'])}__{_safe(row['pos'])}-{digest(key)[:8]}.json")


def cache_read(cfg: dict[str, Any], row: dict[str, Any], stamp: str) -> dict | None:
    path = cache_file(cfg, row)
    if not path.is_file():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if blob.get("stamp") != stamp:
        return None       # model, prompt or sentences changed: ask again
    parsed = blob.get("parsed", {})
    unusable = bool(parsed.get("error")) or not (parsed.get("gloss") or "").strip()
    if unusable and blob.get("attempts", 1) < cfg["gloss"]["max_attempts"]:
        return None       # refused, truncated, unparseable or empty: ask again
    return blob


def cache_read_any(cfg: dict[str, Any], row: dict[str, Any], stamp: str) -> dict | None:
    """The cached reply for this stamp even if it failed: what the run has to
    publish, or account for, when a retry never succeeded."""
    path = cache_file(cfg, row)
    if not path.is_file():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return blob if blob.get("stamp") == stamp else None


def cache_write(cfg: dict[str, Any], row: dict[str, Any], stamp: str,
                sentences: Sequence[str], response: Any, parsed: dict) -> None:
    path = cache_file(cfg, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    attempts = 1
    if path.is_file():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old = {}
        if old.get("stamp") == stamp:
            attempts = old.get("attempts", 1) + 1
            # Never let a retry that failed overwrite an answer that worked.
            if parsed.get("error") and not old.get("parsed", {}).get("error"):
                old["attempts"] = attempts
                path.write_text(json.dumps(old, ensure_ascii=False, indent=2),
                                encoding="utf-8")
                return
    blob = {
        "lemma": row["lemma"], "pos": row["pos"], "rank": row["rank"],
        "stamp": stamp, "model": cfg["gloss"]["model"],
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sentences": list(sentences),
        "attempts": attempts,
        "parsed": parsed,
        "response": response if isinstance(response, dict) else response.to_dict(),
    }
    path.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")


def stamp_for(cfg: dict[str, Any], prompt_digest: str, row: dict[str, Any],
              sentences: Sequence[str]) -> str:
    """What a cached response is only valid for.

    max_tokens is deliberately not part of it. It is a ceiling, not a
    setting that changes an answer: a reply that finished is the reply a
    higher ceiling would have given. A reply that did *not* finish carries an
    error, and an errored response is re-asked rather than reused -- see
    cache_read -- which is how raising the ceiling retries the truncated
    rows without re-billing the 9,900 that were fine.
    """
    g = cfg["gloss"]
    return digest(g["model"], str(g["effort"]), str(g.get("thinking")),
                  prompt_digest, row["lemma"], row["pos"], *sentences)


# -- talking to the API ------------------------------------------------------


def client():
    """The SDK client. The key comes from the environment and nowhere else."""
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set in the environment.\n"
            "Export it in this shell before running the glosses; this script\n"
            "reads it from the environment only and never writes it to a file."
        )
    try:
        import anthropic
    except ImportError:  # pragma: no cover
        raise SystemExit("anthropic is not installed: pip install -r requirements.txt")
    return anthropic.Anthropic()


class Usage:
    """Token totals, so a run can report what it cost."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.input = self.output = self.cache_write = self.cache_read = 0
        self.rows = self.live = 0

    def add(self, u: Any, live: bool = True) -> None:
        """Tokens for one row, whether it was just requested or replayed from
        the cache: the cost of the run is what the rows cost to produce."""
        get = u.get if isinstance(u, dict) else (lambda k: getattr(u, k, None))
        self.input += get("input_tokens") or 0
        self.output += get("output_tokens") or 0
        self.cache_write += get("cache_creation_input_tokens") or 0
        self.cache_read += get("cache_read_input_tokens") or 0
        self.rows += 1
        self.live += bool(live)

    def cost(self, batch: bool = False, cached: bool = True) -> float:
        """What these tokens cost. ``cached=False`` prices every cache read as
        a fresh input token: the worst case for a batch, whose requests need
        not land inside one another's five-minute cache window."""
        cin, cout = PRICES.get(self.model, (0.0, 0.0))
        read = self.cache_read * (CACHE_READ_MULTIPLIER if cached else 1.0)
        write = self.cache_write * (CACHE_WRITE_MULTIPLIER if cached else 1.0)
        total = ((self.input + read + write) * cin + self.output * cout) / 1e6
        return total * (BATCH_MULTIPLIER if batch else 1.0)

    def report(self, label: str, rows: int) -> list[str]:
        per = (lambda v: v / rows if rows else 0.0)
        return [
            f"{label}: {rows} rows ({self.live} sent now, "
            f"{self.rows - self.live} replayed from cache/gloss/)",
            f"  input        {self.input:>9,} tokens ({per(self.input):>7.0f}/row)",
            f"  cache write  {self.cache_write:>9,} tokens",
            f"  cache read   {self.cache_read:>9,} tokens",
            f"  output       {self.output:>9,} tokens ({per(self.output):>7.0f}/row)",
            f"  cost, prompt cache hitting   ${self.cost():.2f} standard, "
            f"${self.cost(batch=True):.2f} batch",
            f"  cost, no cache hit at all    ${self.cost(cached=False):.2f} standard, "
            f"${self.cost(batch=True, cached=False):.2f} batch",
        ]


def parse_reply(response: Any) -> dict[str, Any]:
    """The JSON object from a response, or a row flagged for review."""
    stop = getattr(response, "stop_reason", None)
    if stop == "refusal":
        det = getattr(response, "stop_details", None)
        return {"gloss": "", "example_pt": "", "example_en": "",
                "flags": ["uncertain"],
                "error": f"refusal ({getattr(det, 'category', None)})"}
    text = next((b.text for b in response.content if b.type == "text"), "")
    if stop == "max_tokens" and not text.rstrip().endswith("}"):
        return {"gloss": "", "example_pt": "", "example_en": "",
                "flags": ["uncertain"], "error": "truncated at max_tokens"}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"gloss": "", "example_pt": "", "example_en": "",
                "flags": ["uncertain"], "error": f"unparseable reply: {exc}"}
    data.setdefault("flags", [])
    for k in ("gloss", "example_pt", "example_en"):
        data.setdefault(k, "")
    return data


_ESCAPE = None


def decode_escapes(text: str) -> str:
    """Undo a doubly-escaped \\uXXXX in a reply.

    Claude occasionally emits `\\u00e3` as six literal characters inside a
    JSON string, so json.loads hands back the escape rather than the letter
    and a perfectly good corpus line stops matching the one that was sent.
    Only \\uXXXX is decoded, and only when it is there: nothing else in the
    string is touched.
    """
    global _ESCAPE
    if "\\u" not in text:
        return text
    if _ESCAPE is None:
        import re

        _ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")
    return _ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), text)


def repair(parsed: dict[str, Any], sentences: Sequence[str], contains,
           ) -> tuple[dict[str, Any], str]:
    """Make a reply publishable, or take its example away. Returns the reply
    and the name of what had to be done, empty when nothing did.

    Three things go wrong often enough to be worth handling rather than
    failing the run over, and each is handled in a way that keeps the
    published example a real corpus line:

      escape      a doubly-escaped \\uXXXX, decoded above.
      reanchored  the model tidied the line itself -- dropped the dialogue
                  dash, or the quotes -- so it no longer matches what was
                  sent. The corpus line it tidied is put back; the output is
                  tidied anyway, so nothing about the card changes.
      rewritten   the model edited the Portuguese: an accent added
                  (`tras` -> `trás`), a pronoun supplied, a clause trimmed.
                  There is no way to tell a correction from a corruption, so
                  the example goes and the entry keeps its gloss alone.
      off_target  the line is real and unedited but does not contain the
                  entry. Same treatment.
    """
    out = dict(parsed)
    what = ""
    for key in ("gloss", "example_pt", "example_en"):
        fixed = decode_escapes(out.get(key, ""))
        if fixed != out.get(key, ""):
            out[key], what = fixed, "escape"
    ex = out.get("example_pt", "")
    if ex and ex not in sentences:
        match = next((s for s in sentences if tidy(s) == tidy(ex)), None)
        if match is not None:
            out["example_pt"], what = match, what or "reanchored"
        else:
            out["example_pt"], out["example_en"] = "", ""
            out["flags"] = sorted(set(out.get("flags", [])) | {"uncertain"})
            return out, "rewritten"
    ex = out.get("example_pt", "")
    if ex and not contains(ex):
        out["example_pt"], out["example_en"] = "", ""
        out["flags"] = sorted(set(out.get("flags", [])) | {"uncertain"})
        return out, "off_target"
    return out, what


def verify(parsed: dict[str, Any], sentences: Sequence[str],
           overridden: bool = False) -> str:
    """Empty string if the row is usable, else why not. The example must be
    one of the lines we sent, character for character -- unless a reviewer
    put it there, which is a different provenance, not a broken one."""
    if parsed.get("error"):
        return parsed["error"]
    if not parsed["gloss"].strip():
        return "empty gloss"
    ex = parsed["example_pt"]
    if ex and ex not in sentences and not overridden:
        return "example_pt is not one of the sentences sent"
    if ex and not parsed["example_en"].strip():
        return "example_pt without a translation"
    bad = [f for f in parsed["flags"] if f not in FLAGS]
    if bad:
        return f"unknown flag(s): {', '.join(bad)}"
    return ""


def gloss_rows(cfg: dict[str, Any], rows: Sequence[dict[str, Any]],
               sents: Sentences, progress: bool = True) -> tuple[list[dict], Usage]:
    """One synchronous request per row, cache first. Used by --dry-run; the
    full 10,000 go through --submit instead."""
    prompt = system_prompt(cfg)
    pdig = digest(prompt)
    usage = Usage(cfg["gloss"]["model"])
    overrides = load_overrides(cfg)
    cli = None
    results = []
    for i, row in enumerate(rows, 1):
        sentences = sents.choose(row)
        stamp = stamp_for(cfg, pdig, row, sentences)
        blob = cache_read(cfg, row, stamp)
        if blob is None:
            cli = cli or client()
            params = request_params(cfg, prompt, row, sentences)
            response = cli.messages.create(**params)
            parsed = parse_reply(response)
            cache_write(cfg, row, stamp, sentences, response, parsed)
            usage.add(response.usage)
            blob = {"parsed": parsed, "sentences": sentences}
            if progress:
                _log(f"    {i}/{len(rows)}  {row['lemma']} ({row['pos']})")
        else:
            usage.add(blob.get("response", {}).get("usage", {}), live=False)
            if progress:
                _log(f"    {i}/{len(rows)}  {row['lemma']} ({row['pos']})  [cached]")
        got = blob.get("sentences", sentences)
        parsed, repaired = repair(blob["parsed"], got, sents.contains(row))
        over = overrides.get((row["lemma"], row["pos"]))
        if over:
            parsed = apply_override(parsed, over)
        results.append({**row, **parsed, "sentences": got, "repaired": repaired,
                        "attempts": blob.get("attempts", 1),
                        "source": over["source"] if over else "model",
                        "override_note": over["note"] if over else "",
                        "problem": verify(parsed, got, overridden=bool(over))})
    return results, usage


# -- the full run, through the Batch API ------------------------------------


def submit(cfg: dict[str, Any], rows: Sequence[dict[str, Any]],
           sents: Sentences) -> list[str]:
    """Send every row that is not already cached, as a few batches.

    Split rather than sent whole: the 10,000 requests come to about 50 MB,
    and several smaller uploads fail more gracefully than one large one.
    A row already in cache/gloss/ under the current stamp is not re-sent, so
    resubmitting after a partial failure costs only the rows that are missing.
    """
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    prompt = system_prompt(cfg)
    pdig = digest(prompt)
    pending: list[tuple[str, dict, str, list[str]]] = []
    for row in rows:
        sentences = sents.choose(row)
        stamp = stamp_for(cfg, pdig, row, sentences)
        if cache_read(cfg, row, stamp) is not None:
            continue
        cid = f"r{row['rank']}-{digest(row['lemma'], row['pos'])[:8]}"
        pending.append((cid, row, stamp, sentences))
    if not pending:
        raise SystemExit("every row is already cached: run --collect")

    cli = client()
    size = cfg["gloss"]["batch"]["chunk"]
    batches = []
    for i in range(0, len(pending), size):
        part = pending[i:i + size]
        batch = cli.messages.batches.create(requests=[
            Request(custom_id=cid,
                    params=MessageCreateParamsNonStreaming(
                        **request_params(cfg, prompt, row, sentences)))
            for cid, row, stamp, sentences in part])
        batches.append({
            "batch_id": batch.id, "requests": len(part),
            "rows": {cid: {"rank": row["rank"], "lemma": row["lemma"],
                           "pos": row["pos"], "stamp": stamp,
                           "sentences": sentences}
                     for cid, row, stamp, sentences in part},
        })
        _log(f"  batch {batch.id}: {len(part):,} requests")

    state = Path(cfg["gloss"]["batch"]["state_file"])
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(
        {"model": cfg["gloss"]["model"], "prompt_digest": pdig,
         "submitted": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "requests": len(pending), "batches": batches},
        ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"{len(pending):,} requests in {len(batches)} batches; state in {state}")
    return [b["batch_id"] for b in batches]


def collect(cfg: dict[str, Any], rows: Sequence[dict[str, Any]], sents: Sentences,
            wait: bool = True) -> tuple[list[dict], Usage]:
    """Poll every batch, write each raw response into the cache, then build the
    results from the cache -- so a collect can be repeated, and a rerun after
    a resubmission picks up both halves."""
    state_path = Path(cfg["gloss"]["batch"]["state_file"])
    if not state_path.is_file():
        raise SystemExit(f"no batch state in {state_path}: run --submit first")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    cli = client()
    usage = Usage(cfg["gloss"]["model"])
    by_rank = {r["rank"]: r for r in rows}
    failures: list[tuple[str, str]] = []

    for entry in state["batches"]:
        batch = cli.messages.batches.retrieve(entry["batch_id"])
        while wait and batch.processing_status != "ended":
            counts = batch.request_counts
            _log(f"  {batch.id}: {batch.processing_status}, "
                 f"{counts.processing:,} processing, {counts.succeeded:,} done")
            time.sleep(cfg["gloss"]["batch"]["poll_seconds"])
            batch = cli.messages.batches.retrieve(entry["batch_id"])
        if batch.processing_status != "ended":
            _log(f"  {batch.id} is {batch.processing_status}, not ended: skipped")
            continue
        n = 0
        for result in cli.messages.batches.results(batch.id):
            meta = entry["rows"].get(result.custom_id)
            if meta is None:
                failures.append((result.custom_id, "unknown custom_id"))
                continue
            if result.result.type != "succeeded":
                failures.append((result.custom_id, result.result.type))
                continue
            row = by_rank.get(meta["rank"])
            if row is None:
                failures.append((result.custom_id, "rank is no longer published"))
                continue
            message = result.result.message
            cache_write(cfg, row, meta["stamp"], meta["sentences"], message,
                        parse_reply(message))
            n += 1
        _log(f"  {batch.id}: {n:,} responses cached")
    for cid, why in failures[:20]:
        _log(f"  result {cid}: {why}")
    if len(failures) > 20:
        _log(f"  ... and {len(failures) - 20:,} more failed results")

    return from_cache(cfg, rows, sents, usage)


def from_cache(cfg: dict[str, Any], rows: Sequence[dict[str, Any]], sents: Sentences,
               usage: "Usage | None" = None) -> tuple[list[dict], Usage]:
    """Build the finished rows from cache/gloss/ alone -- no API call.

    Everything published goes through here, so re-rendering after a change to
    the repair rules costs nothing and the raw responses stay untouched on
    disk as the record of what the model actually said.
    """
    pdig = digest(system_prompt(cfg))
    usage = usage or Usage(cfg["gloss"]["model"])
    overrides = load_overrides(cfg, rows)
    results, missing = [], []
    for row in rows:
        sentences = sents.choose(row)
        stamp = stamp_for(cfg, pdig, row, sentences)
        blob = cache_read(cfg, row, stamp)
        if blob is None:
            blob = cache_read_any(cfg, row, stamp)   # an errored reply still counts
        if blob is None:
            missing.append(row)
            continue
        usage.add(blob.get("response", {}).get("usage", {}), live=False)
        parsed, repaired = repair(blob["parsed"], blob["sentences"], sents.contains(row))
        over = overrides.get((row["lemma"], row["pos"]))
        if over:
            parsed = apply_override(parsed, over)
        results.append({**row, **parsed, "sentences": blob["sentences"],
                        "repaired": repaired, "attempts": blob.get("attempts", 1),
                        "source": over["source"] if over else "model",
                        "override_note": over["note"] if over else "",
                        "problem": verify(parsed, blob["sentences"],
                                          overridden=bool(over))})
    if missing:
        _log(f"  {len(missing):,} rows have no response: rerun --submit, then --collect")
    return results, usage


# -- output ------------------------------------------------------------------


def write_tsv(path: Path, results: Sequence[dict[str, Any]],
              show_sentences: bool = False) -> None:
    """Write the gloss rows. The review file *merges*: any column a reviewer
    has added to it is carried over, matched on lemma and POS.

    Without that, regenerating the review file silently destroys the work it
    exists to collect -- it wiped 257 native-speaker verdicts once. Every
    other generated file in eval/ merges rather than overwrites for the same
    reason (see scripts/make_proper_noun_review.py).
    """
    cols = list(REVIEW_COLUMNS if show_sentences else GLOSS_COLUMNS)
    prior: dict[tuple[str, str], dict[str, str]] = {}
    if show_sentences and path.is_file():
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            extra = [c for c in (reader.fieldnames or []) if c not in cols]
            for row in reader:
                prior[(row["lemma"], row["pos"])] = row
        if extra:
            cols += extra
            keys = {(r["lemma"], r["pos"]) for r in results}
            lost = [k for k, row in prior.items()
                    if k not in keys and any((row.get(c) or "").strip() for c in extra)]
            if lost:
                _log(f"  warning: {len(lost)} reviewed row(s) are no longer in the "
                     f"sample and their {', '.join(extra)} would be dropped: "
                     + ", ".join(f"{l} ({p})" for l, p in sorted(lost)[:8]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        # csv defaults, as everywhere else in the pipeline: a sentence that
        # contains a quotation mark is quoted rather than altered.
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in results:
            out = [r["rank"], r["lemma"], r["pos"], "1" if r["is_mwe"] else "0",
                   r["freq_per_million"],
                   f"{r['pos_share']:.3f}" if r["split"] else "",
                   r["gloss"], tidy(r["example_pt"]), tidy(r["example_en"]),
                   " ".join(r["flags"])]
            if show_sentences:
                out += [r.get("problem", ""), r.get("repaired", ""),
                        r.get("attempts", 1), len(r["sentences"]),
                        " | ".join(r["sentences"])]
            else:
                out.append(r.get("source", "model"))
            if len(out) < len(cols):
                kept = prior.get((r["lemma"], r["pos"]), {})
                out += [kept.get(c, "") for c in cols[len(out):]]
            w.writerow(["" if v is None else " ".join(str(v).split()) for v in out])


# -- the dry run -------------------------------------------------------------


def kept_feminine_nouns(cfg: dict[str, Any]) -> set[str]:
    """Feminine person nouns the reviewer kept as their own entry (convention 2)."""
    path = Path(cfg["paths"]["eval_dir"]) / "gender_pairs.tsv"
    if not path.is_file():
        return set()
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["feminine"] for r in csv.DictReader(fh, delimiter="\t")
                if (r.get("jim_decision") or "").strip() == "keep"}


def dryrun_sample(cfg: dict[str, Any], rows: Sequence[dict[str, Any]]) -> list[dict]:
    """A stratified 50 rows: deterministic given the seed, and guaranteed to
    include the cases most likely to break -- split POS, multi-word entries,
    and a feminine noun the conventions keep separate from its masculine."""
    d = cfg["gloss"]["dryrun"]
    rng = random.Random(d["seed"])
    strata = [(lo, hi, n) for lo, hi, n in d["strata"]]
    quota = {i: n for i, (_, _, n) in enumerate(strata)}
    chosen: dict[int, dict] = {}

    def stratum_of(row: dict) -> int | None:
        for i, (lo, hi, _) in enumerate(strata):
            if lo <= row["rank"] <= hi:
                return i
        return None

    def take(pool: Sequence[dict], n: int) -> None:
        order = list(pool)
        rng.shuffle(order)
        taken = 0
        for row in order:
            if taken >= n:
                break
            i = stratum_of(row)
            if i is None or quota[i] <= 0 or row["rank"] in chosen:
                continue
            chosen[row["rank"]] = row
            quota[i] -= 1
            taken += 1
        if taken < n:
            _log(f"  warning: only {taken} of {n} rows available for one requirement")

    feminine = kept_feminine_nouns(cfg)
    req = d["require"]
    take([r for r in rows if r["split"]], req["multi_pos"])
    take([r for r in rows if r["is_mwe"]], req["mwe"])
    take([r for r in rows if r["pos"] == "noun" and r["lemma"] in feminine],
         req["kept_feminine_nouns"])
    for i, (lo, hi, _) in enumerate(strata):
        pool = [r for r in rows if lo <= r["rank"] <= hi and r["rank"] not in chosen]
        take(pool, quota[i])
    return [chosen[k] for k in sorted(chosen)]


def review_sample(cfg: dict[str, Any],
                  results: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Everything a learner meets first, plus an even spread over the rest.

    The top of the list is where a wrong gloss does the most damage and where
    the words are most polysemous, so all of it is reviewed; below that the
    sample is spread evenly by rank so no part of the list goes unlooked-at.
    """
    r = cfg["gloss"]["review"]
    through, want, bands = r["all_through_rank"], r["sampled"], r["bands"]
    rng = random.Random(r["seed"])
    chosen = {x["rank"]: x for x in results if x["rank"] <= through}
    rest = [x for x in results if x["rank"] > through]
    if rest and want:
        lo, hi = min(x["rank"] for x in rest), max(x["rank"] for x in rest)
        width = (hi - lo + 1) / bands
        per = [want // bands + (1 if i < want % bands else 0) for i in range(bands)]
        for i in range(bands):
            band = [x for x in rest
                    if lo + i * width <= x["rank"] < lo + (i + 1) * width
                    and x["rank"] not in chosen]
            band.sort(key=lambda x: x["rank"])
            for x in rng.sample(band, min(per[i], len(band))):
                chosen[x["rank"]] = x
    return [chosen[k] for k in sorted(chosen)]


# -- CLI ---------------------------------------------------------------------


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config.yaml")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="gloss the stratified sample into eval/")
    mode.add_argument("--submit", action="store_true",
                      help="send every uncached row as one batch")
    mode.add_argument("--collect", action="store_true",
                      help="poll the batch and write out/glosses.tsv")
    mode.add_argument("--estimate", action="store_true",
                      help="count input tokens for the full run; no glossing")
    mode.add_argument("--retry", action="store_true",
                      help="re-ask, one request each, the rows whose cached "
                           "reply was refused, truncated or unparseable")
    mode.add_argument("--report", action="store_true",
                      help="rebuild the outputs and the gates from the cache; "
                           "no API call")
    mode.add_argument("--rescue", action="store_true",
                      help="only the corpus pass for entries pass 2 never "
                           "sampled; caches its result and stops")
    ap.add_argument("--no-wait", action="store_true",
                    help="--collect: do not poll, take whatever is ready")
    args = ap.parse_args()

    cfg = config_mod.load(args.config)
    g = cfg["gloss"]
    rows = load_rows(cfg)
    _log(f"{len(rows):,} published rows, "
         f"{len({r['lemma'] for r in rows}):,} distinct entries")
    sents = Sentences(cfg)
    sents.rescue(rows)

    if args.rescue:
        for row in rows:
            if not sents.choose(row):
                print(f"still no sentence: {row['rank']} {row['lemma']} ({row['pos']})")
        print("rescue pass cached")
        return

    if args.estimate:
        prompt = system_prompt(cfg)
        cli = client()
        n_none = 0
        total = 0
        for row in rows:
            s = sents.choose(row)
            n_none += not s
            total += len(s)
        sample = rows[:: max(len(rows) // 40, 1)]
        counted = 0
        for row in sample:
            p = request_params(cfg, prompt, row, sents.choose(row))
            counted += cli.messages.count_tokens(
                model=p["model"], system=p["system"], messages=p["messages"]
            ).input_tokens
        per = counted / len(sample)
        print(f"rows with no example sentence: {n_none}")
        print(f"sentences offered: {total:,} ({total / len(rows):.1f} per row)")
        print(f"input tokens: {per:,.0f} per row on {len(sample)} sampled rows "
              f"=> {per * len(rows):,.0f} for {len(rows):,} rows")
        return

    if args.submit:
        submit(cfg, rows, sents)
        print("submitted; run --collect when the batch has ended")
        return

    if args.retry:
        pdig = digest(system_prompt(cfg))
        todo = []
        for row in rows:
            sentences = sents.choose(row)
            stamp = stamp_for(cfg, pdig, row, sentences)
            if cache_read(cfg, row, stamp) is None:
                todo.append(row)
        if not todo:
            print("nothing to retry")
            return
        _log(f"retrying {len(todo)} rows")
        results, usage = gloss_rows(cfg, todo, sents)
        for r in results:
            state = r["problem"] or (f"repaired: {r['repaired']}" if r["repaired"]
                                     else "ok")
            print(f"  {r['rank']} {r['lemma']} ({r['pos']}) attempt "
                  f"{r['attempts']}: {state}")
        print("\n".join(usage.report("retry", len(results))))
        print("now rerun --report to rebuild the outputs and the gates")
        return

    if args.collect or args.report:
        from scripts import gloss_gates

        if args.report:
            results, usage = from_cache(cfg, rows, sents)
        else:
            results, usage = collect(cfg, rows, sents, wait=not args.no_wait)
        out = config_mod.out_dir(cfg) / g["out_file"]
        write_tsv(out, results)
        print(f"{out}: {len(results):,} rows")

        res = gloss_gates.run(results, rows, cfg, sents.tok.tokenize, sents.surfaces_of)
        lines = usage.report("this run", len(results))
        fixed = Counter(r["repaired"] for r in results if r["repaired"])
        lines.append("  repaired: " + (", ".join(f"{k} {n:,}" for k, n
                                                in sorted(fixed.items()))
                                      if fixed else "nothing"))
        report = Path(cfg["paths"]["reports_dir"]) / g["gates_file"]
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(gloss_gates.render(res, cfg, lines), encoding="utf-8")
        print(f"{report}: "
              + ", ".join(f"{k} {v.n:,}" for k, v in res["gates"].items() if v.n))

        review = review_sample(cfg, results)
        rpath = Path(cfg["paths"]["eval_dir"]) / g["review"]["file"]
        write_tsv(rpath, review, show_sentences=True)
        print(f"{rpath}: {len(review):,} rows for review")

        print("\n".join(lines))
        print("flags: " + ", ".join(f"{f} {res['flags'].get(f, 0):,}"
                                   for f in gloss_gates.FLAGS)
              + f", none {res['unflagged']:,}")
        # Reports first, then fail: a failing run must leave its evidence.
        if res["failed"]:
            raise SystemExit("gloss gate failed: " + ", ".join(res["failed"]))
        print("every fatal gate passed")
        return

    # --dry-run
    sample = dryrun_sample(cfg, rows)
    _log(f"dry run: {len(sample)} rows "
         f"({sum(r['split'] for r in sample)} split POS, "
         f"{sum(r['is_mwe'] for r in sample)} MWEs)")
    results, usage = gloss_rows(cfg, sample, sents)
    path = Path(cfg["paths"]["eval_dir"]) / g["dryrun"]["file"]
    write_tsv(path, results, show_sentences=True)
    print(f"{path}: {len(results)} rows")
    problems = [r for r in results if r["problem"]]
    print(f"problems: {len(problems)}")
    for r in problems:
        print(f"  {r['rank']} {r['lemma']} ({r['pos']}): {r['problem']}")
    print("\n".join(usage.report("dry run", len(results))))
    if usage.rows:
        n = len(rows)
        lo = usage.cost(batch=True) / usage.rows * n
        hi = usage.cost(batch=True, cached=False) / usage.rows * n
        print(f"projected for all {n:,} rows through the Batch API: "
              f"${lo:.2f} if the prompt cache holds, ${hi:.2f} if it never does "
              f"(${usage.cost() / usage.rows * n:.2f}-"
              f"${usage.cost(cached=False) / usage.rows * n:.2f} without the batch discount)")


if __name__ == "__main__":
    main()
