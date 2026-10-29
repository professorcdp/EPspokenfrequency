# European Portuguese Spoken Frequency List

A frequency list of the **10,000 most common lemmas in European Portuguese
film and TV dialogue**, built from the Portugal-tagged portion of the
OpenSubtitles 2018 corpus — 636 million tokens of subtitle text.

Ready-to-import Anki decks are included, with an English gloss and a real
example sentence on every card.

| | |
|---|---|
| Entries | 10,000 rows (two files of 5,000): 9,392 distinct words, 309 of them listed once per part of speech, plus 296 multi-word expressions |
| Corpus | OPUS OpenSubtitles v2018, `pt` (Portugal-tagged) |
| Corpus size | 118,469,705 lines · 636,582,535 tokens · 827,895 unique surface types |
| Lemmatization accuracy | 98.5% on a 332-word human-reviewed sample |
| Glosses | All 10,000 have an English gloss; 9,808 also have an example sentence from the corpus. A native-speaker teacher checked all of the top 500: 479 good, 20 fix, 1 wrong |
| Part of speech | From a neural tagger (Stanza), by majority vote over up to 50 sentences per word |
| Licence | Data and docs (`out/`, `eval/`, `reports/`, `archive/`, README, CHANGELOG, DATA_SOURCES): CC BY-SA 4.0 — see [LICENSE-DATA](LICENSE-DATA). Code (`scripts/`, `tests/`, `config.yaml`, `requirements.txt`): MIT — see [LICENSE](LICENSE) |

An earlier version of this list (April 2026) was never published; the
pipeline that produced it was lost. It is kept for comparison only in
[`archive/out_april_2026/`](archive/out_april_2026/) (tag
`v0-april-2026`), and [CHANGELOG.md](CHANGELOG.md) records how this list
differs from it.

---

## Who this is for

**Learners of European Portuguese** who want to study vocabulary in the
order they are likely to actually hear it. If you have worked through a
beginner course and want a principled answer to "what should I learn
next?", a frequency list built from dialogue is a reasonable guide — and
the Anki decks in `out/` let you start tonight.

It is particularly aimed at learners who keep finding that the Portuguese
in their textbook is Brazilian, or that their word list is drawn from
newspapers rather than conversation.

**Researchers and tool-builders** may find the lists useful as a rough
register baseline, provided you read the Limitations below first and treat
the numbers accordingly.

**It is not a course, a dictionary, or a substitute for either.** The
glosses in [`out/glosses.tsv`](out/glosses.tsv) are a one-to-three-word
English hint per entry and one real corpus sentence, written by a language
model in a single pass — a snapshot of what that model said on one day,
not a lexicographer's definition.

**The first 500 have been checked by a native-speaker Portuguese teacher**,
over two rounds covering all 500: she passed 479, asked for a fix on 20 and
called one wrong, and her corrections are in the published glosses. Those are
the words a learner meets first, which is where the checking went.

**The other 9,500 have not been checked by anyone.** A sample of 200 of them
is set aside for review and is still unreviewed. Below rank 500, treat a gloss
as a starting point and a dictionary as the authority.

---

## Limitations

**Please read this section before you rely on anything here.** This is a
hobbyist project, and being honest about what it is not is more useful than
overselling what it is.

### This is subtitle text, not a balanced corpus

Every number here comes from one source: subtitles for films and TV shows.
That has real consequences.

- **Subtitles are written approximations of speech, not speech.** They are
  condensed to fit reading speed, cleaned of disfluencies, hesitations,
  repairs, and overlaps, and they lose everything about how something was
  said. Real conversation looks different.
- **The register is dramatic dialogue.** Film and TV over-represent crime,
  conflict, romance, and emergencies. *Matar* ("to kill") lands at rank
  121, *morrer* at 153, *arma* at 248 and *polícia* at 267 — higher than
  any corpus of everyday life would put them. The vocabulary of work,
  admin, school and errands correspondingly sits lower.
- **Much of it is translated.** A large share of these subtitles are
  translations of English-language film and TV, so the phrasing can carry
  translation artifacts and English-shaped idiom rather than natively
  produced Portuguese.
- **The `pt` tag is corpus metadata, not verified provenance.** It is a
  strong signal of European Portuguese, but Brazilian material can leak
  through. An explicit BP exclusion list is applied, and it is a blunt
  instrument — it removes obvious markers, not every Brazilianism.
- **It is single-genre and one snapshot in time.** No news, no academic
  prose, no fiction, no non-fiction, no actual recorded conversation, and
  nothing newer than the 2018 corpus release.
