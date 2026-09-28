# Changelog

## Unreleased

Work towards 1.1.0. Not tagged or released; the version number is fixed
when the glosses have been reviewed.

### Added

- **English glosses and example sentences**, `out/glosses.tsv`: one to
  three English senses per entry, commonest first, plus one sentence taken
  verbatim from the corpus and its translation, and flags for `vulgar`,
  `bp-leaning`, `archaic`, `name-like` and `uncertain`. Written by Claude
  (`claude-opus-5`), one request per entry, from the entry, its part of
  speech, its frequency and up to twenty real corpus sentences containing
  it. The prompt ships with the repository
  (`scripts/gloss_prompt.md`) and the run is pinned in `config.yaml`.
  **These are a snapshot of one model's answers, not a reference work**, and
  are not reproducible byte for byte the way the lists are.
- **A repair step between the model's reply and the published row**
  (`gloss.repair`). Three things went wrong often enough in the first full
  run to be worth handling rather than failing over, and each is handled in
  a way that keeps the published example a real corpus line: a
  doubly-escaped `\uXXXX` is decoded (5 rows); an example the model tidied
  itself — dropped the dialogue dash — is re-anchored to the corpus line it
  tidied, which changes nothing about the card (6 rows); and an example the
  model *edited* (an accent added, a pronoun supplied, a clause trimmed) is
  dropped, because there is no telling a correction from a corruption, and
  the entry keeps its gloss alone (24 rows). Every one is counted and listed
  in the gate report.
- **Gates on the glosses**, `reports/gloss_gates.md`: coverage, and the
  check that matters — every example sentence must be one of the corpus
  lines the model was shown, character for character, and must contain the
  entry. A run failing any fatal gate is not published. Per-flag counts and
  the cost of the run are in the same report.
- **`eval/gloss_overrides.tsv`**, a reviewer's answer beating the model's,
  in the same shape as the other human-decision files in `eval/`: match on
  lemma + pos, and only the fields a row fills in are taken, so a row can
  replace the gloss, the example, or both. An overridden row is published
  with `source = override` in `out/glosses.tsv` and is exempt from the
  corpus-provenance gates — a reviewer's sentence has a different
  provenance, not a broken one — but the gate counts it, and counts
  separately any overridden example that is not one of the corpus lines the
  model was shown. An override naming an unpublished lemma is an error, so a
  typo cannot fail silently. Seeded with the one entry the model will not
  gloss (`caseiro`).
- **A review sample**, `eval/gloss_review.tsv`: all of ranks 1–500 plus 200
  spread evenly over the rest, with the sentences each entry was offered, so
  a reader can check what the model was working from.
- **A targeted corpus pass for entries the sampled contexts missed.** Nine
  published entries — eight multi-word expressions and one folded adjective
  — had no sampled sentence containing them, because pass 2 keeps lines for
  the 70,000 most frequent forms and, for a phrase, only lines that happen
  to contain the whole phrase. Those now get one scan of their own, choosing
  lines by the same digest rule, so every one of the 10,000 entries was
  glossed from real sentences rather than from its headword alone.

### Known issues

- **One gloss is not the model's.** `caseiro` (rank 4209, "homemade") trips
  a safety classifier on every attempt, so its gloss is written by hand in
  `eval/gloss_overrides.tsv` and the row is marked `source = override`.
  Every other gloss in the file is the model's. The `gloss_present` gate is
  back to zero tolerance now that overrides cover refusals.
- **200 entries have no example sentence** (2.0%). Either every sampled line
  showed a different word — `doméstica` the adjective rather than the noun —
  or the lines were unintelligible fragments. Those entries have a gloss and
  no example; the reverse Anki card still works, the sentence fields are
  just empty.
- **The glosses are not reproducible byte for byte.** The lists are; these
  are one model's answers on one day, and the response cache in `cache/gloss/`
  is what makes a rerun repeat them rather than re-derive them.

### Fixed

