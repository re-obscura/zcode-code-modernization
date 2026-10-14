---
description: Show the status dashboard for a system — the map, the steps, the verdicts, and what to run next
argument-hint: [system] [open|close|json]
---

Arguments arrive in `$ARGUMENTS` as one string: the first token may be a system name or a mode
(`open` | `close` | `json`); if two tokens are given, the first is the system and the second the mode.
With nothing, follow the plugin's **System** option (else the newest under `analysis/`, else under
`legacy/`), and mode `open`.

ZCode has no transcript-side pane (that was Claude Code's early-access function hooks, which this port
does not use), so this command draws the same picture as a self-contained page,
`analysis/<system>/PANE.html`, which reloads itself every 20 seconds while its window stays open: the
map of the code with each module's state, the steps done, the phases of the plan, each verdict the
proof wrote, what needs attention, and the one command to run next. Everything on it is read from the
files the commands wrote — nothing is guessed, and a fact not on disk shows as missing.

## What to do

1. **`off` short-circuit.** If the plugin's **Status dashboard** option is `off`, say in one line that
   the dashboard is switched off in Plugin settings and stop (a `json` request still answers).
2. **Find the system.** The named one, else the option, else the newest under `analysis/`, else the
   newest under `legacy/` (letters, digits, `-`, `_`). With no system at all, say the one command to
   start with — `/code-modernization:modernize <name> --source <path>` — and stop.
3. **Build and show.** Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_pane.py" <system> . 
   ```

   (on Windows `python` or `py -3` wherever a command says `python3`). It prints the one-row status
   bar — system and track, the steps done, the next command, up to three attention items — and writes
   `analysis/<system>/PANE.html`. Show the bar in your reply verbatim, then open the page for the
   person (`start "" "<path>"` on Windows, `open "<path>"` on macOS, `xdg-open "<path>"` on Linux) when
   the mode is `open` or empty and the option is not `command`... unless running headlessly, where you
   only print the path.
4. **`json`** — run the same script with `--json` and print its output: the exact reading the dashboard
   draws from, for scripting and diffing.
5. **`close`** — there is nothing to close on this side: say the dashboard lives in its browser tab and
   the tab can be closed; nothing keeps running behind it.

If `python3` is missing or the script fails, say so in one line and fall back to what this command can
do without it: read `analysis/<system>/REPORT.html`'s existence and give `/code-modernization:modernize-status <system>` as the fuller alternative.

A stale page is never wrong for long: the page reloads itself, and every command ends by offering this
one when something changed. Re-run this command any time to refresh immediately and get a fresh bar.