- **Neighbouring lines are not a scene.** The corpus file is a stream of
  subtitle lines that has been deduplicated, reordered and interleaved
  across different subtitle versions of the same films, so two adjacent
  lines usually do not belong to one exchange. Counting and tagging are
  unaffected, since both work a line at a time, but every "sample sentence"
  in this project is an isolated line: do not read the lines around one as
  its context, and do not build an annotation task that relies on them.

### How this differs from Davies

The standard published reference is Mark Davies and Ana Maria Raposo
Preto-Bay's *A Frequency Dictionary of Portuguese* (Routledge, 2008). If
you are choosing between them, choose Davies — it is peer-reviewed,
professionally edited, and comes with the things this list lacks.

|  | This list | Davies |
|---|---|---|
| Corpus | ~636M tokens, subtitles only | ~20M tokens across four registers, unevenly weighted: 18M written and 2M spoken |
| Registers | Film/TV dialogue | Fiction, newspaper and academic at 6M words each, and spoken at 2M — 10% of the corpus. Each register is half Portugal, half Brazil. Nearly all of it is 1970–2000, mostly the 1990s |
| Ordering | Raw frequency: occurrences counted, ranked, published | A composite score, not raw frequency. Every register counts equally whatever its size, and within a register the score is half log frequency and half *range* — how many of 100 blocks of 200,000 words the word turns up in. An evenly spread word can outrank a commoner one that clusters |
| Variety | Portugal-tagged, BP markers excluded post hoc; headwords in post-1990 spelling | Both varieties, with BP/EP marked per entry |
| Glosses & examples | One to three English senses per entry and one example sentence taken verbatim from the corpus, written by a language model in one pass. The top 500 checked by a native-speaker teacher; the other 9,500 unchecked | English glosses and example sentences throughout, written and edited by lexicographers |
| Lemmatization | Automatic: a neural tagger (Stanza) reading each word in up to 50 real sentences, checked against a dictionary. 98.5% correct on a 332-word hand-checked sample | Curated |
| POS tags | Automatic, from the same tagger: majority vote over each word's sample sentences, and a word used as two parts of speech is listed once for each. Not hand-checked | Professionally tagged |
| Contractions (*do*, *ao*, *pela*) | Kept as their own entries | Split into preposition + article |
| Review | Automatic output, with about 1,360 decisions made by hand: the gold set, gender pairs and proper-noun drops, plus a native speaker's verdict on every one of the top 500 glosses. Below rank 500 it is not edited entry by entry | Edited and peer-reviewed |
| Cost | Free | A book you buy |

One row is worth spelling out, because it is the easiest way to compare the
two lists wrongly. **Davies's spoken register is not this list's register.**
Of his 2.0M spoken words only 1.0M are from Portugal, and that million is
0.437M of recorded informal conversation (CORDIAL-SIN, CRPC, Português
Falado) plus 0.563M of **interviews transcribed in newspapers and
magazines**, screened for colloquial forms like *pra*. No broadcast material
is described. So most of his Portuguese "spoken" data is interview speech
that arrived through print, and recorded conversation from Portugal is
about 2% of his whole corpus — while this list is dramatic dialogue end to
end. Where the two disagree about a word, that difference in kind is usually
the reason, not an error in either. (Introduction, Table 1 and pp. 2, 6–8.)

What this list offers that Davies does not is scale on a single register
and a strictly European-Portuguese slant: 30× more tokens, all of it
dialogue, with Brazilian markers filtered out. That makes it a decent
*complement* to Davies for a learner targeting spoken EP. It is not a
replacement, and it has not been edited the way a published dictionary is.

### Known technical caveats

These are specific and worth knowing before you study from the list.

- **Part of speech is tagger output, not hand-checked.** The `pos`
  column is Stanza's tag, by majority vote over each word's sample
  sentences (50 for the 4,350 most frequent word forms, 5 for the rest).
  The tagger is not always consistent with itself: 3% of its tags
  contradicted the lemma it gave in the same sentence (a VERB tag on the
  noun *pergunta*) and were discarded. A word the tagger regularly uses two
  ways gets one row per part of speech, with its count divided between
  them: `a` (article and preposition), `que` (conjunction and pronoun),
  `este` (determiner and pronoun), `morto` (adjective and noun). The tags
  follow Universal Dependencies conventions, with one exception made for
  learners: a preposition is never counted as a conjunction (UD tags *para*
  in *para fazer* as one). Entries the tagger never saw intact keep a
  rule-based guess, except the contractions, which are all published as
  `det` (see below).