- **51 rows were not words at all: `conheçoa`, `deixaa`, `levaa` and 48 more.**
  `conheçoa` sat at rank 5,290 in 1.0.0, glossed "I know her". They were
  `conheço-a`, `deixa-a`, `leva-a` — properly hyphenated in the corpus — and
  the tokenizer glued them back together.

  `a` and `as` are both enclitic pronouns and future/conditional tense
  infixes, and `split_enclitic` reassembled a mesoclitic verb whenever the
  tail it had peeled ended in one. Mesoclisis always puts the clitic
  *between* stem and infix (`dar-lhe-ia` = *daria* + *lhe*), so a tail of one
  can never be an infix; that single condition was missing. Every affected
  row ended in `-a` or `-as`, which is what gave the cause away — genuine
  hyphen loss would not favour one clitic so heavily.

  The tokens went where they belong: *deixar* +28,981, *levar* +19,546,
  *matar* +11,196, *conhecer* +7,941.

- **Clusters the corpus writes without their hyphen are now repaired**
  (`fixes.repair_glued_enclitics`): `deixame`, `dáme`, `calate`, `sêlo` and
  26 more, 1,556 tokens. This is the smaller half of the problem and it
  cannot be done by rule — stripping a clitic-shaped tail and checking that
  the stem is a verb form also breaks `sera` (a missing accent on *será*),
  `saiste` (*saíste*), `rodeo`, `eramos` and `fodeste`. So
  `scripts/make_glue_table.py` generates `scripts/data/enclitic_clusters.tsv`
  from clusters the corpus writes **both** ways, and the tokenizer consults
  the table rather than guessing. A cluster has to be attested hyphenated at
  least 100 times, at least twice as often as glued, be neither a dictionary
  word nor a recognised verb form, and not be capitalized mid-line — that
  last test is the one that matters: `mateo` occurs 1,113 times away from the
  start of a line and is capitalized every single time. It is *Mateo*, not
  `mate-o`. `nola`, `pirate`, `rise` and `rite` are the same story. The
  table's digest is hashed into every cache key, so regenerating it
  invalidates the passes that depend on it.

  **Effect on the list:** 52 rows out, 52 in. 636,582,535 tokens (+368,083)
  over 827,895 types (−10,463). The gold-set score is unchanged at 98.5%, the
  quality gate still finds 0 suspects, and the `ser`/`ir` rule fingerprint is
  unchanged (`2defd01d6b1615a7`, 95.9%), so the rule still applies: *ser*
  21,334,148 and *ir* 9,023,260, both within 400 of before. One multi-word
  entry (`guarda costeira`) dropped out as bigram counts shifted and
  `efeitos colaterais` took its place; the other 51 replacements are new
  entries at the bottom of the list, ranks 9,904–10,000.

