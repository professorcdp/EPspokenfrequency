"""The glossing run: what is sent, what is accepted back, what it is keyed on.

None of this calls the API. The three things worth pinning are that the
model is never allowed to invent Portuguese, that a change to the prompt or
to the model invalidates the cached responses, and that the dry-run sample
is the one config.yaml describes.
"""

from __future__ import annotations

import json

import pytest

from scripts import gloss


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    """A handful of rows in the shape load_rows() produces."""
    def row(rank, lemma, pos, mwe=False, split=False, share=1.0):
        return {"rank": rank, "lemma": lemma, "pos": pos, "is_mwe": mwe,
                "raw_freq": 10 ** 6 // rank, "freq_per_million": f"{1000 / rank:.3f}",
                "split": split, "pos_share": share}
    return [row(1, "ser", "verb"), row(2, "meia", "noun", split=True, share=0.6),
            row(3, "bom dia", "mwe", mwe=True), row(4, "casa", "noun")]


# -- the prompt --------------------------------------------------------------


def test_prompt_header_is_not_sent(release_cfg):
    """scripts/gloss_prompt.md explains itself above the rule; only what is
    below the rule is the prompt."""
    text = gloss.system_prompt(release_cfg)
    assert "version\ncontrolled" not in text and "strips this header" not in text
    assert text.startswith("You are compiling English glosses")
    assert "copied exactly" in text


def test_prompt_forbids_inventing_portuguese(release_cfg):
    text = gloss.system_prompt(release_cfg)
    assert "Do not write a sentence of your own" in text
    assert "empty string" in text          # the escape hatch when nothing fits


# -- the request -------------------------------------------------------------


def test_request_pins_model_and_limits(release_cfg, rows):
    p = gloss.request_params(release_cfg, "PROMPT", rows[0], ["Vou ser breve."])
    assert p["model"] == release_cfg["gloss"]["model"] == "claude-opus-5"
    assert p["max_tokens"] == release_cfg["gloss"]["max_tokens"]
    assert p["output_config"]["effort"] == release_cfg["gloss"]["effort"]
    assert p["output_config"]["format"]["schema"]["additionalProperties"] is False
    # No temperature: the parameter does not exist on this model family.
    assert "temperature" not in p


def test_split_rows_are_told_their_share(release_cfg, rows):
    block = gloss.user_block(rows[1], ["As meias estão no chão."])
    assert "60%" in block and "other reading" in block
    assert "share:" not in gloss.user_block(rows[3], ["Vamos para casa."])


def test_a_row_with_no_sentences_says_so(release_cfg, rows):
    block = gloss.user_block(rows[3], [])
    assert "none available" in block and "leave" in block


# -- the cache ---------------------------------------------------------------


def test_cache_key_follows_lemma_and_pos(release_cfg, rows):
    a = gloss.cache_file(release_cfg, rows[3])
    b = gloss.cache_file(release_cfg, dict(rows[3], pos="verb"))
    assert a != b
    assert a.name.startswith("casa__noun-") and a.parent.name == "gloss"


@pytest.mark.parametrize("change", [
    {"model": "claude-opus-4-8"}, {"effort": "high"}, {"thinking": "disabled"},
])
def test_changing_the_run_invalidates_the_cache(release_cfg, rows, change):
    """A cached response is only reused for the exact run that produced it."""
    from scripts import config as config_mod

    base = gloss.stamp_for(release_cfg, "pd", rows[0], ["Vou ser breve."])
    other = config_mod.with_overrides(
        release_cfg, {f"gloss.{k}": v for k, v in change.items()})
    assert gloss.stamp_for(other, "pd", rows[0], ["Vou ser breve."]) != base


def test_the_token_ceiling_is_not_part_of_the_cache_key(release_cfg, rows):
    """A ceiling is not a setting: a reply that finished is the reply a higher
    ceiling would have given, so raising it must not re-bill 10,000 rows. The
    truncated ones come back because an errored reply is re-asked instead."""
    from scripts import config as config_mod

    base = gloss.stamp_for(release_cfg, "pd", rows[0], ["Vou ser breve."])
    higher = config_mod.with_overrides(release_cfg, {"gloss.max_tokens": 8000})
    assert gloss.stamp_for(higher, "pd", rows[0], ["Vou ser breve."]) == base