- <a id="the-glosses-are-a-model-snapshot"></a>**The glosses are a model
  snapshot, not a reference work.** Every gloss and translation in
  `out/glosses.tsv` was written by Claude (`claude-opus-5`) in a single
  pass, one request per entry, from the entry, its part of speech, its
  frequency and up to twenty real corpus sentences containing it. The
  prompt is in the repository
  ([scripts/gloss_prompt.md](scripts/gloss_prompt.md)) because the glosses
  cannot be read as evidence without it. A native speaker checked the top
  500; nobody checked the other 9,500. Two consequences worth knowing: the
  model chose which sense to put first, so the order reflects its judgement
  of spoken frequency rather than a count; and re-running the same prompt on
  a newer model would not give the same answers, so unlike the lists
  themselves the glosses are not reproducible byte for byte. The example
  sentences are the one part that is verifiable — each is a corpus line,
  copied unaltered but for a leading dialogue dash and surrounding quotation
  marks, and the build rejects any the model did not copy exactly. Where the
  model edited a sentence rather than quoting it (22 entries), the example
  was dropped and the entry keeps its gloss alone; 192 entries have no
  example because none of the sampled lines showed the entry in the sense
  being glossed.
- **Contractions are labelled by what they contract, not by the tagger.**
  Stanza expands *do*, *nas*, *pelo* and the rest into two words before
  tagging, so the surface token collects almost no usable evidence: before
  this release *nas*, *no* and 26 others read `unk`, and the ones with a
  stray tag read worse — *pelo* as a noun, *deste* as a verb, *contigo*
  split across three parts of speech. Each form now gets one decided
  answer: preposition + article or demonstrative is `det` (*do*, *nas*,
  *pelo*, *num*, *deste*, *naquela* — 58 forms), preposition + pronoun is
  `pron` (*dele*, *comigo*, *disso*, *nisto*, *daquilo* — 19), and
  preposition + adverb of place is `adv` (*daqui*, *daí*, *dali*). This is
  a decision, not tagger output, and it is the one part of the `pos` column
  that does not come from Stanza.
- **`ser` and `ir` are separated by a rule, not by the tagger.** `foi`,
  `fui`, `fomos`, `foram` and `fora` belong to *ser* ("was") or *ir*
  ("went") depending on the sentence, and the tagger assigns them to *ser*
  almost every time (*fui ao Paquistão* included). So the tagger only
  decides whether an occurrence is a verb at all — the adverb *fora*,
  "outside", is not — and a rule reading the neighbouring words picks the
  verb: *ir* before *a*, *ao*, *para*, *embora* or an infinitive, or after
  *lá*; *ser* before a participle, an adjective, a noun phrase or nothing.
  On the 100 lines used to develop it, it is right on 95.9% of the verb
  uses it decides; on a **held-out** 100 lines labeled afterwards by a
  native-speaker Portuguese teacher, **93.2%** (68 of 73), abstaining on
  8%. An abstention takes the form's own *ser*/*ir* ratio. Every one of
  those five held-out errors calls an *ir* use *ser* (*já fomos*, *já foram
  todos?*), so *ir* is still undercounted a little. The split is estimated from 1,000 random
  lines per form, so each form's share is good to about ±3 percentage
  points. It misses idioms (*ele não foi nessa*) and elliptical questions (*sempre
  foram?*). *Ser* counts 22.3M tokens and *ir* 9.0M.
- **Lemmatization is not perfect.** 98.5% on the hand-checked sample means
  something like 150 of the 10,000 entries may carry a lemma error. The
  known pattern: Stanza sometimes reads a verb form as a noun (`procura`,
  `mentes`, `sacas` kept as nouns) or picks the wrong verb (`vejam` as
  *vir*, not *ver*).
- **Split counts are estimates.** Participles (`educados`: the verb
  *educar* or the adjective *educado*) and words used as two parts of
  speech have their counts divided according to how the tagger reads a
  sample of sentences: 50 for word forms with 10,000+ occurrences, which
  gives 2% steps, and 5 for the rest (20% steps).
- **Six known duplicates remain.** Missing-accent forms are folded into
  their accented twin only when the accented form is at least 10× as
  frequent. Six pairs fall below that and appear twice: `camera`/`câmera`,
  `frigorifico`/`frigorífico`, `amen`/`ámen`, `bla`/`blá`, `mafia`/`máfia`,
  `karate`/`karaté`. They are accepted as known typo pairs rather than
  hidden. Treat the unaccented one as a typo of the other.
- **Folding by frequency can over-merge.** The same 10× rule folds a rare
  unaccented form into a common accented one even when the rare form is a
  real word. Every fold is listed in `reports/QUALITY.md`, with the
  borderline ones (10–20×) in their own section.
