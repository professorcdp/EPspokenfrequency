# EP Spoken Frequency — notes for Claude

## About this project

Python. A two-pass pipeline over a 1.1 GB gzipped corpus that produces the ranked
lists, the Anki deck and the glosses in `out/`. See [PROJECT.md](PROJECT.md) for
what it is and where it stands.

The documentation that already exists is the real reference, so read it rather than
re-deriving things:

| For | Read |
|---|---|
| What the list is, its limits, how to reproduce it | [README.md](README.md) |
| What changed in each release, and the v1.1 work in progress | [CHANGELOG.md](CHANGELOG.md) |
| Running and changing the pipeline, module by module | [scripts/README.md](scripts/README.md) |
| The human-decision files and how they are scored | [eval/README.md](eval/README.md) |
| Where the corpus comes from and how to download it | [DATA_SOURCES.md](DATA_SOURCES.md) |
| The working arrangement, past decisions, Jim-only tasks | [docs/context-from-cowork.md](docs/context-from-cowork.md) |
| Build reports: comparison, quality gate, gloss gates | [reports/](reports/) |

## How to build, run and test

The virtual environment is `./.venv`, so commands use `./.venv/bin/python`.

| To | Run |
|---|---|
| Rebuild everything into `out/` and `reports/` | `./.venv/bin/python -m scripts.build` |
| Run the tests (none need the corpus) | `./.venv/bin/python -m pytest tests/ -q` |
| Rebuild the glosses and their gates from cache, no API calls | `./.venv/bin/python -m scripts.gloss --report` |
| Re-ask the glosses that failed or are missing | `./.venv/bin/python -m scripts.gloss --retry` |

A full build takes about an hour from cold, nearly all of it the Stanza tagging
pass; with `.cache/` warm it is about a minute. The build exits 0 on success and 1
if the quality gate finds a duplicate entry that `config.yaml` does not accept —
every output is still written first.

## Things that are easy to get wrong

- **Every tunable lives in `config.yaml`**, not in code. Stage 2 fixes sit behind
  individual `fixes.*` flags so stage 1 keeps reproducing the April 2026 baseline.
- **Human decisions live in `eval/`**, and regenerating tools must merge rather
  than overwrite. Overwriting `eval/gloss_review.tsv` once destroyed 257
  native-speaker verdicts.
- **The corpus is never in the repo.** `data/` is ignored; `DATA_SOURCES.md` says
  how to fetch it.
- **The gloss response cache in `cache/gloss/` is ignored and cost $24.95 to
  produce.** Changing a row's lemma, part of speech or prompt re-keys it and bills
  it again.
- **Anki note identity comes from lemma plus part of speech.** Changing a
  published part of speech makes a re-import create a second note rather than
  update the first.
- **Before any rebuild, snapshot `out/` and `reports/`** and diff afterwards. Every
  round of fixes so far has moved something nobody expected.

## 2nd brain workflow

### At the start of every session

0. Open by stating this project's stamp in one line, e.g. "This is a BUSINESS
   project." Read it from the `.claude-account` marker file in the project folder
   (that marker is what actually routes the folder to the right Claude Max account)
   and check it agrees with PROJECT.md. If they disagree or the marker is missing,
   tell Jim and fix it with `claude-stamp personal .` or `claude-stamp business .`
   (**Where:** VS Code terminal, in the project folder), then ask him to reload the
   VS Code window before continuing.
1. Read PROJECT.md, the latest 3 entries in the runlog, and the decision records.
2. Check open issues: `gh issue list`
3. Give Jim a short summary of where things stand and propose the next step
   (usually the top "priority: now" issue). Wait for his go-ahead before starting
   large changes.

### Task tracking (GitHub Issues)

- All work is tracked as GitHub Issues, using the `gh` tool.
- Labels: type (`feature`, `bug`, `chore`, `question`) and priority
  (`priority: now`, `priority: next`, `priority: later`).
- Reference issues in commit messages ("Fixes #12" when a commit completes one).
- Close an issue when its work is done and committed.
- New work discovered along the way becomes a new issue rather than quietly
  expanding the current task.

### At the end of every session

1. Add a runlog entry (date, what changed, issues touched, what's next).
2. Update "Current status" in PROJECT.md if it changed.
3. Record significant decisions as new decision records.
4. Commit and push.

### Rules

- Never commit secrets: API keys, passwords, certificates, .p8 keys, .env files.
- Before creating issues or pushing, check `gh auth status` matches the project's
  stamp.
- The Claude account is chosen by the folder's `.claude-account` marker, never by
  signing in or out. `claude auth status` shows which account this folder is
  metered to.
