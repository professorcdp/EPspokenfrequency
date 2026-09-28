"""Configuration loading and validation.

Every tunable lives in config.yaml.  This module turns it into a plain
nested dict with light validation, plus a few derived conveniences.  It
deliberately does not invent defaults for anything the YAML omits: a
missing key is an error, so a build can never silently run with different
thresholds than the config file records.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when config.yaml is missing a key or holds an invalid value."""


_REQUIRED_SECTIONS = (
    "corpus",
    "run",
    "paths",
    "tokenizer",
    "lemmatizer",
    "bigrams",
    "filters",
    "fixes",
    "quality",
    "output",
    "conventions",
    "pos",
    "serir",
)

_FIX_FLAGS = (
    "diacritic_folding",
    "accent_variant_folding",
    "bp_after_folding",
    "extended_proper_nouns",
    "mwe_constituent_check",
    "lemma_closure",
    "plural_folding",
    "split_enclitics",
    "english_plurals_foreign",
    "split_ambiguous",
    "short_token_rule",
    "cap_sentence_starts",
    "proper_noun_review",
    "contraction_pos",
    "repair_glued_enclitics",
    "split_aware_proper_nouns",
)


def load(path: str | Path) -> dict[str, Any]:
    """Load config.yaml, validate it, and return it as a nested dict."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ConfigError(f"{path} did not parse to a mapping")
    _stamp_glue_table(cfg)
    validate(cfg)
    return cfg


def _stamp_glue_table(cfg: dict[str, Any]) -> None:
    """Record the enclitic table's digest inside the tokenizer settings.

    Every pass is cached under a hash of `cfg["tokenizer"]`, so a change to
    the table has to show up there or a rebuild would silently reuse
    tokenization from before it. The same reasoning put the lemmatizer's vote
    filter in the config rather than in code.
    """
    import hashlib

    glue = cfg.get("tokenizer", {}).get("glue_repair")
    if not glue or not glue.get("table"):
        return
    path = Path(glue["table"])
    glue["digest"] = (hashlib.sha256(path.read_bytes()).hexdigest()[:16]
                      if path.is_file() else "absent")


def validate(cfg: dict[str, Any]) -> None:
    """Check structural invariants.  Raises ConfigError on the first fault."""
    missing = [s for s in _REQUIRED_SECTIONS if s not in cfg]
    if missing:
        raise ConfigError(f"config missing required section(s): {', '.join(missing)}")

    stage = cfg["run"].get("stage")
    if stage not in (1, 2):
        raise ConfigError(f"run.stage must be 1 or 2, got {stage!r}")

    for flag in _FIX_FLAGS:
        if flag not in cfg["fixes"]:
            raise ConfigError(f"fixes.{flag} must be set explicitly (true/false)")
        if not isinstance(cfg["fixes"][flag], bool):
            raise ConfigError(f"fixes.{flag} must be a boolean")

    # Stage 1 reproduces the original's known flaws, so its suspect list is
    # expected to be non-empty and the gate only warns.  Stage 2 must fail.
    if stage == 1 and cfg["fixes"]["diacritic_folding"]:
        raise ConfigError(
            "stage 1 is a faithful baseline; fixes.diacritic_folding must be false. "
            "Set run.stage: 2 to enable fixes."
        )
    if stage == 2 and not cfg["quality"].get("fail_on_suspects"):
        raise ConfigError(
            "stage 2 must enforce the quality gate; set quality.fail_on_suspects: true"
        )

    workers = cfg["run"].get("workers")
    if not isinstance(workers, int) or workers < 1:
        raise ConfigError(f"run.workers must be a positive int, got {workers!r}")

    chunk = cfg["run"].get("chunk_lines")
    if not isinstance(chunk, int) or chunk < 1:
        raise ConfigError(f"run.chunk_lines must be a positive int, got {chunk!r}")

    sample = cfg["run"].get("sample_lines", None)
    if sample is not None and (not isinstance(sample, int) or sample < 1):
        raise ConfigError(f"run.sample_lines must be null or a positive int, got {sample!r}")

    bands = cfg["output"].get("bands")
    files = cfg["output"].get("files")
    if not bands or not files or len(bands) != len(files):
        raise ConfigError("output.bands and output.files must be non-empty and equal length")
    for (lo, hi) in bands:
        if lo < 1 or hi < lo:
            raise ConfigError(f"invalid band [{lo}, {hi}]")

    if cfg["bigrams"]["min_collocation_share"] <= 0:
        raise ConfigError("bigrams.min_collocation_share must be > 0")


def is_sample_run(cfg: dict[str, Any]) -> bool:
    return cfg["run"].get("sample_lines") is not None


def _root(cfg: dict[str, Any]) -> Path | None:
    """Scratch root for non-release builds, or None for the release build."""
    build = Path(cfg["paths"]["build_dir"])
    if is_sample_run(cfg):
        return build / f"sample{cfg['run']['sample_lines']}_stage{cfg['run']['stage']}"
    if cfg["run"]["stage"] < 2:
        return build / "stage1"
    return None


def out_dir(cfg: dict[str, Any]) -> Path:
    """Where the lists go. Only the full stage 2 build writes to out/; the
    stage 1 baseline and --sample runs go under build/, so neither can ever
    overwrite the published lists."""
    root = _root(cfg)
    return root if root is not None else Path(cfg["paths"]["out_dir"])


def reports_dir(cfg: dict[str, Any]) -> Path:
    root = _root(cfg)
    return root / "reports" if root is not None else Path(cfg["paths"]["reports_dir"])


def with_overrides(cfg: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of cfg with dotted-path overrides applied.

    Used by the CLI's --set a.b.c=value and by the fix-ablation runs.
    """
    out = copy.deepcopy(cfg)
    for dotted, value in overrides.items():
        node = out
        parts = dotted.split(".")
        for key in parts[:-1]:
            if key not in node or not isinstance(node[key], dict):
                raise ConfigError(f"--set path does not exist: {dotted}")
            node = node[key]
        if parts[-1] not in node:
            raise ConfigError(f"--set path does not exist: {dotted}")
        node[parts[-1]] = value
    validate(out)
    return out