- **A native speaker's first-pass gloss review is applied**
  (`eval/gloss_review.tsv`, from the advisor's commit `6edc345`). 257 of the
  top 500 rows carry a verdict. Seven of them say "verdict given on the
  earlier gloss text", and by decision those do not count as reviewed, so the
  reviewed total is **250: 236 good, 13 fix, 1 wrong** — not the 257/243 the
  raw tally shows.

  Her example changes are accepted as overrides, in two kinds. Six are
  sentences she edited, and those are published with `source =
  override-edited`; seven are different corpus lines she chose from the ones
  the model was shown, published as `override-chosen`. An eighth chose the
  line already there, so there was nothing to apply. The English for all
  thirteen was written here to match her Portuguese — she supplied the
  Portuguese only — and every row says so in its `note`.

  `out/glosses.tsv` gains a `source` column and `config.yaml` a
  `gloss.source_labels` table, so the deck's `Gloss_Source` field can read
  "corpus line, edited by a native speaker" for those six. The field itself
  arrives with the glossed deck; the column is there now.

- **Regenerating the review file no longer destroys the review.**
  `write_tsv` overwrote `eval/gloss_review.tsv` with the columns it knows
  about, which wiped all 257 verdicts the first time the file was rebuilt
  after the advisor filled them in (recovered from git). It now merges,
  carrying over any column a reviewer has added, matched on lemma and POS,
  and warns when a reviewed row has left the sample. Every other generated
  file in `eval/` already worked this way.

- **`lorque` is dropped**: *Iorque* with its capital I read as a lowercase l,
  7,119 occurrences at rank 3,885, invisible to the proper-noun filter
  because it is never capitalized. It and `lolaus` (*Iolaus*, 731) are in
  `eval/proper_noun_drops_review.tsv`, which gains a `note` column. A scan
  for siblings — an l where a capital I belongs, never capitalized, whose
  I-form is a frequent dropped name — finds 121 in the corpus, but every one
  apart from these two occurs 74 times or fewer, far below the list. The two
  worth knowing about that the scan cannot see are `lgreja` (595) and
  `lnglês` (141), whose I-forms are ordinary words rather than dropped names.

- **The proper-noun filter measures capitalisation per reading**
  (`fixes.split_aware_proper_nouns`). The plain ratio mixes every reading of a
  surface together, so a name hiding inside a common word can never reach the
  threshold. Where the per-occurrence splitter has divided a surface, the
  name reading is now measured on its own.

  **This needs three guards, and without them it is worse than useless.** The
  PROPN reading must have at least 3 votes and 10% of the surface's votes, and
  the capitals must fit inside it. Without them a single stray PROPN tag
  collapses the denominator and the ratio saturates at 1.00: the first run
  dropped `fora`, `tratar`, `estado`, `soldado`, `dado`, `espada`, `privado`,
  `sagrado`, `gelado`, `temporada`, `embaixada`, `condado` and `deputado` as
  names. With the guards, 36 lemmas are re-measured and five cross the
  threshold: `antártida`, `prelado`, `prado`, `bushido` and `unidas` (as in
  *Nações Unidas*). Three entries leave the list — `lorque`, `unidas` (3,330)
  and `prado` (2,457) — three enter at the bottom, and **no count changes at
  all**.

  **The `são` and `nova` residues survive, and that is the right answer.**
  Measured on their PROPN reading alone `são` reads 0.21 and `nova` 0.76,
  against a threshold of 0.85 and the 1.00 that names like *john* and *maria*
  sit at. What is left of them after the tag split is mostly the common word
  the tagger mislabelled, not the place — so the remedy for `nova` is a better
  vote share, not the filter.

- **`largo` has a gloss override**: "wide, broad; (noun) square, plaza", since
  the noun sense lost its own row when `larga`'s adjectival occurrences pushed
  the noun share below the POS-split threshold.

- **`são` was published as a noun at rank 86, with 1,117,272 occurrences.**
  It is the third person plural of *ser* — "they are" — and Stanza says so in
  45 of its 50 sampled sentences. It was capitalized in only 2% of its
  mid-line occurrences, so it is hardly ever the *São* of São Paulo.

  The cause was a clause in the consistency rule. `pos.consistent` rejects a
  VERB or AUX tag whose lemma is a function word, which is right for the POS
  column — a preposition tagged VERB is noise — but *ser*, *ter*, *ir* and
  *este* are function words and inflected verbs at the same time. So all 45
  AUX votes were thrown away, and the 5 that read the word as a name decided
  the lemma. `é`, `somos` and `eram` escaped only because *every* one of their
  votes was dropped, which triggers the "if all are dropped, all count"
  fallback. `são` had five survivors, so it did not.

  Deciding which lemma an occurrence belongs to now uses
  `pos.consistent_shape`, the same rule without that clause, and `são` and
  `nova` join `fixes.ambiguous_forms` so their counts are divided by tag:

  | entry | before | after |
  |---|---:|---:|
  | *ser* (verb) | 21,334,148 | **22,339,499** |
  | `são` (noun) | 1,117,272 | 111,921 |
  | *novo* (adj) | 387,344 | **491,234** |
  | `nova` (noun) | 216,438 | 112,548 |

  *ser* was undercounted by 4.7%. Four counts changed and nothing else: no
  entry entered or left the list, the token total, the gold score (98.5%),
  the quality gate (0 suspects) and the ser/ir fingerprint are all unchanged.

  **The residues are still not clean entries.** `são` keeps 111,921
  occurrences at rank 558, glossed "Saint (before male names); they are" — a
  mixture of the name and what the tag sample did not catch. `nova` keeps
  112,548 at rank 553 and is glossed as the feminine adjective, which means
  those occurrences probably belong to *novo* as well: the vote was 26–24, and
  the proper-noun side is inflated by *Nova Iorque*, which already has an
  entry of its own at rank 1,050. Neither residue is filtered as a proper
  noun, because the capitalization ratio is measured over every occurrence of
  the surface, verb uses included.

- **`larga` and `largas` are divided between *largar* and *largo* by tag**
  (`fixes.ambiguous_forms`). The surface is both the verb (*larga isso!*) and
  the feminine adjective (*uma rua larga*), and the whole 55,702 occurrences
  were going to *largar* — which, once the enclitic fix pushed the count up,
  published a `largar` / `adj` row at rank 1,063. The per-occurrence splitter
  now divides the count the way it divides *fomos* between *ir* and *ser*:
  *largar* 111,474 and *largo* 23,636, conserving the total.

  This needed one more thing to be right. `resolve_joint` took Stanza's lemma
  at face value for a listed ambiguous form, and 21 of 50 sampled `larga`
  sentences come back with lemma *largo* tagged VERB — Stanza reading "eu
  largo" as a form of the adjective. Counting those would have moved most of
  a verb's occurrences onto *largo*, so the consistency rule that already
  filters the lemma votes now filters these too. It applies to the ambiguous
  branch only: the participle branch derives its lemma from the surface
  rather than from Stanza, and filtering it moved 63 entries and 324 counts.

  **Effect:** two entries out (`largar` adj, `largo` noun), two in at the
  bottom (`obediente`, `hebraico`), two counts changed, and nothing else.
  Token total, gold score (98.5%), quality gate (0 suspects) and the ser/ir
  fingerprint are all unchanged. One consequence worth knowing: `largo` used
  to be published twice, as a noun (*o largo*, a square — 4,986) and an
  adjective (2,276). With 16,374 adjectival occurrences added, the noun share
  falls to 21%, below the 25% POS-split threshold, so `largo` is now a single
  adjective row and the "square" sense no longer has one of its own.

### Changed

- **Every contraction now takes the part of speech of what it contracts**
  (`fixes.contraction_pos`, `pos.contraction_pos`). Stanza expands *do*,
  *nas*, *pelo* and the rest into two words before tagging, so the surface
  token collected almost no usable evidence: 28 contraction entries read
  `unk`, and those with a stray tag read worse — `pelo` as a noun, `deste` as
  a verb, `ao` as a conjunction, `contigo` split across three parts of
  speech. Each form now gets one decided answer, by what it is made of
  rather than by the paradigm it sits in:

  | group | POS | forms |
  |---|---|---|
  | preposition + article or demonstrative | `det` | 58: *do*, *nas*, *pelo*, *num*, *deste*, *naquela*, *noutro*, … |
  | preposition + pronoun | `pron` | 19: *dele*, *dela*, *deles*, *delas*, *nele*, *nela*, *neles*, *nelas*, *disto*, *disso*, *daquilo*, *nisto*, *nisso*, *naquilo*, *àquilo*, *comigo*, *contigo*, *connosco*, *convosco* |
  | preposition + adverb of place | `adv` | 3: *daqui*, *daí*, *dali* |

  `do` and `da` already read `det` on the tagger's own evidence; the rest of
  the determiner group now agrees with them. The pronoun and adverb groups
  are the ones the tagger would never have got right and a single blanket
  answer would have got wrong.

  **70 rows changed part of speech** and `unk` rows fell from 106 to 78.
  Because the three `contigo` rows and four other split entries merge into
  one, three entries move into the list from just below rank 10,000
  (`carnívoro`, `decretar`, `lótus`). Word lists, counts and ranks are
  otherwise unchanged; the gold-set score (98.5%) and the quality gate (0
  suspects) are unaffected.

  **This changes Anki note identity for those 70 notes.** A note's GUID
  comes from its word and part of speech, so re-importing over 1.0.0 adds a
  second note for each contraction whose POS changed and leaves the old one
  behind. Deleting the twenty decks before importing is the clean path for
  anyone who has not yet started reviewing.


## 1.0.0 — 2026-09-24

The first public release: 10,000 words of European Portuguese film and TV
dialogue, ranked, with a ready-to-import Anki package. Lemmas come from a
neural tagger checked against a dictionary and score 98.5% on a
hand-reviewed sample; the part of speech is the tagger's, and `ser` and
`ir` are separated by a rule measured against a native-speaker-labeled
sample.

**Overlap with the April list** is 79.0% of band 1 (ρ 0.944) and 63.3% of
band 2 (ρ 0.851). Against the v0.9 checkpoint the word lists barely change;
what changed there was the POS column and, through POS splitting, which
rows fill the last places of each band.

**Known issues.**

- **No glosses or example sentences.** The `Gloss_EN`, `Example_PT` and
  `Example_EN` fields ship empty, for you to fill in; until a note has a
  gloss it has no English → Portuguese card. Glosses are planned for 1.1.
- **Six accent pairs are accepted as known typos** and appear as two
  entries each: `camera`/`câmera`, `frigorifico`/`frigorífico`,
  `amen`/`ámen`, `bla`/`blá`, `mafia`/`máfia`, `karate`/`karaté`. They sit
  below the 10× folding ratio, and the quality gate accepts them by name.
- **The `ser`/`ir` rule is right on 95.9%** of the verb uses it decides on
  the development sample and **93.2%** (68 of 73) on the held-out sample,
  abstaining on 8–9%. Its errors all call an `ir` use `ser`, so `ir` is
  still slightly undercounted. One adverbial *fora* in twenty reaches the
  rule at all (*lá fora*, mistagged by Stanza), affecting about 1% of
  `fora` tokens; left for a later round rather than tuned away against the
  test set.
- **Re-importing a later `.apkg`** matches notes by word and part of
  speech, and Anki's "Update notes" option then replaces every field,
  glosses and examples a learner has typed in included; choosing "Never"
  keeps them but freezes ranks. Deferred to 1.1, when glosses ship.

- **A ready-to-import Anki package**, `out/EP_Spoken_Frequency.apkg`: one
  note type, twenty decks of 500 words numbered in rank order
  (`01 · 1–500` … `20 · 9501–10000`), a Portuguese → English card
  for every note, and an English → Portuguese card that appears only once
  a gloss is added. Notes are identified by word and part of speech, so a
  later release imported over this one updates notes instead of
  duplicating them. The TSV files remain for building your own note type.
- **Part of speech from Stanza.** The POS column -- renamed from
  `pos_guess` to `pos`, and the Anki field from `POS_guess` to `POS` -- is
  now the tagger's majority vote over each word's sample sentences,
  replacing the rule heuristic reconstructed from the April list.
  Prepositions are never counted as conjunctions (Universal Dependencies
  tags *para fazer* as one); the list is in config.yaml. A word the tagger uses
  as two parts of speech gets one row for each, with its count divided the
  same way participle counts are divided across lemmas: 311 words now have
  more than one row (`a` as article and preposition, `que`, `este`,
  `morto`), so the 10,000 rows hold 9,390 distinct words. 148 entries
  without usable tags, mostly contractions, keep the heuristic.
- **Larger samples for frequent words.** Word forms with 10,000+
  occurrences are now read in 50 sentences instead of 5, so their splits
  move in 2% steps instead of 20%.
- **One tagging pass.** Lemmas, participle splits and POS now come from a
  single Stanza pass over about 500,000 sentences, and a lemma vote is
  discarded when Stanza's lemma and tag contradict each other (`saia`
  given the lemma *saia* but tagged VERB). Gold-set accuracy is unchanged
  at 98.5%. `vá` added to the override table (Stanza read it as *ver*).
