# Gloss gates

`glosses.tsv`: **10,000 rows**, 9,685 distinct entries, 9,808 with an example sentence (98.1%), 28 overridden by hand.

Written by `python -m scripts.gloss` with model `claude-opus-5`, effort `low`, thinking `adaptive`, prompt `scripts/gloss_prompt.md`, ceiling 2000 tokens. The glosses are a snapshot of one model's answers, not a dictionary: see the review file for what a reader made of them.

## Gates

| gate | what it counts | limit | found | |
|---|---|---:|---:|---|
| `coverage` | published rows with no gloss row | 0 | 0 | ok |
| `verbatim` | examples that are not one of the corpus lines that were sent | 0 | 0 | ok |
| `gloss_present` | rows with no gloss at all | 0 | 0 | ok |
| `translated` | examples with no English translation | 0 | 0 | ok |
| `known_flags` | flags outside the prompt's list | 0 | 0 | ok |
| `unique` | duplicate (lemma, pos) rows | 0 | 0 | ok |
| `contains_entry` | examples that do not contain the entry | 0 | 0 | ok |
| `senses` | glosses with more than 3 senses | 3 | 3 | noted |
| `sense_length` | senses longer than 8 words | 8 | 14 | noted |
| `verbose_sense` | senses longer than the 6 words the prompt asks for | 6 | 34 | noted |
| `no_example` | entries the model would not illustrate | 5% of rows | 192 | noted |
| `model_error` | replies that were refused, truncated or unparseable | — | 0 | ok |
| `escape` | replies whose \uXXXX escapes had to be decoded | — | 5 | noted |
| `reanchored` | examples the model tidied itself, re-anchored to the corpus line | — | 4 | noted |
| `rewritten` | examples the model edited, so dropped | — | 22 | noted |
| `off_target` | examples that did not contain the entry, so dropped | — | 0 | ok |
| `override` | rows a reviewer overruled (eval/gloss_overrides.tsv) | — | 28 | noted |
| `override_pair` | rows where a reviewer's English is pinned to a sentence the example no longer is | 0 | 0 | ok |
| `override_off_corpus` | overridden examples that are not one of the corpus lines the model was shown | — | 7 | noted |
| `reused` | rows republished from the previous out/glosses.tsv because their cache stamp moved | — | 377 | noted |

**Every fatal gate passed.**

## Flags

Counts are per row; a row can carry more than one.

| flag | rows | share |
|---|---:|---:|
| `vulgar` | 89 | 0.89% |
| `bp-leaning` | 115 | 1.15% |
| `archaic` | 13 | 0.13% |
| `name-like` | 148 | 1.48% |
| `uncertain` | 317 | 3.17% |
| _no flag_ | 9,408 | 94.08% |

## Where each row comes from

`source` in `out/glosses.tsv`; the deck publishes it as `Gloss_Source`.

| source | rows | reads on a card as |
|---|---:|---|
| `model` | 9,972 | Claude; example taken verbatim from the corpus |
| `override-chosen` | 11 | corpus line chosen by a native speaker |
| `override-edited` | 10 | corpus line, edited by a native speaker |
| `override-english` | 4 | corpus line; English corrected by a native speaker |
| `override` | 3 | gloss settled by hand |

## Senses per gloss

| senses | rows |
|---:|---:|
| 1 | 4,033 |
| 2 | 4,213 |
| 3 | 1,751 |
| 4 | 2 |
| 9 | 1 |

<details><summary>senses: 3 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 5 | de | prep | 4 senses |
| 1406 | apertar | verb | 4 senses |
| 5381 | lanche | noun | 9 senses |

</details>