- **Proper nouns are removed by capitalization, and some will slip
  through.** A word is treated as a name if it is capitalized away from the
  start of a line almost every time. Dictionary words that the filter
  removed at 5,000+ occurrences were reviewed one by one — `deus`, `sr`,
  `natal` and 26 others were restored — but names below that threshold were
  not reviewed. Everything removed with 100+ occurrences is listed in
  `out/dropped_proper_nouns.txt`.
- **English words are only partly filtered.** English plurals and many
  English names are removed; other English words that turn up in
  Portuguese dialogue (`ok`, `zombie`) are kept, deliberately in the case of
  `ok`.
- **MWE counts are an overlay, not a replacement.** An MWE's `raw_freq` is
  the bigram count, and it is *not* subtracted from its constituent words'
  lemma counts. This is the usual frequency-list convention, but it means
  the column does not sum to the corpus.

---

## What's in `out/`

Two rank bands — **1–5000** and **5001–10000** — each published in four
formats. Files without a number in the name are the first band.

### The frequency lists

| File | What it is |
|---|---|
| `ep_spoken_top5000.tsv` / `.csv` | Ranks 1–5000. The main list. |
| `ep_spoken_5001_10000.tsv` / `.csv` | Ranks 5001–10000. |

TSV and CSV hold identical data; pick whichever your tools prefer. Columns:

| Column | Meaning |
|---|---|
| `rank` | 1-based rank by `raw_freq`. |
| `lemma` | Lemma form, or the surface multi-word expression for MWE entries. |
| `is_mwe` | `1` for a multi-word expression, `0` otherwise. |
| `pos` | Part of speech from the tagger. One of `det`, `prep`, `conj`, `pron`, `adv`, `intj`, `num`, `noun`, `adj`, `verb`, `mwe`, `unk`. A word used as two parts of speech has one row for each. See caveats. |
| `raw_freq` | Lemma occurrence count across the full corpus. |
| `freq_per_million` | Occurrences per million tokens (of 636,582,535). |

### The Anki decks