def test_an_unusable_reply_is_asked_again(release_cfg, rows, tmp_path, monkeypatch):
    """Refused, truncated, unparseable or simply empty: not an answer."""
    from scripts import config as config_mod

    cfg = config_mod.with_overrides(
        release_cfg, {"gloss.cache_dir": str(tmp_path), "gloss.max_attempts": 2})
    stamp = "s1"
    good = {"gloss": "to be", "example_pt": "", "example_en": "", "flags": []}
    gloss.cache_write(cfg, rows[0], stamp, [], {"usage": {}}, good)
    assert gloss.cache_read(cfg, rows[0], stamp) is not None

    bad = dict(good, gloss="", error="truncated at max_tokens")
    gloss.cache_write(cfg, rows[1], stamp, [], {"usage": {}}, bad)
    assert gloss.cache_read(cfg, rows[1], stamp) is None       # ask again
    gloss.cache_write(cfg, rows[1], stamp, [], {"usage": {}}, bad)
    assert gloss.cache_read(cfg, rows[1], stamp) is not None   # out of attempts


def test_a_failed_retry_never_overwrites_an_answer(release_cfg, rows, tmp_path):
    from scripts import config as config_mod

    cfg = config_mod.with_overrides(release_cfg, {"gloss.cache_dir": str(tmp_path)})
    good = {"gloss": "to be", "example_pt": "", "example_en": "", "flags": []}
    gloss.cache_write(cfg, rows[0], "s1", [], {"usage": {}}, good)
    gloss.cache_write(cfg, rows[0], "s1", [], {"usage": {}},
                      {"gloss": "", "example_pt": "", "example_en": "",
                       "flags": [], "error": "refusal (cyber)"})
    kept = gloss.cache_read(cfg, rows[0], "s1")
    assert kept["parsed"]["gloss"] == "to be" and kept["attempts"] == 2


def test_changing_the_prompt_or_the_sentences_invalidates_the_cache(release_cfg, rows):
    base = gloss.stamp_for(release_cfg, "pd", rows[0], ["Vou ser breve."])
    assert gloss.stamp_for(release_cfg, "OTHER", rows[0], ["Vou ser breve."]) != base
    assert gloss.stamp_for(release_cfg, "pd", rows[0], ["Serei breve."]) != base


# -- what comes back ---------------------------------------------------------

SENT = ["Vou ser breve.", "Não quero ser mau."]


def _reply(**kw):
    out = {"gloss": "to be", "example_pt": SENT[0], "example_en": "I'll be brief.",
           "flags": []}
    out.update(kw)
    return out


def test_a_good_reply_passes():
    assert gloss.verify(_reply(), SENT) == ""


def test_an_invented_example_is_rejected():
    """The whole point: every example sentence is a real corpus line."""
    assert "not one of the sentences" in gloss.verify(
        _reply(example_pt="Eu sou português."), SENT)


def test_an_edited_example_is_rejected():
    """Even a corrected or re-punctuated line is not the line we sent."""
    assert gloss.verify(_reply(example_pt="Vou ser breve"), SENT)


def test_no_example_is_allowed():
    """Better an entry with no example than a wrong one."""
    assert gloss.verify(_reply(example_pt="", example_en=""), SENT) == ""


def test_an_untranslated_example_is_rejected():
    assert gloss.verify(_reply(example_en=""), SENT)


def test_an_empty_gloss_is_rejected():
    assert gloss.verify(_reply(gloss="  "), SENT)


def test_unknown_flags_are_rejected():
    assert "unknown flag" in gloss.verify(_reply(flags=["rude"]), SENT)
    assert gloss.verify(_reply(flags=["vulgar", "bp-leaning"]), SENT) == ""


class _Block:
    def __init__(self, text): self.type, self.text = "text", text


class _Response:
    def __init__(self, text, stop="end_turn"):
        self.content, self.stop_reason, self.stop_details = [_Block(text)], stop, None


def test_truncated_replies_are_flagged_not_guessed():
    parsed = gloss.parse_reply(_Response('{"gloss":"to b', stop="max_tokens"))
    assert parsed["error"] and parsed["flags"] == ["uncertain"]
    assert gloss.verify(parsed, SENT)


def test_a_refusal_becomes_a_review_row():
    parsed = gloss.parse_reply(_Response("", stop="refusal"))
    assert "refusal" in parsed["error"]