- **`ser` and `ir` are now split by a rule.** v0.9 said the tagger split
  them by context; it does not. The larger sample shows it assigns `foi`,
  `fui`, `fomos` and `foram` to *ser* almost regardless of context, all 50
  sampled uses of `fui` and `fomos` included (*fui ao Paquistão*). Stanza
  now only decides whether an occurrence is a verb, which keeps the adverb
  *fora* ("outside") out, and a next-word rule (`scripts/serir.py`) picks
  *ser* or *ir*. Scored against 100 random corpus lines checked by hand
  (`eval/ser_ir_sample.tsv`): 95.9% right on the verb uses it decides,
  abstaining on 9%; none of the 19 adverbial *fora* lines reaches it. On a
  held-out sample of another 100 lines labeled afterwards by a
  native-speaker Portuguese teacher (`eval/ser_ir_sample2.tsv`), 93.2%
  (68/73), abstaining on 8% —
  the honest estimate, since the rule was never tuned against it.
  Abstentions, and non-verb tags on forms that are always verbs (Stanza
  tags 6% of `foi` as a conjunction in clefts like *Foi por isso que*),
  take the form's own *ser*/*ir* ratio. The build applies the rule only
  while a passing score exists for its current version. Per form, *ir* is
  now 26% of `fui`, 29% of `fomos`, 11% of `foram` and 10% of `foi`. *Ser*
  goes from 21.5M tokens to 21.3M and *ir* from 8.9M to 9.0M: `fui` and
  `fomos` move a lot, but `foi`, the biggest form by far, is mostly the
  copula.

