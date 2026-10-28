"""Step 5: rank, normalize, and write every output file.

README: "Top 5000 entries by raw lemma count, output as TSV and CSV" (the
published set actually runs to 10,000 across two bands).

Columns, exactly as the original: rank, lemma, is_mwe, pos, raw_freq,
freq_per_million.  The per-million figure is round(raw / total_tokens * 1e6,
3), which reproduces all 10,000 original rows exactly.

MWEs are an overlay: a multi-word entry's raw_freq is its bigram count and
is NOT subtracted from its constituents' lemma counts, per the original and
the usual frequency-list convention.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Entry:
    rank: int
    lemma: str
    is_mwe: bool
    pos: str
    raw_freq: int
    freq_per_million: float

    def row(self) -> list[str]:
        return [
            str(self.rank),
            self.lemma,
            "1" if self.is_mwe else "0",
            self.pos,
            str(self.raw_freq),
            f"{self.freq_per_million:.3f}",
        ]


HEADER = ["rank", "lemma", "is_mwe", "pos", "raw_freq", "freq_per_million"]


def band_label(rank: int, size: int) -> str:
    """Anki band label for a rank: rank 1 size 500 -> '0001-0500'."""
    lo = ((rank - 1) // size) * size + 1
    return f"{lo:04d}-{lo + size - 1:04d}"


# Published rows found to have no gloss while writing the enrichable files.
# Appended to rather than raised on, so one missing row cannot stop the build
# before it has written its reports; scripts/build.py fails on it at the end.
MISSING_GLOSSES: list[tuple[str, str]] = []


def build_tags(rank: int, pos: str, cfg: dict[str, Any],
               flags: Sequence[str] = (), reviewed: bool = False) -> str:
    """Tag string for one Anki note, in the original's field order.

    The frequency, POS and source tags are the original's and keep their
    order. 1.1 appends one `flag::` tag per gloss flag, so a learner can find
    or suspend the vulgar or the uncertain ones, and `gloss::reviewed` where a
    native speaker has passed a verdict on the entry.
    """
    tcfg = cfg["output"]["anki"]["tags"]
    b500 = band_label(rank, tcfg["band500"])
    b1000 = band_label(rank, tcfg["band1000"])
    return " ".join(
        [f"freq::{b500}", f"freq500::{b500}", f"freq1000::{b1000}", f"pos::{pos}"]
        + list(tcfg["static"])
        + [f"flag::{f}" for f in flags]
        + (["gloss::reviewed"] if reviewed else [])
    )


def rank_entries(
    lemma_counts: Mapping[str, int],
    mwes: Sequence[Mapping[str, Any]],
    total_tokens: int,
    tagger,
    limit: int,
) -> list[Entry]:
    """Merge single lemmas and MWEs into one ranked list.

    Ordering is count desc then lemma ascending, so ties are broken
    deterministically rather than by dict insertion order.
    """
    combined: list[tuple[str, int, bool]] = [
        (lemma, count, False) for lemma, count in lemma_counts.items()
    ]
    combined += [(m["mwe"], int(m["raw_freq"]), True) for m in mwes]
    combined.sort(key=lambda t: (-t[1], t[0]))

    out: list[Entry] = []
    for i, (lemma, count, is_mwe) in enumerate(combined[:limit], start=1):
        out.append(
            Entry(
                rank=i,
                lemma=lemma,
                is_mwe=is_mwe,
                pos=tagger.tag(lemma, is_mwe=is_mwe),
                raw_freq=count,
                freq_per_million=round(count / total_tokens * 1e6, 3),
            )
        )
    return out


def rank_rows(
    rows: Sequence[tuple[str, str, int, bool]], total_tokens: int, limit: int
) -> list[Entry]:
    """Rank (lemma, pos, count, is_mwe) rows. A lemma split by POS has one
    row per POS; ties break by lemma then POS, so order is deterministic."""
    ordered = sorted(rows, key=lambda r: (-r[2], r[0], r[1]))
    return [
        Entry(rank=i, lemma=lemma, is_mwe=is_mwe, pos=pos, raw_freq=count,
              freq_per_million=round(count / total_tokens * 1e6, 3))
        for i, (lemma, pos, count, is_mwe) in enumerate(ordered[:limit], start=1)
    ]


def _write_delimited(path: Path, rows: Iterable[Sequence[str]], delimiter: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter=delimiter, lineterminator="\n")
        for row in rows:
            writer.writerow(row)


def write_band(entries: Sequence[Entry], spec: Mapping[str, Any], out_dir: Path, cfg) -> None:
    rows = [HEADER] + [e.row() for e in entries]
    _write_delimited(out_dir / f"{spec['stem']}.tsv", rows, "\t")
    _write_delimited(out_dir / f"{spec['stem']}.csv", rows, ",")
    write_anki(entries, spec, out_dir, cfg, enrichable=False)
    write_anki(entries, spec, out_dir, cfg, enrichable=True)


def write_anki(
    entries: Sequence[Entry],
    spec: Mapping[str, Any],
    out_dir: Path,
    cfg: dict[str, Any],
    enrichable: bool,
) -> None:
    """Write an Anki import file.

    The header directives are reproduced exactly as in the original files so
    that an existing import, note type and deck keep working: separator,
    html, notetype, deck, columns, tags column.
    """
    acfg = cfg["output"]["anki"]
    columns = acfg["enrichable_columns"] if enrichable else acfg["minimal_columns"]
    kind = "enrichable" if enrichable else "minimal"
    path = out_dir / f"{spec['anki_stem']}_anki_{kind}.tsv"
    # The enrichable file now carries the published glosses; the minimal one
    # stays bare, so it needs none of this.
    glosses: dict[tuple[str, str], dict] = {}
    reviewed: set[tuple[str, str]] = set()
    labels: dict[str, str] = {}
    if enrichable:
        from scripts.build_apkg import published_glosses, reviewed_entries

        glosses = published_glosses(cfg, out_dir)
        reviewed = reviewed_entries(cfg)
        labels = cfg["gloss"].get("source_labels", {})

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(f"#separator:{acfg['separator']}\n")
        fh.write(f"#html:{str(acfg['html']).lower()}\n")
        fh.write(f"#notetype:{acfg['notetype']}\n")
        fh.write(f"#deck:{spec['deck']}\n")
        fh.write("#columns:" + "\t".join(columns) + "\n")
        fh.write(f"#tags column:{len(columns)}\n")
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        for e in entries:
            if enrichable:
                g = glosses.get((e.lemma, e.pos))
                if g is None:
                    # Collected, not raised: exiting here would leave the
                    # later lists, the deck and every report unwritten, and a
                    # failing build must still leave its evidence behind. The
                    # build reports these at the end, as the quality gate does.
                    MISSING_GLOSSES.append((e.lemma, e.pos))
                    g = {"gloss": "", "example_pt": "", "example_en": "",
                         "flags": "", "source": ""}
                flags = g["flags"].split() if g["flags"] else []
                writer.writerow(
                    [e.rank, e.lemma, e.pos,
                     g["gloss"], g["example_pt"], g["example_en"],
                     "1" if e.is_mwe else "0", e.raw_freq,
                     f"{e.freq_per_million:.3f}",
                     labels.get(g["source"], g["source"]),
                     build_tags(e.rank, e.pos, cfg, flags=flags,
                                reviewed=(e.lemma, e.pos) in reviewed)]
                )
            else:
                writer.writerow(
                    [e.rank, e.lemma, e.pos, "1" if e.is_mwe else "0",
                     e.raw_freq, f"{e.freq_per_million:.3f}",
                     build_tags(e.rank, e.pos, cfg)]
                )


def write_all(entries: Sequence[Entry], cfg: dict[str, Any], out_dir: Path) -> list[Path]:
    """Write every band plus the QC sample.  Returns the paths written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    by_rank = {e.rank: e for e in entries}

    for (lo, hi), spec in zip(cfg["output"]["bands"], cfg["output"]["files"]):
        band = [by_rank[r] for r in range(lo, hi + 1) if r in by_rank]
        write_band(band, spec, out_dir, cfg)
        written += [
            out_dir / f"{spec['stem']}.tsv",
            out_dir / f"{spec['stem']}.csv",
            out_dir / f"{spec['anki_stem']}_anki_minimal.tsv",
            out_dir / f"{spec['anki_stem']}_anki_enrichable.tsv",
        ]

    # QC sample: a fixed stride through the first band, as in the original.
    first_lo, first_hi = cfg["output"]["bands"][0]
    stride = max((first_hi - first_lo + 1) // 60, 1)
    sample = [by_rank[r] for r in range(first_lo, first_hi + 1, stride) if r in by_rank]
    qc = out_dir / cfg["output"]["qc_sample"]
    _write_delimited(qc, [HEADER] + [e.row() for e in sample], ",")
    written.append(qc)
    return written


def write_checksums(cfg: dict[str, Any], out_dir: Path) -> Path:
    """SHA-256 of every release asset, in `sha256sum -c` format.

    The assets are what a release attaches, and another project pins them by
    digest, so the sums are built rather than pasted into the release notes.
    `glosses.tsv` is an input to this build rather than an output of it, so it
    is hashed as it stands on disk; every other asset has just been written.
    """
    import hashlib

    ocfg = cfg["output"]
    lines = []
    for name in ocfg["release_assets"]:
        path = out_dir / name
        if not path.is_file():
            raise FileNotFoundError(
                f"release asset {path} is missing -- cannot write checksums"
            )
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        # Two spaces and a bare filename: the format `sha256sum -c` reads,
        # and the assets arrive beside it in the same download directory.
        lines.append(f"{h.hexdigest()}  {name}")
    path = out_dir / ocfg["checksums"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def _write_dropped_file(
    path: Path, rows, bp_excluded, min_count: int, total: int, foreign=(), short=()
) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Lemmas filtered out by the proper-noun/OOV heuristic.\n")
        fh.write("# Sorted desc by raw count -- review to rescue any false positives.\n")
        if min_count > 1:
            fh.write(
                f"# Truncated to entries with >= {min_count} occurrences: "
                f"{len(rows):,} of {total:,}. The full list is written next to\n"
                f"# this file as *_full.txt and is not committed.\n"
            )
        fh.write("# count\tlemma\tcap_ratio\treason\n")
        for lemma, count, ratio, reason in rows:
            fh.write(f"{count}\t{lemma}\t{ratio:.3f}\t{reason}\n")
        if bp_excluded:
            fh.write("#\n# BP-leaning lemmas excluded by the exclusion list:\n")
            for lemma, reason in bp_excluded:
                fh.write(f"#\t{lemma}\t{reason}\n")
        if foreign:
            fh.write("#\n# Foreign-word filter (English plurals):\n")
            for lemma, count, reason in foreign:
                fh.write(f"#\t{count}\t{lemma}\t{reason}\n")
        if short:
            fh.write("#\n# Short-token rule (1-2 letters, not a PT word or listed interjection):\n")
            for lemma, count, reason in short:
                fh.write(f"#\t{count}\t{lemma}\t{reason}\n")


def write_dropped(log, cfg: dict[str, Any], out_dir: Path) -> list[Path]:
    """Write the drop log twice.

    The full list runs to ~260k entries and 10 MB, nearly all of it hapax
    noise, so only the reviewable head is committed; the complete list is
    written alongside it and gitignored.
    """
    ocfg = cfg["output"]
    min_count = ocfg.get("dropped_min_count", 100)
    total = len(log.proper_nouns)

    full_path = out_dir / ocfg["dropped_proper_nouns_full"]
    _write_dropped_file(full_path, log.proper_nouns, log.bp_excluded, 1, total,
                        getattr(log, "foreign", ()), getattr(log, "short", ()))

    head = [r for r in log.proper_nouns if r[1] >= min_count]
    path = out_dir / ocfg["dropped_proper_nouns"]
    _write_dropped_file(path, head, log.bp_excluded, min_count, total,
                        [f for f in getattr(log, "foreign", ()) if f[1] >= min_count],
                        [f for f in getattr(log, "short", ()) if f[1] >= min_count])
    return [path, full_path]