def test_missing_fields_are_filled_in_not_crashed_on():
    parsed = gloss.parse_reply(_Response(json.dumps({"gloss": "to be"})))
    assert parsed["example_pt"] == "" and parsed["flags"] == []


# -- the dry-run sample ------------------------------------------------------


def test_dryrun_sample_matches_the_config(release_cfg):
    """Deterministic, stratified, and containing the awkward cases."""
    d = release_cfg["gloss"]["dryrun"]
    rows = gloss.load_rows(release_cfg)
    sample = gloss.dryrun_sample(release_cfg, rows)
    assert len(sample) == sum(n for _, _, n in d["strata"])
    for lo, hi, n in d["strata"]:
        assert sum(lo <= r["rank"] <= hi for r in sample) == n
    assert [r["rank"] for r in sample] == sorted(r["rank"] for r in sample)
    assert sum(r["split"] for r in sample) >= d["require"]["multi_pos"]
    assert sum(r["is_mwe"] for r in sample) >= d["require"]["mwe"]
    feminine = gloss.kept_feminine_nouns(release_cfg)
    assert sum(r["pos"] == "noun" and r["lemma"] in feminine
               for r in sample) >= d["require"]["kept_feminine_nouns"]
    assert sample == gloss.dryrun_sample(release_cfg, rows)


# -- tidying for display -----------------------------------------------------


@pytest.mark.parametrize("raw, shown", [
    ("- Tarde demais para quê?", "Tarde demais para quê?"),
    ("— Não sei.", "Não sei."),
    ('"Nós somos os teus amantes alegres"', "Nós somos os teus amantes alegres"),
    ('- "Convidas-me para ir ao cinema?"', "Convidas-me para ir ao cinema?"),
    ("«Vem cá»", "Vem cá"),
    # left alone: a quote inside the line, an unmatched one, and a line whose
    # dashes are part of what was said
    ('Ele disse "olá" e saiu.', 'Ele disse "olá" e saiu.'),
    ('Convidas-me para ir ao cinema?"', 'Convidas-me para ir ao cinema?"'),
    ("- - que?", "- - que?"),
    ("Pomos o pão-de-loç na mesa.", "Pomos o pão-de-loç na mesa."),
])
def test_tidy(raw, shown):
    assert gloss.tidy(raw) == shown


def test_tidying_happens_after_the_verbatim_check(release_cfg, rows, tmp_path):
    """The check compares against the corpus line; the card shows it tidied.
    Tidying first would make an edited sentence pass as verbatim."""
    sent = "- Tarde demais para quê?"
    reply = {"gloss": "too late", "example_pt": gloss.tidy(sent),
             "example_en": "Too late for what?", "flags": []}
    assert gloss.verify(reply, [sent])          # the tidied form is NOT verbatim
    ok = dict(reply, example_pt=sent)
    assert gloss.verify(ok, [sent]) == ""
    out = tmp_path / "g.tsv"
    gloss.write_tsv(out, [{**rows[0], **ok, "sentences": [sent], "problem": ""}])
    assert "- Tarde" not in out.read_text(encoding="utf-8")
    assert "Tarde demais para quê?" in out.read_text(encoding="utf-8")


# -- the review sample -------------------------------------------------------


def test_review_sample_covers_the_top_and_spreads_over_the_rest(release_cfg):
    r = release_cfg["gloss"]["review"]
    results = [{"rank": i, "lemma": f"w{i}", "pos": "noun"} for i in range(1, 10001)]
    sample = gloss.review_sample(release_cfg, results)
    top = [x for x in sample if x["rank"] <= r["all_through_rank"]]
    assert len(top) == r["all_through_rank"]
    assert len(sample) == r["all_through_rank"] + r["sampled"]
    assert [x["rank"] for x in sample] == sorted(x["rank"] for x in sample)
    # every band of the tail contributes
    rest = [x["rank"] for x in sample if x["rank"] > r["all_through_rank"]]
    lo, hi = r["all_through_rank"] + 1, 10000
    width = (hi - lo + 1) / r["bands"]
    for i in range(r["bands"]):
        assert any(lo + i * width <= k < lo + (i + 1) * width for k in rest)
    assert sample == gloss.review_sample(release_cfg, results)


# -- the gates ---------------------------------------------------------------