## v0.9 — 2026-09, rebuilt pipeline, human-checked (private checkpoint)

The first version whose pipeline is in this repository. `python -m
scripts.build` regenerates `out/` from the corpus, byte for byte, with the
pinned library versions.

**Overlap with April.** 79.5% of the April top-5,000 is still in the top
5,000 (Spearman ρ 0.948 on the shared words); 62.4% of the 5,001–10,000
band (ρ 0.879). Most of the movement is deliberate — the April list counted
the same word several times, and this release does not.

### Why ranks moved

- **One word, one entry.** April's lemmatizer left inflected forms and
  spelling variants as separate entries: `nao` at rank 1004 beside `não`,
  `acha` beside `achar`, `chega` beside `chegar`, `exactamente` and
  `exatamente` counted apart. They are now merged, which raises the
  surviving headword and frees the rank the duplicate occupied.
- **A better lemmatizer.** simplemma alone was replaced by Stanza, reading
  each word in real sentences, with a dictionary check and simplemma as the
  fallback: 98.5% correct on a human-reviewed sample, against 90.4% for
  simplemma alone.
- **`ser` and `ir` separated** — *later found not to work; see
  Unreleased.* April assigned `foi`, `fomos`, `foram` wholesale to `ir`.
  They were split by the tagger: `ir` fell from 11.2M tokens to 9.5M, and
  `ser` rose from 20.6M to 22.9M.
