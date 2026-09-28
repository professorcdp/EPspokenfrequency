"""Regenerate eval/proper_noun_drops_review.tsv without losing decisions.

The review file lists PT dictionary words the proper-noun filter drops
(>= review_min_count occurrences) for a human keep/drop decision.  Once
those decisions are loaded as a keep-list, the kept words stop appearing in
the drop log -- so the file is merged, never rebuilt from the log:

  * every row already in the file is kept, with its decision;
  * count and cap_ratio are refreshed from the latest stage 2 build, and
    the previous cap_ratio is kept alongside for comparison;
  * filter_drops says whether the filter, keep-list ignored, still drops
    the word on its own;
  * words the filter now drops that were not in the file are appended with
    a blank decision, and printed.

Input: reports/proper_noun_audit.tsv, written by every stage 2
build.

    python -m scripts.make_proper_noun_review
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

COLUMNS = ["lemma", "count", "cap_ratio", "cap_ratio_before", "filter_drops",
           "decision", "note"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="reports/proper_noun_audit.tsv")
    ap.add_argument("--out", default="eval/proper_noun_drops_review.tsv")
    args = ap.parse_args()

    with open(args.audit, encoding="utf-8", newline="") as fh:
        audit = {r["lemma"]: r for r in csv.DictReader(fh, delimiter="\t")}

    out = Path(args.out)
    previous: list[dict[str, str]] = []
    if out.is_file():
        with out.open(encoding="utf-8", newline="") as fh:
            previous = list(csv.DictReader(fh, delimiter="\t"))
    known = {r["lemma"] for r in previous}

    rows: list[dict[str, str]] = []
    for r in previous:
        a = audit.get(r["lemma"], {})
        before = r.get("cap_ratio_before") or r.get("cap_ratio", "")
        rows.append({
            "lemma": r["lemma"],
            "count": a.get("count", r.get("count", "")),
            "cap_ratio": a.get("cap_ratio", ""),
            "cap_ratio_before": before,
            "filter_drops": a.get("filter_drops", ""),
            "decision": (r.get("decision") or "").strip(),
            "note": (r.get("note") or "").strip(),
        })
    new = [a for lemma, a in audit.items() if lemma not in known and a["filter_drops"] == "yes"]
    for a in sorted(new, key=lambda a: (-int(a["count"]), a["lemma"])):
        rows.append({"lemma": a["lemma"], "count": a["count"], "cap_ratio": a["cap_ratio"],
                     "cap_ratio_before": "", "filter_drops": "yes", "decision": "",
                     "note": ""})

    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(COLUMNS) + "\n")
        for r in rows:
            fh.write("\t".join(str(r[c]) for c in COLUMNS) + "\n")

    decided = sum(1 for r in rows if r["decision"])
    print(f"{len(rows)} rows -> {out} ({decided} decisions kept, {len(new)} new rows)")
    for a in sorted(new, key=lambda a: (-int(a["count"]), a["lemma"])):
        print(f"  NEW  {a['lemma']:16} {int(a['count']):>9,}  cap_ratio {a['cap_ratio']}")


if __name__ == "__main__":
    main()