def _result(rank=1, lemma="casa", pos="noun", mwe=False, gloss_="house",
            ex=None, en="Let's go home.", flags=(), sentences=None, problem=""):
    """A finished gloss row. The example defaults to one that contains the
    entry, so each test only states what it is actually testing."""
    if ex is None:
        ex = f"Vamos para {lemma}."
    if sentences is None:
        sentences = [ex] if ex else []
    return {"rank": rank, "lemma": lemma, "pos": pos, "is_mwe": mwe,
            "raw_freq": 1, "freq_per_million": "1.0", "split": False,
            "pos_share": 1.0, "gloss": gloss_, "example_pt": ex, "example_en": en,
            "flags": list(flags), "sentences": list(sentences), "problem": problem}


def _gates(results, cfg, rows=None):
    from scripts import gloss_gates

    def tokenize(text):
        return [t.strip(".,!?¿¡\"'").lower() for t in text.split()]

    def surfaces_of(row):
        return {row["lemma"], row["lemma"] + "s"}

    return gloss_gates.run(results, rows if rows is not None else results,
                           cfg, tokenize, surfaces_of)


def test_a_clean_run_passes_every_gate(release_cfg):
    res = _gates([_result()], release_cfg)
    assert res["failed"] == []
    assert res["with_example"] == 1 and res["unflagged"] == 1


def test_a_missing_row_fails_coverage(release_cfg):
    rows = [_result(), _result(rank=2, lemma="livro")]
    res = _gates([rows[0]], release_cfg, rows=rows)
    assert "coverage" in res["failed"] and res["gates"]["coverage"].n == 1


def test_an_example_that_does_not_contain_the_entry_fails(release_cfg):
    """The strongest check: the sentence came back from the right request, but
    it does not illustrate the entry."""
    res = _gates([_result(ex="A casa é grande.", lemma="livro",
                          sentences=["A casa é grande."])], release_cfg)
    assert "contains_entry" in res["failed"]


def test_a_multi_word_entry_needs_the_whole_phrase(release_cfg):
    ok = _result(lemma="bom dia", pos="mwe", mwe=True, ex="Bom dia, Maria.",
                 sentences=["Bom dia, Maria."])
    assert _gates([ok], release_cfg)["failed"] == []
    bad = _result(lemma="bom dia", pos="mwe", mwe=True, ex="Que bom.",
                  sentences=["Que bom."])
    assert "contains_entry" in _gates([bad], release_cfg)["failed"]


def test_too_many_entries_without_an_example_fails(release_cfg):
    """One unillustrated entry is an answer; a run full of them is a failure."""
    few = [_result(rank=i, lemma=f"w{i}") for i in range(1, 100)]
    few[0] = _result(rank=1, lemma="w1", ex="", en="", sentences=["Vamos para w1."])
    res = _gates(few, release_cfg)
    assert res["gates"]["no_example"].n == 1 and res["failed"] == []
    many = [_result(rank=i, lemma=f"w{i}", ex="", en="",
                    sentences=[f"Vamos para w{i}."]) for i in range(1, 100)]
    assert "no_example" in _gates(many, release_cfg)["failed"]


def test_shape_problems_are_counted_but_do_not_fail(release_cfg):
    long_sense = " ".join(["word"] * 7)
    res = _gates([_result(gloss_=f"a; b; c; d"),
                  _result(rank=2, lemma="livro", gloss_=long_sense)], release_cfg)
    assert res["gates"]["senses"].n == 1
    assert res["gates"]["verbose_sense"].n == 1
    assert res["failed"] == []


def test_the_report_names_the_model_and_counts_the_flags(release_cfg):
    from scripts import gloss_gates

    res = _gates([_result(flags=["vulgar"]),
                  _result(rank=2, lemma="livro", flags=["vulgar", "archaic"])],
                 release_cfg)
    text = gloss_gates.render(res, release_cfg, ["cost: $0.00"])
    assert release_cfg["gloss"]["model"] in text
    assert "snapshot" in text
    assert "| `vulgar` | 2 |" in text and "| `archaic` | 1 |" in text
    assert "cost: $0.00" in text


# -- repairing a reply before it is published --------------------------------

CORPUS = ["- Andei à tua procura.", "Bem e mal são conceitos relativos."]