- **Enclitics split.** April counted `dá-me` and `vou-me` as single words
  (its README said otherwise). They are now split into verb + pronoun, so
  `vai-te embora` no longer creates its own entries, and object pronouns
  (`me` rank 15, `te` 23, `lhe` 70) are counted in full.
- **Lemmatization conventions**, written down in
  [eval/conventions.md](eval/conventions.md): contractions are entries,
  nouns for people keep the feminine (`senhora`, `rapariga`), diminutives
  and comparatives stay separate, and headwords use the post-1990
  spelling.
- **`a` is now separate from `o`.** April folded the preposition/article
  `a` into `o`; `o` drops from 58.1M tokens to 29.9M, and `a` rises from
  rank 8281 to rank 3.
- **Proper nouns removed properly.** April kept `john` (rank 449), `mr`,
  `charlie`, `peter` and `joe` as vocabulary. Names are now removed by capitalization, with
  every dictionary word removed at 5,000+ occurrences reviewed by hand —
  `deus`, `sr` and `natal` stay.
- **Corrections to April's exclusions.** `cara` ("face") was excluded as
  Brazilian by mistake and is back (rank 340); the unaccented `voce`
  slipped past the BP filter and is now caught.
- **Junk removed.** The subtitle watermark `pt-subs rips`, the MWE `d c`,
  English plurals (`zombies`) and one- or two-letter fragments are gone.

### Also new

- A 400-word gold set, human-reviewed ([eval/lemma_gold.tsv](eval/lemma_gold.tsv)),
  and a quality gate that fails the build on suspected duplicate entries.
  The release passes it. Six missing-accent pairs below the folding
  threshold are accepted as known typo pairs and listed in the README.
- Reports in [reports/](reports/): comparison with April, the quality gate
  with every accent fold, and the lemmatizer comparison.
- Multi-word expressions: 302 in the top 10,000 (April: 290).
- Token count 636,214,452 (April: 623,920,347), because split enclitic
  pronouns now count as tokens of their own.

### Unchanged

The `pos_guess` column was still a rule-based heuristic, reconstructed
from the April list.

## 2026-04 — first version, unpublished (`v0-april-2026`)

Frequency list of the top 10,000 lemmas, with Anki decks, produced by a
pipeline whose scripts were later lost. Automatic output, not reviewed,
and never published.
Kept in [archive/out_april_2026/](archive/out_april_2026/) for comparison.

Known problems, all found while rebuilding: inflected forms and accent
variants counted as separate entries, `ser`/`ir` conflated, enclitic
clusters left unsplit despite the documentation, names (`john`, `charlie`)
and a subtitle watermark in the list, and `cara` excluded as Brazilian by
mistake.
