---
description: Fill in the brief's approval block — who approves, when, and whether it covers Phase 1 only or the full plan
argument-hint: <system> [name, role]
---

Arguments arrive in `$ARGUMENTS` as one string: `$system` is the first token; the remainder, when given,
is `name, role` (the approver's name and role, comma separated).

Fill in the approval block of `analysis/$system/MODERNIZATION_BRIEF.md`: who, when, and whether the
approval covers Phase 1 or the full plan. It changes nothing else in the file. Upstream this was the
pane's sign-off dialog; on ZCode it is this command (and the dashboard's Next line points here while
the brief is unsigned).

## Steps

1. If `analysis/$system/MODERNIZATION_BRIEF.md` does not exist, stop and say so; the brief comes from
   `/code-modernization:modernize-brief $system`.
2. Read the file and find its **Approval Block** (the fenced block with `Approved by:`, `Date:` and
   `Approval covers:`). If the brief has no approval block, stop and say the brief predates this
   plugin's format; regenerating the brief adds it.
3. If the block is already signed (`Approved by:` carries a name), ask before replacing: one pop-up
   (AskUserQuestion) — replace the signature, or leave it. Never change anything else in the file
   either way.
4. Collect what is missing with **one** pop-up: the approver's **name** and **role** (when not in
   `$ARGUMENTS`), and the **coverage** — *Phase 1 only* or *Full plan*. The person can type any other
   coverage wording; keep it verbatim. In a headless run, do not invent a signature: stop and say the
   block waits for a person.
5. Write the block in place, exactly this shape:

   ```
   Approved by: <name>, <role>  Date: <YYYY-MM-DD>
   Approval covers: Phase 1 only | Full plan
   ```

   (today's date; the coverage as chosen). Re-write only the lines of the block; byte-for-byte keep
   everything before and after it.
6. Refresh the report (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py" $system`) and the
   dashboard (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_pane.py" $system .`; both one-line
   conveniences: if they fail, say so and carry on). Confirm in two lines what was signed and what the
   signed approval now authorizes: the build commands read the brief and treat the approval block and
   the edited criteria as binding. The next command is the brief's Phase 1 command.