def _repair(example, sentences=CORPUS, contains=lambda t: True, **kw):
    reply = {"gloss": "to walk", "example_pt": example, "example_en": "x",
             "flags": [], **kw}
    return gloss.repair(reply, sentences, contains)


def test_a_double_escaped_reply_is_decoded_not_dropped():
    """Claude sometimes writes \\uXXXX as six literal characters. The sentence
    is right; only its escaping is wrong."""
    fixed, what = _repair("Bem e mal s\\u00e3o conceitos relativos.")
    assert what == "escape"
    assert fixed["example_pt"] == CORPUS[1]
    assert gloss.verify(fixed, CORPUS) == ""


def test_an_example_the_model_tidied_itself_is_re_anchored():
    """Dropping the dialogue dash is what we do on output anyway, so the
    corpus line goes back in and nothing about the card changes."""
    fixed, what = _repair("Andei à tua procura.")
    assert what == "reanchored"
    assert fixed["example_pt"] == CORPUS[0]
    assert gloss.verify(fixed, CORPUS) == ""


def test_an_edited_example_is_dropped_and_flagged():
    """`tras` -> `trás`, a pronoun supplied, a clause trimmed: there is no
    telling a correction from a corruption, so the example goes."""
    fixed, what = _repair("Tu andaste à minha procura.")
    assert what == "rewritten"
    assert fixed["example_pt"] == "" and fixed["example_en"] == ""
    assert "uncertain" in fixed["flags"]
    assert fixed["gloss"] == "to walk"        # the gloss survives
    assert gloss.verify(fixed, CORPUS) == ""


def test_a_real_line_that_does_not_contain_the_entry_is_dropped():
    fixed, what = _repair(CORPUS[1], contains=lambda t: False)
    assert what == "off_target"
    assert fixed["example_pt"] == "" and "uncertain" in fixed["flags"]


def test_a_clean_reply_is_left_exactly_as_it_is():
    fixed, what = _repair(CORPUS[0])
    assert what == "" and fixed["example_pt"] == CORPUS[0]


# -- a reviewer overruling the model -----------------------------------------


def _overrides(tmp_path, release_cfg, body):
    from scripts import config as config_mod

    (tmp_path / "gloss_overrides.tsv").write_text(
        "# a comment, and a blank line follow\n\n"
        "lemma\tpos\tgloss\texample_pt\texample_en\tnote\n" + body,
        encoding="utf-8")
    return config_mod.with_overrides(release_cfg, {"paths.eval_dir": str(tmp_path)})


def test_the_shipped_overrides_file_covers_the_refused_word(release_cfg):
    """caseiro is refused by a safety classifier on every attempt, which is
    why max_missing_gloss is back to zero: this file is the answer."""
    over = gloss.load_overrides(release_cfg)
    assert ("caseiro", "adj") in over
    assert over[("caseiro", "adj")]["gloss"].startswith("homemade")
    assert over[("caseiro", "adj")]["note"]
    assert release_cfg["gloss"]["gates"]["max_missing_gloss"] == 0


def test_only_the_fields_a_reviewer_fills_in_are_taken():
    model = {"gloss": "wrong", "example_pt": "Uma casa velha.",
             "example_en": "An old house.", "flags": ["uncertain"]}
    # gloss only: the model's example survives
    out = gloss.apply_override(model, {"gloss": "house", "example_pt": "",
                                       "example_en": "", "note": ""})
    assert out["gloss"] == "house" and out["example_pt"] == "Uma casa velha."
    # example only: the model's gloss survives
    out = gloss.apply_override(model, {"gloss": "", "example_pt": "A casa é azul.",
                                       "example_en": "The house is blue.", "note": ""})
    assert out["gloss"] == "wrong" and out["example_pt"] == "A casa é azul."
    # and an override clears the model's own hedge
    assert "uncertain" not in out["flags"]


def test_an_override_clears_a_refusal():
    refused = {"gloss": "", "example_pt": "", "example_en": "", "flags": ["uncertain"],
               "error": "refusal (general_harms)"}
    out = gloss.apply_override(refused, {"gloss": "homemade", "example_pt": "",
                                         "example_en": "", "note": "by hand"})
    assert gloss.verify(out, []) == ""


