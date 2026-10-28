"""Release assets and the SHA256SUMS.txt that pins them.

Another project pins these files by digest, so the sums file is part of the
release rather than a convenience: these tests check the shipped one against
the shipped assets, not just the code that writes it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import config as config_mod, emit as emit_mod

ROOT = Path(__file__).resolve().parents[1]


def test_asset_list_is_the_published_four(release_cfg):
    """Pinned: the deck, both list bands and the glosses."""
    assert release_cfg["output"]["release_assets"] == [
        "EP_Spoken_Frequency.apkg",
        "ep_spoken_top5000.tsv",
        "ep_spoken_5001_10000.tsv",
        "glosses.tsv",
    ]
    assert release_cfg["output"]["checksums"] == "SHA256SUMS.txt"


def test_shipped_sums_match_the_shipped_assets(release_cfg):
    """The committed SHA256SUMS.txt describes the committed out/ files."""
    out = ROOT / "out"
    lines = (out / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(release_cfg["output"]["release_assets"])
    for line in lines:
        want, name = line.split("  ", 1)
        got = hashlib.sha256((out / name).read_bytes()).hexdigest()
        assert got == want, f"{name} does not match its recorded digest"


def test_every_asset_is_listed_once_and_in_order(release_cfg):
    out = ROOT / "out"
    names = [l.split("  ", 1)[1]
             for l in (out / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()]
    assert names == release_cfg["output"]["release_assets"]


def test_format_is_what_sha256sum_c_reads(release_cfg, tmp_path):
    """Two spaces, a bare filename, one line each, trailing newline."""
    for name in release_cfg["output"]["release_assets"]:
        (tmp_path / name).write_bytes(b"x")
    text = emit_mod.write_checksums(release_cfg, tmp_path).read_text(encoding="utf-8")
    assert text.endswith("\n")
    empty = hashlib.sha256(b"x").hexdigest()
    for line in text.splitlines():
        digest, sep, name = line.partition("  ")
        assert sep == "  " and "/" not in name
        assert digest == empty and len(digest) == 64


def test_a_missing_asset_is_an_error_not_a_short_file(release_cfg, tmp_path):
    """Writing sums for assets that are not there would publish a file that
    silently pins less than the release ships."""
    (tmp_path / "glosses.tsv").write_bytes(b"x")
    with pytest.raises(FileNotFoundError):
        emit_mod.write_checksums(release_cfg, tmp_path)