| File | What it is |
|---|---|
| `EP_Spoken_Frequency.apkg` | **Ready to import**: twenty decks of 500 words, glossed throughout, with the note type and the card templates in one package. See [Importing the Anki decks](#importing-the-anki-decks). |
| `ep_spoken_anki_minimal.tsv` | Rank, Lemma_PT, POS, Is_MWE, Raw_Freq, Freq_per_million, Tags |
| `ep_spoken_anki_enrichable.tsv` | The same, plus `Gloss_EN`, `Example_PT`, `Example_EN` and `Gloss_Source`, all filled in |
| `ep_spoken_5001_10000_anki_minimal.tsv` | Ranks 5001–10000, minimal fields |
| `ep_spoken_5001_10000_anki_enrichable.tsv` | Ranks 5001–10000, enrichable fields |

### The glosses

| File | What it is |
|---|---|
| `glosses.tsv` | One row per entry: `gloss` (one to three English senses, commonest first), `example_pt` (a corpus line containing the entry, verbatim), `example_en` (its translation), `flags`, `source`. |

`flags` is zero or more of `vulgar`, `bp-leaning` (the form or sense is
mainly Brazilian), `archaic`, `name-like` (in this corpus the token is
probably mostly a name) and `uncertain` (the model was not confident).
Slang and vulgarities are glossed plainly: this is a record of how people
speak, not a teaching aid. See [the caveat below](#the-glosses-are-a-model-snapshot).

`source` says where the row came from, and the deck publishes it as
`Gloss_Source`. It reads `model` for 9,972 rows. The other 28 are in
[eval/gloss_overrides.tsv](eval/gloss_overrides.tsv), where a reviewer
overruled the model:

| `source` | Rows | What a card shows |
|---|---:|---|
| `model` | 9,972 | Claude; example taken verbatim from the corpus |
| `override-chosen` | 11 | corpus line chosen by a native speaker |
| `override-edited` | 10 | corpus line, edited by a native speaker |
| `override-english` | 4 | corpus line; English corrected by a native speaker |
| `override` | 3 | gloss settled by hand |

The three kinds differ in what the reviewer touched. `override-chosen` is a
different corpus line she picked from the ones the model was shown, so it is
still verbatim. `override-edited` is a sentence she corrected and therefore no
longer verbatim — *trás*, for instance, where she restored an accent the
subtitle had dropped. Her eleventh such sentence was for *dever*, which had no
example at all until she wrote one; it is held back rather than published,
because the entry is now a verb and her sentence is the noun.
`override-english` leaves the Portuguese alone and takes only her correction
to the translation. `override` covers the three glosses settled by hand:
*caseiro*, which the model refuses to gloss, *largo*, and *de*, whose senses
she extended.

Of the English translations on those rows, 5 are hers, 12 were written here
and she confirmed them, 5 she corrected, and 3 were written here to match
sentences she supplied in the second round and she has not seen them yet.
Each row records which in its `note`.

### Quality-control files

| File | What it is |
|---|---|
| `qc_sample.csv` | A spot-check sample across the first band — a quick way to eyeball output quality without opening a 5,000-row file. |
| `dropped_proper_nouns.txt` | Words removed as proper nouns (with 100+ occurrences), plus the BP exclusions, English plurals and fragments removed by the other filters. |

The build reports are in [`reports/`](reports/): `COMPARISON.md` (this
list against the unpublished April 2026 version), `QUALITY.md` (the quality gate and every
accent fold), and `backend_scores.md` (how the lemmatizers compared).

### Release assets

Everything above is in the repository, so cloning gets you all of it. A
[tagged release](https://github.com/professorcdp/EPspokenfrequency/releases)
also attaches four files on their own, for anyone who wants the data
without the repository:

| Asset | What it is |
|---|---|
| `EP_Spoken_Frequency.apkg` | The Anki package. |
| `ep_spoken_top5000.tsv` | Ranks 1–5000. |
| `ep_spoken_5001_10000.tsv` | Ranks 5001–10000. |
| `glosses.tsv` | The glosses and example sentences, all 10,000 rows. |

A fifth file, `SHA256SUMS.txt`, carries their SHA-256 digests. Download the
assets and that file into one directory and check them with:

```bash
sha256sum -c SHA256SUMS.txt      # macOS: shasum -a 256 -c SHA256SUMS.txt
```

Each line should read `OK`. The sums are written by the build rather than
by hand, so they describe the files the pipeline actually produced; they
are in `out/SHA256SUMS.txt` in the repository too, and a rebuild that moves
any asset moves its line with it. If you are pinning this data in another
project, pin the digest and not the tag — a tag can be moved, a digest
cannot.

---

## How the list is built

From `pt.txt.gz` to `out/`, in one command (`python -m scripts.build`):

1. **Tokenize and count.** A Portuguese-aware tokenizer strips subtitle
   artifacts and lowercases. Enclitic clusters are split and the verb is
   restored: `fazê-lo` counts as *fazer* + *lo*, and `dar-lhe-ia` as
   *daria* + *lhe*.
2. **Second pass.** Bigram counts for multi-word expressions, sample
   sentences for every frequent word (50 for the 4,350 word forms with
   10,000+ occurrences, 5 for the rest), and capitalization statistics for
   the proper-noun filter.
3. **Tag and lemmatize.** [Stanza](https://stanfordnlp.github.io/stanza/)
   reads the 62,916 word forms frequent enough to reach the list inside
   their sample sentences — about 499,000 sentences, covering 62,523 of
   those forms — and gives each occurrence a lemma and a part of speech.
   The majority lemma wins, after discarding votes where the lemma and the
   tag contradict each other. When
   Stanza's answer is not a dictionary word (it occasionally invents forms
   like *agradeçar*),
   [simplemma](https://github.com/adbar/simplemma) is used instead; simplemma
   also handles the rare tail. A small table of hand-verified corrections
   covers errors Stanza makes at high frequency (`dói` is *doer*, not
   *dizer*).
4. **Resolve context-dependent forms per occurrence.** Participles are
   split between the verb and the adjective according to how Stanza tags
   them in their sample sentences. `foi`, `fui`, `fomos`, `foram` and
   `fora` are split between *ser* and *ir* by a separate next-word rule,
   because the tagger cannot tell them apart (see caveats).
5. **Apply the lemmatization conventions** in
   [eval/conventions.md](eval/conventions.md):
   1. contractions (`do`, `ao`, `pela`) are their own entries;
   2. adjectives fold to the masculine, but nouns for people keep the
      feminine (`senhora`, `rapariga`), and a feminine with its own meaning
      always stays (`música`, `sexta`) — decided pair by pair in
      [eval/gender_pairs.tsv](eval/gender_pairs.tsv);
   3. diminutives stay separate (`coisinha`);
   4. comparatives and irregular superlatives are their own entries
      (`maior`, `melhor`, `ótimo`);
   5. spelling-reform variants merge under the post-1990 spelling
      (`acção` → `ação`, `óptimo` → `ótimo`), while words that keep their
      consonant in European spelling (`facto`, `contacto`) are left alone.

   Pronouns are their own entries too (`me`, not *eu*).
6. **Fold remaining duplicates.** Each lemma is checked against the
   lemmatizer again, and regular plurals are folded onto their singular
   (guarded: `óculos`, `férias` and `cais` are not plurals of anything). An
   unaccented form folds into its accented twin when the accented form is at
   least 10× as frequent, and wrong or Brazilian accents (`näo`, `prêmio`)
   fold into the European spelling.
7. **Filter.** BP-leaning words are removed from the exclusion list —
   `aeromoça`, `bacana`, `banheiro`, `celular`, `galera`, `geladeira`,
   `legal`, `mano`, `massa`, `né`, `oi`, `trem`, `você`, `vocês`, `xícara`,
   `ônibus`, with their unaccented variants. Proper nouns are removed by
   capitalization, subject to the reviewed decisions in
   [eval/proper_noun_drops_review.tsv](eval/proper_noun_drops_review.tsv).
   English plurals are removed, and so are one- and two-letter fragments
   that are neither words nor interjections.
8. **Assign part of speech.** Each word's count is divided across the
   parts of speech the tagger gave it, the same way participle counts are
   divided across lemmas. A second part of speech becomes its own row only
   if it holds at least 25% of the word's count and at least 3 tagged
   sentences; otherwise it joins the majority.
9. **Rank and emit** the top 10,000 rows by count, with multi-word
   expressions — kept by log-likelihood (Dunning G² ≥ 2500) and a
   collocation share of at least 5% — ranked alongside them. 296 of them
   make the top 10,000: 191 in the first band and 105 in the second.

### How it is checked

- **A human-reviewed gold set.** [eval/lemma_gold.tsv](eval/lemma_gold.tsv)
  is 400 words sampled from the corpus across the frequency range, each
  checked by hand. 332 are scored; 68 were marked as names, foreign words or
  junk. The published lemmas are correct for **98.5%** of them.
- **A quality gate.** Every build looks for entries that are probably the
  same word counted twice — a form that lemmatizes to another entry, an
  accent variant of another entry, a regular plural of another entry — and
  fails if it finds any that are not explicitly accepted. **This release
  passes.** Two kinds of pair are accepted in `config.yaml`, each listed:
  words that are genuinely different (`avô`/`avó`, `pôr`/`por`,
  `cirurgiã`/`cirurgia`), and the six known typo pairs from the caveats,
  which sit below the 10× folding threshold. Any new suspect fails the
  build.
- **Two labeled *ser*/*ir* samples**, 100 corpus lines each, 20 for each of
  `foi`, `fui`, `fomos`, `foram` and `fora`.
  [eval/ser_ir_sample.tsv](eval/ser_ir_sample.tsv) was used to develop the
  rule: its labels were proposed by an AI model acting as a Portuguese
  informant and checked by hand, and the rule scores **95.9%** on the verb
  uses it decides (71 of 74).
  [eval/ser_ir_sample2.tsv](eval/ser_ir_sample2.tsv) is **held out**:
  labeled afterwards by a native-speaker Portuguese teacher, never used to
  shape the rule, and therefore the honest estimate — **93.2%**
  (68 of 73), abstaining on 8%. Stanza's verb test keeps the adverb *fora*
  away from the rule in 19 of 20 held-out cases; the exception is *lá
  fora*, which it mistagged as a verb. The build uses the rule only while a
  score of at least 95% on the development set exists for its current
  version; both tables are in
  [reports/serir_scores.md](reports/serir_scores.md).
- **Automatic gates on the glosses.** Every gloss run checks that each
  published row got a gloss, that each example sentence is one of the corpus
  lines the model was shown — character for character — and that the
  sentence really contains the entry; a run that fails any of those is not
  published. Counts, per-flag totals and what the run cost are in
  [reports/gloss_gates.md](reports/gloss_gates.md). The glosses' *meaning*
  is not gated: a sample is set aside for a reader in
  [eval/gloss_review.tsv](eval/gloss_review.tsv).
- **Determinism.** The same corpus, configuration and library versions
  produce byte-identical output. The glosses are the exception — see the
  caveat.

---

## Reproducing this

You need Python 3.13 and several GB of free disk (the corpus, Stanza's
models and PyTorch). The first build takes about an hour on an 8-core
machine; later builds reuse cached passes and take a minute.

```bash
git clone https://github.com/professorcdp/EPspokenfrequency.git
cd EPspokenfrequency
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -c "import stanza; stanza.download('pt')"
```

Download the corpus (1.1 GB) into `data/` as described in
[DATA_SOURCES.md](DATA_SOURCES.md), then:

```bash
./.venv/bin/python -m scripts.build
```

This writes `out/` and `reports/` and exits with status 0. If you change
the configuration and the build exits with status 1, the quality gate has
found a new suspected duplicate: it is listed in `reports/QUALITY.md`, and
every output has still been written.

`requirements.txt` pins the exact versions used for this release. With
them the build reproduces `out/` byte for byte; a different Stanza or
simplemma release can change individual lemmas. To rebuild the April-style
list for comparison, run `python -m scripts.build --stage 1` (output in
`build/stage1/`). [scripts/README.md](scripts/README.md) covers the other
options.

---

## Importing the Anki decks

**Use `out/EP_Spoken_Frequency.apkg`.** In Anki, choose **File → Import**,
select it, and you are done: the note type, the card templates and both
decks come with it.

- Twenty decks of 500 words each, under one parent and numbered so they
   sort in rank order: `Portuguese::European Portuguese - Spoken::01 ·
   1–500`, `::02 · 501–1000`, and so on to `::20 · 9501–10000`. Study them
   in order and you meet the commonest words first.
- One note type, `Portuguese (EP) – Spoken Frequency`, with ten fields:
  `Rank`, `Lemma_PT`, `POS`, `Gloss_EN`, `Example_PT`, `Example_EN`,
  `Is_MWE`, `Raw_Freq`, `Freq_per_million` and `Gloss_Source`.
- **Card 1 (Portuguese → English)** shows the word large, with its part of
  speech beneath it. The back gives the English gloss, the example sentence
  and its translation, then the rank, the frequency and `Gloss_Source` in
  small print.
- **Card 2 (English → Portuguese)** shows the gloss and asks for the word.
  Every note has one, because every note is glossed. (Its front is still
  wrapped in a condition on `Gloss_EN`, which is what let the 1.0 deck ship
  with no reverse cards at all.)
- **`Gloss_Source` says where each card's gloss came from** — for 9,972 of
  them that the example is a corpus line the model quoted, and for 29 that a
  native speaker chose the sentence, edited it, corrected the English, or
  that the gloss was settled by hand.
- Every note carries the tags below, the same as in the TSV files.

**There is no field for your own notes, and that is deliberate.** Anki
cannot merge fields when it imports: *Always* overwrites every field of
every note it matches, and *If newer* overwrites every field of each note it
updates. So any field this package shipped could be wiped by a later release,
along with whatever you had written in it. A place to write that we would
overwrite is worse than no place.

**To keep your own notes**, add a field yourself: **Tools → Manage Note
Types → Fields → Add**. Know the trade before you do. Once the note type
differs from the one in the package, Anki stops updating these notes
altogether — a later release will add words that are new, but your existing
notes keep the glosses and ranks they already have.

**The ten fields are frozen from 1.1.0.** Anki matches fields by position, so
adding, removing or reordering one would break re-import for everyone already
studying. Anything the deck needs later will go in a separate note type.

### Importing a later release

**If you have the 1.0 deck, delete it first** — all twenty decks — or import
1.1 into a fresh Anki profile. The note type has changed (1.0 had no
`Gloss_Source`) and 70 entries changed their part of speech, which changes
how Anki identifies them. Importing 1.1 over 1.0 does not fail; it quietly
does almost nothing. On a test import it refused 9,880 notes and added 120,
which is Anki declining to update notes across a changed note type.

Deleting the 1.0 decks loses whatever review history you have on them — the
scheduling, the intervals, the lapses. There is no way to carry it across,
and 1.0 shipped with no glosses, so what you would be keeping is history on
a deck with no English side.

**From 1.1.0 onward, re-importing works as you would expect.** Notes are
identified by their word and part of speech, so a new release matches the
notes you have instead of adding duplicates, and your review history is
kept. Anki's import screen asks whether to **Update notes**:

| Option | What happens |
|---|---|
| **If newer** | Brings in the new release's glosses, ranks and counts. This is the one to use. |
| **Always** | The same, unconditionally. |
| **Never** | Nothing is updated; new words are still added. |

*If newer* actually works now: each release carries its own timestamp, where
1.0.0's was frozen, so Anki could never see a newer copy and *If newer* did
nothing at all.

Updating replaces **every** field of each note it touches. Nothing in the
shipped fields is yours to lose — but if you have added a field of your own,
see the warning above: Anki will not update those notes at all.

### Advanced: the TSV files, for your own note type

If you want your own fields or card design, import the `*_anki_*.tsv`
files instead. They carry Anki's header directives, so Anki configures
most of the import itself: separator, note type, target deck, field
mapping and tags column are all declared in the file.

1. **Create the note type first**; Anki will not invent it for you. Go to
   **Tools → Manage Note Types → Add**, name it
   `Portuguese (EP) – Spoken Frequency`, and give it fields matching the
   file you plan to import:
   - *minimal*: `Rank`, `Lemma_PT`, `POS`, `Is_MWE`, `Raw_Freq`,
     `Freq_per_million`
   - *enrichable*: `Rank`, `Lemma_PT`, `POS`, `Gloss_EN`, `Example_PT`,
     `Example_EN`, `Is_MWE`, `Raw_Freq`, `Freq_per_million`,
     `Gloss_Source`

   (The `Tags` column is not a field; Anki maps it to note tags
   automatically.) Then design your own card templates.
2. Choose **File → Import** and select one of the `out/*_anki_*.tsv` files.
3. The import screen pre-fills from the file's headers. Check that the
   **Field separator** is Tab, the **Notetype** is `Portuguese (EP) –
   Spoken Frequency`, the **Deck** is `Portuguese::European Portuguese -
   Spoken - First 5000` (or `... - 5001 to 10000`), and **Allow HTML in
   fields** is off.
4. Click **Import**.

Do not mix the two paths in one Anki profile: the TSV import creates its
own notes, separate from the `.apkg`'s, so you would study every word
twice.

### Which file should I import?

**The `.apkg`**, unless you have a reason not to. It arrives glossed, with
both cards working from the first import and nothing to fill in.

On the advanced path, take **`ep_spoken_anki_enrichable.tsv`**, which ships
with the same glosses, examples and `Gloss_Source` filled in, or the
*minimal* file if you would rather write your own glosses from the bare
ranked list. The TSV files hold 5,000 words
each, so you will want to slice them by tag (below) as you go.

### Studying in frequency order

The twenty decks are the order. Work through `01 · 1–500` before `02 ·
501–1000`, and you learn the words roughly in the order you will hear
them. The numbers keep the decks in order in Anki's deck list, and each
deck has its own daily limits, so a deck you have not started sends you no
new cards.

Every note also carries tags, for slicing more finely than a deck — all
the verbs in the first thousand, say — from the Anki browser:

| Tag | Meaning |
|---|---|
| `freq::0001-0500`, `freq::0501-1000`, … | 500-word band (matches the decks) |
| `freq500::…` | 500-word band (alias) |
| `freq1000::0001-1000`, … | 1000-word band |
| `pos::det`, `pos::verb`, … | Part of speech |
| `source::opensubtitles_ep_v2018` | Provenance |
| `variety::EP`, `register::spoken` | Variety and register |
| `flag::vulgar` (89), `flag::bp-leaning` (115), `flag::name-like` (148), `flag::uncertain` (318), `flag::archaic` (13) | What the gloss was flagged as. Suspend `flag::vulgar` if you would rather not meet those, or search `flag::uncertain` for the glosses to check first |
| `gloss::reviewed` (500) | A native-speaker teacher passed a verdict on this entry's gloss |

The tags are on the TSV notes too, and are the only way to study those in
order, since each TSV file imports into a single 5,000-note deck.

---

## Repository layout

```
out/                   Published frequency lists and Anki decks
reports/               Build reports: comparison, quality gate, backend scores
archive/out_april_2026/  The unpublished April 2026 list, kept for comparison
eval/                  Gold set, conventions, and the hand-reviewed decision files
scripts/               The pipeline (python -m scripts.build)
tests/                 Unit tests (pytest; no corpus needed)
config.yaml            Every threshold, list and switch the pipeline uses
data/                  Corpus download target — gitignored, never committed
DATA_SOURCES.md        Corpus citation and download instructions
CHANGELOG.md           What changed between versions
```

`data/` is excluded from version control because the corpus is a 1.1 GB
file that has no business in git history. Download it yourself following
[DATA_SOURCES.md](DATA_SOURCES.md).

---

## Licence and citation

The data and the code are licensed separately:

- **The data** — the lists and Anki files in `out/`, and `eval/`,
  `reports/` and `archive/` — is **CC BY-SA 4.0**
  ([LICENSE-DATA](LICENSE-DATA)), and so is the documentation: this
  README, CHANGELOG.md and DATA_SOURCES.md. Use it, change it,
  redistribute it: keep the attribution and share derivatives alike.
- **The code** — `scripts/` (with its data tables), `tests/`,
  `config.yaml` and `requirements.txt` — is **MIT** ([LICENSE](LICENSE)),
  so you can reuse the pipeline in any project, keeping the copyright
  notice.

To attribute the data: *European Portuguese Spoken Frequency List, by Jim
Ranalli (Professor Caloiro), licensed under CC BY-SA 4.0. Derived from OPUS
OpenSubtitles v2018 (Lison & Tiedemann 2016).*

If you publish anything based on this, please cite the underlying corpus:

> Lison, P., & Tiedemann, J. (2016). OpenSubtitles2016: Extracting Large
> Parallel Corpora from Movie and TV Subtitles. *LREC 2016*.

Full citations, BibTeX and upstream terms are in
[DATA_SOURCES.md](DATA_SOURCES.md).