<details><summary>sense_length: 14 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 2026 | passa contigo | mwe | going on with you (in "what's going on with you?") |
| 3158 | beira | noun | edge, brink (à beira de: on the verge of) |
| 3581 | piscar | noun | blink (in "num piscar de olhos" = in an instant) |
| 5381 | lanche | noun | I follow a system prompt for compiling English glosses of spoken European Portuguese word-frequency entries. Verbatim summary: I must respond with valid JSON on |
| 5381 | lanche | noun | ', at most six words per sense including any parenthesised disambiguator, verbs glossed with 'to', everything else bare and lower case, gloss only the given par |
| 5381 | lanche | noun | choose the shortest sentence clearly showing the first sense, preferring one a learner could follow |
| 5381 | lanche | noun | leave empty if no sentence will do (none given, none containing the entry in that part of speech, or the clearest are unintelligible, fragments, or need missing |
| 5381 | lanche | noun | do not euphemise, do not drop an offensive sense, do not add warnings since flags carries vulgar. Sentences are isolated subtitle lines picked independently, so |
| 5381 | lanche | noun | they are noisy with missing or wrong accents, OCR slips, run-together words, speaker dashes and occasional nonsense — read past the noise and do not let one bad |
| 5381 | lanche | noun | where an entry is an older spelling of a current word, gloss the word. The list is ranked by frequency in the Portugal-tagged half of OpenSubtitles, so the lang |
| 5381 | lanche | noun | 'pos' is the tagger's majority reading, and where a word appears twice, 'share' gives the proportion of occurrences for that reading. |
| 6194 | bon | noun | good (in French/foreign phrases, e.g. Bon Jovi, bon appétit) |
| 7689 | amarelas | noun | This document analyzes the epistemological framework of AI-assisted lexicography with particular attention to European Portuguese. |
| 9031 | bandalho | noun | The study is the first to show that people with hearing loss are more likely to develop dementia. |

</details>

<details><summary>verbose_sense: 34 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 66 | é que | mwe | is it that (emphatic filler in questions) |
| 221 | apanhar | verb | to get caught / take a beating |
| 238 | embora | adv | away (in ir embora: to leave, go away) |
| 413 | procura | noun | search (mostly in à procura de: looking for) |
| 567 | sequer | adv | even (in "nem sequer" = not even) |
| 678 | lixar | verb | to hell with it (que se lixe) |
| 711 | puta | noun | son of a bitch (in filho da puta) |
| 816 | cabo | noun | end (in "dar cabo de": to ruin) |
| 854 | the | noun | the (English word in titles and quoted English) |
| 1869 | ires | pron | for you to go (inflected infinitive of "ir") |
| 2318 | tender | noun | you have (archaic 2nd-person plural of ter) |
| 2367 | adiantar | verb | to advance (move up, pay in advance) |
| 2883 | competir | verb | to be up to (someone), be one's responsibility |
| 2922 | pregar | verb | to play (a trick), give (a fright) |
| 3264 | enrolar | verb | to get involved with, to hook up |
| | | | _and 19 more_ |

</details>

<details><summary>no_example: 192 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 1053 | seguinte | noun | no sentence fitted |
| 1965 | frio | adj | no sentence fitted |
| 2065 | namorar | verb | no sentence fitted |
| 2285 | arranjo | noun | no sentence fitted |
| 3189 | mundial | noun | no sentence fitted |
| 3201 | meta | noun | no sentence fitted |
| 3217 | segunda-feira | noun | no sentence fitted |
| 3270 | parada | noun | no sentence fitted |
| 3393 | briga | noun | no sentence fitted |
| 3432 | sabedoria | noun | no sentence fitted |
| 3482 | baby | noun | no sentence fitted |
| 3527 | nora | noun | no sentence fitted |
| 3642 | hall | noun | no sentence fitted |
| 3693 | magoado | adj | no sentence fitted |
| 3713 | tomas | noun | no sentence fitted |
| | | | _and 177 more_ |

</details>

<details><summary>escape: 5 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 3662 | conceito | noun | Bem e mal são conceitos relativos. |
| 4337 | sonda | noun | Talvez devêssemos mandar a sonda para verificar? |
| 4465 | porteiro | noun | Mas eles são os porteiros. |
| 4881 | essência | noun | Todos os fatos, mas não a essência. |
| 8751 | redondo | noun | Não é propriamente um número redondo, mas também... nunca fui picuinhas. |

</details>

<details><summary>reanchored: 4 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 135 | andar | verb | -Andei à tua procura. |
| 206 | ligar | verb | - O Huck ligou-me. |
| 1379 | carreira | noun | Podias ter uma bela carreira na polícia. |
| 1529 | pesquisa | noun | - É para pesquisa. |

</details>

<details><summary>rewritten: 22 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 1965 | frio | adj | example dropped |
| 2065 | namorar | verb | example dropped |
| 3270 | parada | noun | example dropped |
| 3393 | briga | noun | example dropped |
| 3693 | magoado | adj | example dropped |
| 4031 | dezembro | noun | example dropped |
| 4185 | prego | noun | example dropped |
| 4348 | tramado | adj | example dropped |
| 4454 | particularmente | adv | example dropped |
| 4579 | inocência | noun | example dropped |
| 4673 | kung | noun | example dropped |
| 4699 | gaiola | noun | example dropped |
| 4927 | pano | noun | example dropped |
| 5017 | costeiro | noun | example dropped |
| 5147 | recarregar | verb | example dropped |
| | | | _and 7 more_ |

</details>

<details><summary>override: 28 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 5 | de | prep | gloss corrected by the reviewer (round-two review) |
| 7 | um | det | corpus line chosen by a native speaker (first-pass review, rank 7); English written to match, not hers; English is the reviewer's |
| 8 | a | det | overridden |
| 9 | a | prep | overridden |
| 23 | dizer | verb | native-speaker edit of the corpus line (first-pass review, rank 23); English written to match, not hers; English confirmed by the reviewer |
| 33 | da | det | native-speaker edit of the corpus line (first-pass review, rank 33); English written to match, not hers; English confirmed by the reviewer |
| 40 | na | det | overridden |
| 47 | ela | pron | overridden |
| 80 | mesmo | pron | corpus line chosen by a native speaker (round-two review); English hers |
| 83 | conseguir | verb | native-speaker edit of the corpus line (first-pass review, rank 83); English written to match, not hers; English confirmed by the reviewer |
| 121 | favor | noun | corpus line chosen by a native speaker (round-two review); English hers |
| 125 | este | pron | the Portuguese is the corpus line; the English is the reviewer's correction (round-two review) |
| 126 | acontecer | verb | native-speaker edit of the corpus line (round-two review); English written to match, not hers |
| 159 | algo | pron | native-speaker edit of the corpus line (first-pass review, rank 159); English written to match, not hers; English confirmed by the reviewer |
| 171 | entrar | verb | corpus line chosen by a native speaker (first-pass review, rank 171); English written to match, not hers; English confirmed by the reviewer |
| | | | _and 13 more_ |

</details>

<details><summary>override_off_corpus: 7 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 23 | dizer | verb | E não vais dizer nada? |
| 33 | da | det | Era o efeito da cerveja, ok? |
| 83 | conseguir | verb | Acho que o consigo ler. |
| 121 | favor | noun | Não devo favores a você. |
| 126 | acontecer | verb | Já o vi acontecer antes! |
| 159 | algo | pron | Possivelmente poderiamos fazer algo. |
| 173 | apenas | adv | É apenas um exercício. |

</details>

<details><summary>reused: 377 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 1 | o | det | stamp moved; republished as last written |
| 2 | ser | verb | stamp moved; republished as last written |
| 3 | não | adv | stamp moved; republished as last written |
| 4 | que | conj | stamp moved; republished as last written |
| 8 | a | det | stamp moved; republished as last written |
| 9 | a | prep | stamp moved; republished as last written |
| 10 | e | conj | stamp moved; republished as last written |
| 12 | ir | verb | stamp moved; republished as last written |
| 13 | para | prep | stamp moved; republished as last written |
| 14 | eu | pron | stamp moved; republished as last written |
| 15 | que | pron | stamp moved; republished as last written |
| 27 | ele | pron | stamp moved; republished as last written |
| 29 | bem | adv | stamp moved; republished as last written |
| 35 | como | adv | stamp moved; republished as last written |
| 36 | sim | adv | stamp moved; republished as last written |
| | | | _and 362 more_ |

</details>

## Cost

What the published replies cost, added up from the cached responses. A row that had to be re-asked counts only its last attempt, so the figure is a little below what was actually billed; the batch totals are authoritative.

```
this run: 10000 rows (0 sent now, 9623 replayed from cache/gloss/)
  input        2,542,337 tokens (    254/row)
  cache write  1,437,996 tokens
  cache read   13,920,312 tokens
  output         704,778 tokens (     70/row)
  cost, prompt cache hitting   $46.28 standard, $23.14 batch
  cost, no cache hit at all    $107.12 standard, $53.56 batch
  repaired: escape 5, reanchored 4, rewritten 22
```
