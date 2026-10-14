---
description: Review the flagged business rule cards one at a time — the review deck, writing the same verdicts as modernize-review
argument-hint: <system> [flagged|p0|all] [filter]
---

Arguments arrive in `$ARGUMENTS` as one string: `$system` is the first token; the optional second is
`$scope` (`flagged` | `p0` | `all`); the optional remainder is `$filter` (matches an id, a domain, a
title or a cited file).

This is the review **deck**: the rule cards one at a time, each with its citation and its question,
until the person stops. It writes the same two files as
`/code-modernization:modernize-review` (`RULE_REVIEWS.json` and `RULE_REVIEWS.md`) and never edits
`BUSINESS_RULES.md`. Upstream this deck lived in the transcript-side pane; on ZCode it runs on the
AskUserQuestion tool, one pop-up per rule.

## 1 — Choose the cards

Read `analysis/$system/BUSINESS_RULES.md` (each card has `### RULE-NNN`, Priority, Confidence, and
sometimes a suspected defect or an SME question) and, if it exists, `analysis/$system/RULE_REVIEWS.json`;
rules already decided are skipped, and you say how many. `$scope` picks the rest:

- **flagged** (the default): P0 rules that have a suspected defect, an SME question or less than High
  confidence, plus any rule the brief's open questions name.
- **p0**: every P0 rule. **all**: every rule.

`$filter` keeps only cards whose id, category, title or cited path matches it (case-insensitive
substring). Say how many cards will be asked (about a minute per ten). If none is left, say so and give
the next command.

## 2 — Deal the cards

One AskUserQuestion call per rule, in priority order (P0 first, suspected defects first):

- **Question:** the rule's id as the header; the title, the plain-English statement, its
  Given/When/Then in one line, and the suspected defect or SME question if it has one, as the question
  text.
- **Options (four):**
  1. **Right** — the rule is correct and wanted (verdict `confirmed`).
  2. **Wrong, or not wanted** — it misdescribes the code, or the code does this today but should not
     (verdict `wrong`).
  3. **Not sure** — needs a discussion (verdict `discuss`).
  4. **Show the cited lines first** — read the cited range from `legacy/$system/<path>` (up to about
     15 lines, plus two of context either side), put them in your next message, and ask the same three
     verdict options again for this rule.
- The person can always type instead: their note becomes the verdict's `note`, in their words. Verdicts
  already typed in the request (`RULE-004 wrong: it truncates on purpose`) are recorded as given, with
  no pop-up for those rules. Stop when they say to. Without the tool and without typed verdicts (a
  headless run) do not guess: leave every rule unreviewed and say so.

## 3 — Record

Re-read `analysis/$system/RULE_REVIEWS.json` first (what `/code-modernization:modernize-review` or an
earlier deck recorded meanwhile is not lost), then merge:

```json
{ "system": "<name>", "version": 1, "reviews": {
    "RULE-004": { "verdict": "confirmed", "at": "<ISO time>", "title": "<the rule's title>", "note": "<their words, optional>" } } }
```

`verdict` is `confirmed`, `wrong` or `discuss`. Change an earlier entry only when a new answer replaces
it. Write `analysis/$system/RULE_REVIEWS.md` from it: a short paragraph, then a table
`Rule | Verdict | When | Title | Note`, sorted by rule number. Refresh the report
(`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py" $system`; a convenience: if it fails or
`python3` is missing, say so in one line and carry on), and refresh the dashboard the same way with
`build_pane.py` when the **Status dashboard** option is not `off`.

## 4 — What happens next

Tell the person, in three lines: rules marked wrong or needing discussion are not settled; `brief`
lists them as open questions and never builds a Behavior Contract on them; `transform` and `reimagine`
will not pin a wrong rule as the oracle and stop on a P0 rule still under discussion. Then the next
command: `/code-modernization:modernize-brief $system` (run it again if the brief exists and any rule
changed), or the brief's next build command when the plan is already approved.
