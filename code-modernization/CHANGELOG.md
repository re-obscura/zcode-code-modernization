# Changelog

Each release gets a new number in the plugin manifest; the harness only offers an update when that number changes.

## 1.1.0 (ZCode port)

Adapted from upstream 1.0.0 for ZCode (Apache-2.0, upstream by Anthropic). Same commands, same agents, same proof machinery; the harness-specific parts were rewritten on ZCode's documented APIs, and nothing was dropped without a working replacement.

- **Manifest and commands.** `.zcode-plugin/plugin.json` with `commands`, `agents` and `hooks`; commands take their arguments as one `$ARGUMENTS` string and define how to split it (ZCode has no named-argument frontmatter).
- **Fan-outs on the Agent tool.** The upstream Workflow-tool scripts cannot run on ZCode, so the five fan-outs (extract-rules, harden, uplift deltas, uplift migrate, reimagine scaffold, portfolio assess) are re-specified in the commands as Agent-tool pipelines with the same phases, caps and result contracts, each resumable through a journal directory under `analysis/<system>/`. The upstream scripts stay in `workflows/` as the normative reference (see `workflows/README.md`).
- **X-ray reads, for real.** A `PostToolUse` hook on `Read` (`hooks/zcode/hook.py`, a Python port of the upstream x-ray) attaches what the analysis knows about a legacy file as context only the model sees. Controlled by the plugin's **X-ray reads** option.
- **Source guard.** A `PreToolUse` hook denies writes aimed under `legacy/` (symlink targets included) — the ZCode replacement for the hand-added deny rule upstream suggests. **Source guard** option: `auto` (default, engages where the plugin works), `on`, `off`.
- **Status dashboard instead of the live pane.** ZCode has no transcript-side pane, so the pane's information lives in `analysis/<system>/PANE.html` (auto-refreshing, built by `scripts/build_pane.py` from the same disk artifacts) and the pane's three commands are now real commands: `modernize-panel` (build, show, `json`), `modernize-review-pane` (the rule deck, one pop-up per card, same files as `modernize-review`) and `modernize-sign` (fills the brief's approval block). The upstream pane source is kept under `hooks/` for reference.
- **Telemetry on ZCode's seven events.** Same whole-numbers-only counts, wired to `UserPromptSubmit`, `Stop`, `SessionStart` and `PostToolUseFailure`; ZCode has no `StopFailure`, so model-error counts (`api`) are dormant here. Reads the version from `.zcode-plugin/plugin.json`, honors `ZCODE_PLUGIN_DATA` / `ZCODE_PLUGIN_OPTION_*` alongside the upstream variable names, and knows the ZCode permission modes.
- **Agents.** Frontmatter `tools` converted to ZCode's tool set (`Glob`/`Grep` do not exist there; search goes through Bash). The reimagine handoff file is `AGENTS.md` (what ZCode reads) instead of `CLAUDE.md`.
- **Python 3.8+ only dependency unchanged:** `python3` (or `python` / `py -3`) for the map render, shard builder, proof scripts, report, dashboard and telemetry; `scc`/`cloc` optional; a build toolchain for your stack optional but it enables the strongest proof.

## 1.0.0

- **A front door.** `/code-modernization:modernize` asks what you want done (once), records it in `analysis/<system>/INTENT.md`, shows the road and gives the exact first command. `--source <path>` links the code so nothing has to be copied.
- **Same-stack version moves.** `modernize-uplift` catalogs what changes between two versions of the same technology, records a measured baseline, migrates one pilot unit and then the rest by playbook.
- **Independent proof.** `modernize-verify` re-runs the tests from clean, re-runs your own canary, tries inputs nobody used and gives each module one verdict, PROVEN, PARTLY PROVEN or NOT PROVEN, computed by a script from files it parses itself.
- **People decide what only they can.** `modernize-review` records a person's verdict on each flagged rule; the plan, the build and the tests read it. A difference the proof finds is accepted once per input by a person, never by the tool.
- **Comparison that fits real output.** Floating-point output can be compared within a declared, justified tolerance; masks and approvals are listed in the result.
- **Proportional rule extraction.** The same rule found in several files is folded into one, and the number of rules follows the size of the code.
- **A one-page report** (`REPORT.html`, works offline) with the proof, the rules, the map and a next step you can copy.
- **A live progress pane** (early access, terminal): the estate map, the rule review deck, the sign-off dialog and the proof at a glance.
- **Usage counts** (whole numbers only, off by switch): which commands run, how far a system gets, what the plugin runs on (operating system, python status, path problems on Windows), and which kinds of failure happen (python missing, blocked by a permission rule, model errors, the plugin's own script errors). Once per version and machine at session start it also says what it runs on. See the Telemetry section of the README.
