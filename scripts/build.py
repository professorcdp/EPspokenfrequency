"""Pipeline entry point.

    python -m scripts.build --config config.yaml
    python -m scripts.build --sample 2000000          # dev run
    python -m scripts.build --set fixes.diacritic_folding=true --stage 2

Runs the five README steps in order, writes every output named in the
config, and produces COMPARISON.md, QUALITY.md and build_stats.json.
Outputs go to paths.out_dir; `out/` is never written to.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from scripts import bigrams as bigrams_mod
from scripts import compare as compare_mod
from scripts import config as config_mod
from scripts import conventions as conventions_mod
from scripts import counts as counts_mod
from scripts import emit as emit_mod
from scripts import eval_lemmas as eval_mod
from scripts import filters as filters_mod
from scripts import occurrence as occurrence_mod
from scripts import pos as pos_mod
from scripts import lemmas as lemmas_mod
from scripts import quality as quality_mod
from scripts.postag import PosTagger


FIX_FLAGS = (
    "diacritic_folding", "accent_variant_folding", "bp_after_folding",
    "extended_proper_nouns", "mwe_constituent_check", "lemma_closure",
    "plural_folding", "split_enclitics", "english_plurals_foreign",
    "split_ambiguous", "short_token_rule", "proper_noun_review",
)
# fixes.cap_sentence_starts is deliberately not here: tried and rejected
# (see scripts/data/quality_notes.md). The code stays behind the flag.


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def aggregate_lemmas(
    surface_counts: dict[str, int],
    lemma_map: dict[str, str],
    splits: dict[str, Counter] | None = None,
    redirect=lambda lemma: lemma,
) -> dict[str, int]:
    """Sum surface counts onto their lemmas, deterministically.  A surface
    with a per-occurrence split has its count divided across lemmas."""
    out: Counter = Counter()
    splits = splits or {}
    for surface in sorted(surface_counts):
        count = surface_counts[surface]
        if surface in splits:
            for lemma, share in occurrence_mod.apportion(count, splits[surface]).items():
                out[redirect(lemma)] += share
        else:
            out[lemma_map.get(surface, surface)] += count
    return dict(out)


def stage1_overrides(cfg: dict[str, Any]) -> dict[str, Any]:
    """Everything that makes stage 1 the April pipeline again: every fix
    off, simplemma alone, and a gate that only warns."""
    out: dict[str, Any] = {f"fixes.{k}": False for k, v in cfg["fixes"].items()
                           if isinstance(v, bool)}
    out["quality.fail_on_suspects"] = False
    out["lemmatizer.backend"] = "simplemma"
    out["lemmatizer.tiered.enabled"] = False
    return out


def effective_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """Settings a stage implies.  Stage 1 keeps the tokenizer exactly as the
    original pipeline ran it; stage 2 turns enclitic splitting on when
    fixes.split_enclitics is set.  Every cache is keyed on the tokenizer, so
    the two stages never share a stale cache."""
    if cfg["run"]["stage"] >= 2 and cfg["fixes"].get("split_enclitics"):
        cfg = config_mod.with_overrides(cfg, {"tokenizer.split_enclitics": True})
    if cfg["run"]["stage"] >= 2 and cfg["fixes"].get("repair_glued_enclitics"):
        cfg = config_mod.with_overrides(cfg, {"tokenizer.repair_glue": True})
    return cfg


def published_map_path(cfg: dict[str, Any]) -> Path:
    """Where the surface -> published lemma map is cached.

    The map is a by-product of the gold-set scoring, and the only place the
    whole chain -- backend, gate, conventions, closure, accent folds -- is
    resolved into one lookup. scripts/gloss.py needs it to find a published
    entry's corpus sentences, so it is written out rather than thrown away.
    Keyed on the settings that shape it, so it can never be read against a
    different build.
    """
    material = {k: cfg[k] for k in ("tokenizer", "lemmatizer", "conventions",
                                    "fixes", "filters", "serir")}
    material["stage"] = cfg["run"]["stage"]
    material["sample_lines"] = cfg["run"].get("sample_lines")
    d = hashlib.sha256(json.dumps(material, sort_keys=True,
                                  ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    return Path(cfg["paths"]["cache_dir"]) / f"published_{d}.tsv.gz"


def save_published_map(cfg: dict[str, Any], published: Mapping[str, str]) -> Path:
    import gzip

    path = published_map_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        for surface in sorted(published):
            fh.write(f"{surface}\t{published[surface]}\n")
    return path


def load_published_map(cfg: dict[str, Any]) -> dict[str, str] | None:
    import gzip

    path = published_map_path(cfg)
    if not path.is_file():
        return None
    out: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            surface, _, lemma = line.rstrip("\n").partition("\t")
            out[surface] = lemma
    return out


def run(cfg: dict[str, Any]) -> dict[str, Any]:
    cfg = effective_config(cfg)
    started = time.monotonic()
    out_dir = config_mod.out_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = config_mod.reports_dir(cfg)
    rep_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {"stage": cfg["run"]["stage"]}

    import simplemma

    stats["simplemma_version"] = simplemma.__version__

    # -- step 1: tokenize and count ---------------------------------------
    _log("step 1: unigram pass")
    uni = counts_mod.unigram_pass_cached(cfg)
    stats["fingerprint"] = uni.fingerprint()
    fingerprint_rows = counts_mod.compare_fingerprint(uni, cfg)
    _log(f"  {uni.n_tokens:,} tokens, {uni.n_types:,} types")

    # -- step 3 (scan): bigrams, contexts, casing -------------------------
    # Runs before step 2 because the lemmatizer wants the sampled contexts.
    _log("step 3a: bigram + context pass")
    bg = bigrams_mod.bigram_pass_cached(cfg, uni.counts)
    stats["bigram_pairs"] = len(bg.pairs)
    stats["context_types"] = len(bg.contexts)
    _log(f"  {len(bg.pairs):,} distinct pairs, contexts for {len(bg.contexts):,} types")

    # -- step 2: lemmatize -------------------------------------------------
    _log(f"step 2: lemmatize ({cfg['lemmatizer']['backend']})")
    types = sorted(uni.counts)
    lem = cfg["lemmatizer"]

    tier = lem.get("tiered", {})
    min_count = None
    if tier.get("enabled"):
        limit = max(hi for _, hi in cfg["output"]["bands"])
        min_count = tier.get("primary_min_count")
        if min_count is None:
            # Count at the last published rank, as a surface-level proxy,
            # divided by the safety factor. Conservative: surfaces well
            # below the cutoff still qualify, because several surfaces can
            # aggregate onto one lemma.
            ordered = sorted(uni.counts.values(), reverse=True)
            at_limit = ordered[limit - 1] if len(ordered) >= limit else 1
            min_count = max(at_limit // tier.get("safety_factor", 10), 1)
        stats["tier_min_count"] = min_count
        _log(f"  tier threshold: surface count >= {min_count:,}")

    # One Stanza tagging pass over every frequent word's sample sentences
    # supplies lemmas, per-occurrence splits and POS alike.
    tags: dict | None = None
    vote_filter = None
    shape_filter = None
    if lem["backend"] == "gated" and lem["gate"]["primary"] == "stanza_tags":
        tier_types = [t for t in types if uni.counts[t] >= (min_count or 1)]
        tags = occurrence_mod.tag_cached(tier_types, bg.contexts, cfg)
        stats["tagged_types"] = sum(1 for t in tier_types if tags.get(t))
        stats["tagged_sentences"] = sum(len(v) for v in tags.values())
        is_verb = pos_mod.verb_lemmas(tags)
        closed = frozenset(PosTagger.load().closed)
        if lem.get("tags_vote_filter") == "consistency":
            vote_filter = lambda s, l, u: pos_mod.consistent(s, l, u, is_verb, closed)
            shape_filter = lambda s, l, u: pos_mod.consistent_shape(
                s, l, u, is_verb, closed)
        backend = lemmas_mod.GatedBackend(
            lemmas_mod.TagsBackend(tags, vote_filter),
            lemmas_mod.SimplemmaBackend(),
            lem.get("spellchecker_lang", "pt"),
        )
    else:
        backend = lemmas_mod.get_backend(lem["backend"], cfg)
    if tier.get("enabled"):
        backend = lemmas_mod.TieredBackend(
            backend, lemmas_mod.SimplemmaBackend(), uni.counts, min_count
        )

    lemma_map = lemmas_mod.build_lemma_map(cfg, types, bg.contexts, backend=backend)

    conv_log = None
    if cfg["run"]["stage"] >= 2 and cfg["conventions"].get("enabled"):
        # Before closure: closure uses the map as its own oracle, so it then
        # respects the conventions instead of undoing them.
        simple = lemmas_mod.SimplemmaBackend()
        cache: dict[str, str] = {}

        def relemmatize(word: str) -> str:
            if word not in cache:
                cache[word] = simple.lemmatize_types([word])[word]
            return cache[word]

        lemma_map, conv_log = conventions_mod.apply(
            lemma_map, cfg, lemmas_mod.in_dictionary, relemmatize
        )
        stats["conventions"] = conv_log.summary(uni.counts)
        for name, info in stats["conventions"].items():
            _log(f"  convention {name}: {info['surfaces']:,} surfaces, "
                 f"{info['tokens']:,} tokens")

    # Per-occurrence resolution: participles and fomos-type forms.
    splits: dict[str, Counter] = {}
    joint_splits: dict[str, Counter] = {}
    split_protected: set[str] = set()
    if cfg["run"]["stage"] >= 2 and cfg["fixes"].get("split_ambiguous"):
        tier_min = stats.get("tier_min_count") or cfg["lemmatizer"]["tiered"]["primary_min_count"]
        cands = occurrence_mod.candidates(uni.counts, cfg, tier_min)
        _log(f"  per-occurrence: {len(cands):,} candidate surfaces (count >= {tier_min})")
        if tags is not None:
            tagged = {c: tags.get(c, []) for c in cands}
        else:
            tagged = occurrence_mod.tag_cached(cands, bg.contexts, cfg)
        simple = lemmas_mod.SimplemmaBackend()
        sm = lambda w: simple.lemmatize_types([w])[w]
        joint = occurrence_mod.resolve_joint(tagged, lemma_map, cfg,
                                             lemmas_mod.in_dictionary, sm,
                                             consistent=shape_filter)
        for surface, j in joint.items():
            norm_joint: Counter = Counter()
            for (lemma, upos), n in j.items():
                norm_joint[(conventions_mod.normalize_lemma(
                    lemma, cfg, lemmas_mod.in_dictionary, sm), upos)] += n
            joint_splits[surface] = norm_joint
            norm = occurrence_mod.lemma_votes(norm_joint)
            splits[surface] = norm
            lemma_map[surface] = sorted(norm, key=lambda l: (-norm[l], l))[0]
            for lemma in norm:
                if lemma in (occurrence_mod.adjective_form(surface), occurrence_mod.noun_form(surface)):
                    split_protected.add(lemma)
        # ser / ir: the tagger cannot separate them, so foi/fui/fomos/foram/
        # fora are split by the next-word rule instead -- but only if the rule,
        # exactly as it now stands, has been scored above the threshold.
        sc = cfg["serir"]
        if sc.get("apply"):
            from scripts import serir as serir_mod

            score = serir_mod.load_score("reports/serir_scores.md")
            ok = (score is not None and score["accuracy"] >= sc["min_accuracy"]
                  and score["rule_digest"] == serir_mod.rule_digest(cfg))
            if not ok:
                _log("  ser/ir: rule NOT applied -- no current score at or above "
                     f"{sc['min_accuracy']:.0%} (run python -m scripts.serir --score)")
            else:
                serir_joint = serir_mod.counts_joint(cfg, _log)
                stats["serir"] = {}
                for form, j in serir_joint.items():
                    if not j:
                        continue
                    joint_splits[form] = j
                    splits[form] = occurrence_mod.lemma_votes(j)
                    lemma_map[form] = sorted(splits[form], key=lambda l: (-splits[form][l], l))[0]
                    votes = splits[form]
                    tot = sum(votes.values())
                    stats["serir"][form] = {l: round(v / tot, 4) for l, v in sorted(votes.items())}
                _log("  ser/ir: rule applied (score "
                     f"{score['accuracy']:.1%}): " + ", ".join(
                         f"{f} ser {v.get('ser', 0):.0%}/ir {v.get('ir', 0):.0%}"
                         for f, v in stats["serir"].items()))

        multi = {s: v for s, v in splits.items() if len(v) > 1}
        stats["split_surfaces"] = len(splits)
        stats["split_multi_lemma"] = len(multi)
        stats["split_tokens"] = sum(uni.counts[s] for s in multi)
        _log(f"  per-occurrence: {len(splits):,} surfaces resolved, {len(multi):,} split "
             f"across lemmas ({stats['split_tokens']:,} tokens)")

    closure_redirect: dict[str, str] = {}
    if cfg["fixes"].get("lemma_closure"):
        protected = frozenset(split_protected)
        plural_rule = None
        if cfg["run"]["stage"] >= 2:
            protected |= frozenset(conventions_mod.protected_forms(cfg)
                                   if cfg["conventions"].get("enabled") else ())
        if cfg["run"]["stage"] >= 2 and cfg["fixes"].get("plural_folding"):
            tantum = set(cfg["fixes"].get("plurale_tantum", ()))
            closed = set(PosTagger.load().closed)
            from scripts.quality import singular_candidates

            # Lemma counts before closure, to judge whether a candidate
            # plural really is the plural of its candidate singular.
            est: Counter = Counter()
            for surface, count in uni.counts.items():
                if surface in splits:
                    for lemma, share in occurrence_mod.apportion(count, splits[surface]).items():
                        est[lemma] += share
                else:
                    est[lemma_map.get(surface, surface)] += count
            max_ratio = cfg["fixes"].get("plural_max_ratio", 5)
            min_sg = cfg["fixes"].get("plural_min_singular_count", 1000)
            in_dict = lemmas_mod.in_dictionary

            def plural_rule(lemma, inventory):
                # Guards, each learned from a real misfire on the full run:
                #   closed class   nós -> nó, pois -> poi, três -> trê
                #   real singular  país -> *paí, depois -> *depoi (junk tail
                #                  lemmas are in the inventory)
                #   frequency      deus (750k) -> deu, férias -> féria: a
                #                  "plural" far commoner than its "singular"
                #                  is not its plural
                # The singular must be a real word: in the PT dictionary, or
                # common enough in the corpus not to be tail junk (elfo,
                # gangue and slang are missing from the dictionary; *paí and
                # *depoi have a handful of occurrences).
                if lemma in tantum or lemma in closed:
                    return None
                for sg in singular_candidates(lemma, inventory):
                    if sg in closed:
                        continue
                    if not (in_dict(sg) or est.get(sg, 0) >= min_sg):
                        continue
                    if est.get(lemma, 0) > max_ratio * max(est.get(sg, 0), 1):
                        continue
                    return sg
                return None

        lemma_map, redirects = lemmas_mod.close_lemma_map(
            lemma_map, lemmas_mod.SimplemmaBackend(), bg.contexts,
            protected=protected, plural_rule=plural_rule,
        )
        closure_redirect = dict(redirects)
        stats["lemma_closure_redirects"] = len(redirects)
        _log(f"  closure: merged {len(redirects):,} lemmas onto other entries")

    def follow(lemma: str) -> str:
        seen = set()
        while lemma in closure_redirect and lemma not in seen:
            seen.add(lemma)
            lemma = closure_redirect[lemma]
        return lemma

    lemma_counts = aggregate_lemmas(uni.counts, lemma_map, splits, follow)
    _log(f"  {len(lemma_counts):,} lemmas from {len(types):,} types")

    # -- step 3 (score): MWEs ---------------------------------------------
    _log("step 3b: MWE scoring")
    mwes = bigrams_mod.score_mwes(cfg, bg, uni.counts)
    stats["mwes_retained"] = len(mwes)
    _log(f"  {len(mwes):,} MWEs retained")

    # -- step 4: filters ---------------------------------------------------
    _log("step 4: filters")
    fold_log: list = []
    if cfg["fixes"].get("diacritic_folding") or cfg["fixes"].get("accent_variant_folding"):
        lemma_counts, fold_log = filters_mod.fold_diacritics(
            lemma_counts, cfg, lemmas_mod.in_dictionary
        )
        stats["diacritic_folded"] = len(fold_log)
        _log(f"  folded {len(fold_log):,} accent variants")

    cap_ratios = {w: bg.cap_ratio(w) for w in lemma_counts}
    if cfg["run"]["stage"] >= 2 and cfg["fixes"].get("split_aware_proper_nouns"):
        # A surface split across readings is judged on its PROPN reading only.
        pn = cfg["filters"]["proper_nouns"]
        by_reading = filters_mod.reading_cap_ratios(
            joint_splits, bg.cap_counts, bg.noninitial_counts,
            min_votes=pn.get("reading_min_propn_votes", 3),
            min_share=pn.get("reading_min_propn_share", 0.10))
        moved = {l: (cap_ratios[l], r) for l, r in by_reading.items()
                 if l in cap_ratios and abs(cap_ratios[l] - r) > 1e-9}
        cap_ratios.update({l: r for l, r in by_reading.items() if l in cap_ratios})
        stats["cap_ratio_by_reading"] = {l: [round(a, 3), round(b, 3)]
                                        for l, (a, b) in sorted(moved.items())}
        _log(f"  proper nouns: {len(moved)} lemmas re-measured on their PROPN reading")
    kept, flog = filters_mod.apply(
        lemma_counts, cap_ratios, cfg, lemmas_mod.in_dictionary, lemmas_mod.in_english
    )
    stats["foreign_dropped"] = len(flog.foreign)

    # Proper-noun audit: for every reviewed word, and every dictionary word
    # the filter drops at >= review_min_count, what the filter decides on its
    # own (keep-list ignored). Feeds scripts/make_proper_noun_review.py.
    if cfg["run"]["stage"] >= 2:
        import csv as _csv

        pn = cfg["filters"]["proper_nouns"]
        review_min = pn.get("review_min_count", 5000)
        reviewed: set[str] = set()
        kf = Path(pn.get("keep_file", ""))
        if kf.is_file():
            with kf.open(encoding="utf-8", newline="") as fh:
                reviewed = {r["lemma"] for r in _csv.DictReader(fh, delimiter="\t")}
        audit = []
        for lemma, count in lemma_counts.items():
            ratio = cap_ratios.get(lemma, 0.0)
            drops, _ = filters_mod.is_proper_noun(lemma, count, ratio, cfg,
                                                  lemmas_mod.in_dictionary)
            if lemma in reviewed or (drops and count >= review_min
                                     and lemmas_mod.in_dictionary(lemma)):
                audit.append((lemma, count, ratio, drops))
        audit.sort(key=lambda r: (-r[1], r[0]))
        with (rep_dir / "proper_noun_audit.tsv").open("w", encoding="utf-8", newline="\n") as fh:
            fh.write("lemma\tcount\tcap_ratio\tfilter_drops\n")
            for lemma, count, ratio, drops in audit:
                fh.write(f"{lemma}\t{count}\t{ratio:.3f}\t{'yes' if drops else 'no'}\n")
    stats["short_dropped"] = len(flog.short)
    stats["bp_excluded"] = len(flog.bp_excluded)
    stats["proper_nouns_dropped"] = len(flog.proper_nouns)
    _log(f"  dropped {len(flog.proper_nouns):,} proper nouns, "
         f"{len(flog.bp_excluded)} BP lemmas")

    # -- step 5: rank and emit --------------------------------------------
    _log("step 5: rank and emit")
    tagger = PosTagger.load()
    limit = max(hi for _, hi in cfg["output"]["bands"])

    # Part of speech: from the tagger where there is evidence, split across
    # entries the way counts are split across lemmas; the rule heuristic
    # otherwise (and always in stage 1).
    fold_to = {src: dst for src, dst, *_ in fold_log}
    headword_of_lemma = lambda l: fold_to.get(follow(l), follow(l))
    headword_of_surface = lambda s: headword_of_lemma(lemma_map.get(s, s))
    weighted: dict = {}
    raw_votes: dict = {}
    if cfg["pos"]["source"] == "tagger" and tags is not None and cfg["run"]["stage"] >= 2:
        pos_stats: dict[str, int] = {}
        weighted, raw_votes = pos_mod.aggregate(
            uni.counts, tags, joint_splits, headword_of_surface, headword_of_lemma, cfg,
            closed=frozenset(tagger.closed), stats=pos_stats)
        stats["pos_votes_counted"] = pos_stats.get("counted", 0)
        stats["pos_votes_inconsistent"] = pos_stats.get("inconsistent", 0)
    rows: list[tuple[str, str, int, bool]] = []
    n_split = n_fallback = 0
    contractions = pos_mod.contraction_pos(cfg)
    if contractions:
        stats["contraction_pos"] = dict(Counter(contractions.values()))
    for lemma, count in kept.items():
        parts = pos_mod.assign(lemma, count, weighted, raw_votes, cfg, tagger.tag,
                               contractions)
        if lemma not in weighted and lemma not in contractions:
            n_fallback += 1
        if len(parts) > 1:
            n_split += 1
        rows += [(lemma, pos, c, False) for pos, c in parts]
    rows += [(m["mwe"], "mwe", int(m["raw_freq"]), True) for m in mwes]
    entries = emit_mod.rank_rows(rows, uni.n_tokens, limit)
    published = {e.lemma for e in entries if not e.is_mwe}
    stats["pos_source"] = cfg["pos"]["source"] if weighted else "heuristic"
    stats["pos_split_lemmas_all"] = n_split
    stats["pos_split_in_list"] = sum(
        1 for l in published if sum(1 for e in entries if e.lemma == l and not e.is_mwe) > 1)
    stats["pos_heuristic_in_list"] = sum(1 for l in published if l not in weighted)
    _log(f"  POS: {stats['pos_split_in_list']:,} published lemmas split by POS, "
         f"{stats['pos_heuristic_in_list']:,} on the heuristic (no tagged evidence)")
    written = emit_mod.write_all(entries, cfg, out_dir)
    written += emit_mod.write_dropped(flog, cfg, out_dir)
    stats["entries"] = len(entries)
    _log(f"  wrote {len(written)} files to {out_dir}/")

    # The ready-to-import Anki package, built from the band files just written.
    from scripts import build_apkg

    apkg = build_apkg.build(cfg, out_dir)
    stats["apkg"] = {"bytes": apkg["bytes"], "notes": apkg["notes"]}
    _log(f"  wrote {Path(apkg['path']).name}: {apkg['bytes']:,} bytes, "
         f"{sum(apkg['notes'].values()):,} notes in {len(apkg['notes'])} decks")

    # -- quality report ----------------------------------------------------
    _log("quality report")
    # Use the lemma map itself as the oracle, so the check asks "is this
    # inventory closed under the lemmatizer that built it?" rather than
    # under some other backend, which would report spurious duplicates.
    # Headwords kept apart on purpose are exempt.
    exempt = set(tagger.closed) | set(split_protected)
    if cfg["run"]["stage"] >= 2:
        exempt |= set(cfg["fixes"].get("plurale_tantum", ()))
        if cfg["conventions"].get("enabled"):
            exempt |= conventions_mod.protected_forms(cfg)
    # One row per lemma for the duplicate checks: a lemma split by POS is
    # one word, not a duplicate of itself.
    seen: set[str] = set()
    lemma_entries = []
    for e in entries:
        if e.is_mwe or e.lemma in seen:
            continue
        seen.add(e.lemma)
        lemma_entries.append(e)
    entry_lemmas = [e.lemma for e in lemma_entries]
    relemma = {w: (w if w in exempt else follow(lemma_map.get(w, w))) for w in entry_lemmas}
    suspects = quality_mod.find_suspects(
        lemma_entries, cfg, lambda w: relemma.get(w, w), closed_class=frozenset(exempt),
    )
    quality_mod.write_tsv(suspects, rep_dir / cfg["paths"]["reports"]["quality_tsv"])
    quality_text = quality_mod.render_report(suspects, cfg)
    if fold_log:
        quality_text += quality_mod.render_folds(fold_log, cfg)
    notes = Path(__file__).parent / "data" / "quality_notes.md"
    if cfg["run"]["stage"] >= 2 and notes.is_file():
        # Standing notes (experiments tried and rejected), kept in the report.
        quality_text += notes.read_text(encoding="utf-8")
    (rep_dir / cfg["paths"]["reports"]["quality"]).write_text(quality_text, encoding="utf-8")
    stats["suspects"] = len(suspects)
    _log(f"  {len(suspects):,} suspect duplicate entries")

    # -- gold-set evaluation ----------------------------------------------
    # Score the lemma map this build actually published -- backend, gate,
    # conventions and closure together -- not a backend in isolation. The
    # backend-by-backend comparison lives in backend_scores.md.
    _log("gold-set evaluation")
    try:
        gold_rows, gold_meta = eval_mod.load_gold(cfg)
        label = f"pipeline, stage {cfg['run']['stage']} ({cfg['lemmatizer']['backend']})"
        # What a surface is published under: its lemma, after closure and
        # after any accent-variant fold of that lemma's count.
        fold_to = {src: dst for src, dst, *_ in fold_log}
        published = {s: fold_to.get(follow(l), follow(l)) for s, l in lemma_map.items()}
        save_published_map(cfg, published)
        result = eval_mod.score(gold_rows, published)
        gold_text = eval_mod.render({label: result}, gold_meta)
        stats["gold"] = {label: result["accuracy"]}
    except FileNotFoundError as exc:
        gold_text = f"_Gold set unavailable: {exc}_"
        stats["gold"] = None

    # -- comparison report -------------------------------------------------
    _log("comparison report")
    band_reports = []
    original_dir = Path(cfg["paths"]["original_dir"])
    for (lo, hi), spec in zip(cfg["output"]["bands"], cfg["output"]["files"]):
        orig = compare_mod.read_band(original_dir / f"{spec['stem']}.tsv")
        rebuilt = compare_mod.read_band(out_dir / f"{spec['stem']}.tsv")
        if orig and rebuilt:
            band_reports.append(
                (f"ranks {lo}-{hi}", compare_mod.compare_bands(orig, rebuilt, hi))
            )
    baseline_reports = []
    baseline_dir = Path(cfg["paths"].get("baseline_dir", ""))
    if cfg["run"]["stage"] >= 2 and baseline_dir.is_dir() and baseline_dir != out_dir:
        for (lo, hi), spec in zip(cfg["output"]["bands"], cfg["output"]["files"]):
            base = compare_mod.read_band(baseline_dir / f"{spec['stem']}.tsv")
            rebuilt = compare_mod.read_band(out_dir / f"{spec['stem']}.tsv")
            if base and rebuilt:
                baseline_reports.append(
                    (f"ranks {lo}-{hi}", compare_mod.compare_bands(base, rebuilt, hi))
                )

    conventions_text = ""
    if conv_log is not None:
        conventions_text = compare_mod.render_conventions(conv_log, uni.counts, entries)

    report = compare_mod.render(
        cfg, fingerprint_rows, band_reports, quality_text, gold_text, stats,
        baseline_reports=baseline_reports, conventions_text=conventions_text,
    )
    (rep_dir / cfg["paths"]["reports"]["comparison"]).write_text(report, encoding="utf-8")

    stats["elapsed_s"] = round(time.monotonic() - started, 1)
    (rep_dir / cfg["paths"]["reports"]["stats"]).write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # The gate runs last so that the reports are always written first: a
    # failing build must still leave the evidence behind.
    quality_mod.enforce(suspects, cfg)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--sample", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--stage", type=int, default=None, choices=(1, 2))
    ap.add_argument("--set", action="append", default=[], metavar="PATH=VALUE")
    ap.add_argument("--all-fixes", action="store_true",
                    help="stage 2 with every fixes.* flag on")
    args = ap.parse_args()

    def coerce(text: str) -> Any:
        low = text.lower()
        if low in ("true", "false"):
            return low == "true"
        if low in ("null", "none"):
            return None
        try:
            return int(text)
        except ValueError:
            return text

    cfg = config_mod.load(args.config)
    overrides: dict[str, Any] = {}
    if args.sample is not None:
        overrides["run.sample_lines"] = args.sample
    if args.workers is not None:
        overrides["run.workers"] = args.workers
    if args.stage is not None:
        overrides["run.stage"] = args.stage
        if args.stage == 1:
            overrides.update(stage1_overrides(cfg))
    if args.all_fixes:
        overrides["run.stage"] = 2
        overrides["quality.fail_on_suspects"] = True
        for flag in FIX_FLAGS:
            overrides[f"fixes.{flag}"] = True
    for item in args.set:
        path, _, raw = item.partition("=")
        overrides[path] = coerce(raw)
    if overrides:
        cfg = config_mod.with_overrides(cfg, overrides)

    try:
        stats = run(cfg)
    except quality_mod.QualityGateFailure as exc:
        print(f"\nQUALITY GATE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