def test_an_overridden_example_is_not_held_to_the_corpus_check():
    """A reviewer's sentence has a different provenance, not a broken one --
    but the row is marked, and the gate counts it."""
    reply = {"gloss": "house", "example_pt": "Uma frase escrita à mão.",
             "example_en": "A sentence written by hand.", "flags": []}
    assert gloss.verify(reply, ["A casa é azul."])
    assert gloss.verify(reply, ["A casa é azul."], overridden=True) == ""


def test_the_gates_exempt_an_override_but_still_count_it(release_cfg):
    row = {**_result(), "source": "override", "override_note": "by hand",
           "example_pt": "Uma frase escrita à mão."}
    res = _gates([row], release_cfg)
    assert res["failed"] == []                     # neither verbatim nor contains_entry
    assert res["gates"]["verbatim"].n == 0 and res["gates"]["contains_entry"].n == 0
    assert res["gates"]["override"].n == 1
    assert res["gates"]["override_off_corpus"].n == 1


def test_an_override_for_an_unpublished_row_is_an_error(release_cfg, tmp_path):
    """A typo in a lemma must not fail silently."""
    cfg = _overrides(tmp_path, release_cfg,
                     "casssa\tnoun\thouse\t\t\ttypo\n")
    rows = [{"lemma": "casa", "pos": "noun"}]
    with pytest.raises(SystemExit) as exc:
        gloss.load_overrides(cfg, rows)
    assert "casssa" in str(exc.value)


def test_the_same_row_cannot_be_overridden_twice(release_cfg, tmp_path):
    cfg = _overrides(tmp_path, release_cfg,
                     "casa\tnoun\thouse\t\t\tone\ncasa\tnoun\thome\t\t\ttwo\n")
    with pytest.raises(SystemExit) as exc:
        gloss.load_overrides(cfg)
    assert "twice" in str(exc.value)


def test_comments_and_blank_lines_are_ignored(release_cfg, tmp_path):
    cfg = _overrides(tmp_path, release_cfg, "\n# another comment\ncasa\tnoun\thouse\t\t\t\n")
    assert set(gloss.load_overrides(cfg)) == {("casa", "noun")}


# -- the review file is an input as well as an output -------------------------


def test_regenerating_the_review_file_keeps_a_reviewer_s_columns(release_cfg, tmp_path):
    """It wiped 257 native-speaker verdicts once. Every generated file in
    eval/ merges rather than overwrites, and this one is no exception."""
    path = tmp_path / "gloss_review.tsv"
    rows = [_result(rank=1, lemma="casa"), _result(rank=2, lemma="livro")]
    gloss.write_tsv(path, rows, show_sentences=True)

    # a reviewer adds columns and fills one in
    text = path.read_text(encoding="utf-8").splitlines()
    head, body = text[0], text[1:]
    path.write_text("\n".join(
        [head + "\ttutor_verdict\ttutor_note"]
        + [body[0] + "\tgood\tfine as it is", body[1] + "\t\t"]) + "\n",
        encoding="utf-8")

    gloss.write_tsv(path, rows, show_sentences=True)      # regenerate
    import csv

    back = list(csv.DictReader(path.open(encoding="utf-8", newline=""), delimiter="\t"))
    assert [r["lemma"] for r in back] == ["casa", "livro"]
    assert back[0]["tutor_verdict"] == "good"
    assert back[0]["tutor_note"] == "fine as it is"
    assert back[1]["tutor_verdict"] == ""


def test_a_reviewed_row_leaving_the_sample_is_reported(release_cfg, tmp_path, capsys):
    path = tmp_path / "gloss_review.tsv"
    gloss.write_tsv(path, [_result(rank=1, lemma="casa")], show_sentences=True)
    text = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([text[0] + "\ttutor_verdict", text[1] + "\tgood"]) + "\n",
                    encoding="utf-8")
    gloss.write_tsv(path, [_result(rank=1, lemma="livro")], show_sentences=True)
    assert "no longer in the sample" in capsys.readouterr().err


def test_the_gloss_file_has_no_reviewer_columns(release_cfg, tmp_path):
    """out/glosses.tsv is published output; only the review file merges."""
    path = tmp_path / "glosses.tsv"
    gloss.write_tsv(path, [_result()], show_sentences=False)
    header = path.read_text(encoding="utf-8").splitlines()[0].split("\t")
    assert header == list(gloss.GLOSS_COLUMNS)
    assert "source" in header and "tutor_verdict" not in header
