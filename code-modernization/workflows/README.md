# Workflows — reference implementations

These JavaScript files are the plugin's **Workflow-tool scripts** as upstream wrote them for Claude
Code: scripted multi-agent jobs (fan-outs with journals, adversarial verification, circuit breakers)
that a Claude Code session runs with its `Workflow` tool. ZCode has no `Workflow` tool, so the ZCode
plugin does **not** execute them.

They are kept because they are the exact specification the ZCode commands implement with the `Agent`
tool:

| Script | ZCode equivalent |
| --- | --- |
| `extract-rules.js` | `modernize-extract-rules` Method A (shards in batches, per-rule referees, consolidation, the P0 two-judge panel, the DTO catalog, the journal under `analysis/<system>/extract-rules-journal/`) |
| `harden-scan.js` | `modernize-harden` Scan (five class finders, a refuter per finding, double-judged Critical/High, the journal under `analysis/<system>/harden-journal/`) |
| `uplift-deltas.js` | `modernize-uplift` Step 3 (one finder per delta category, verified per delta, the journal under `analysis/<system>/delta-journal/`) |
| `uplift-migrate.js` | `modernize-uplift` Step 5b (one agent per unit, dependency-ordered batches, the circuit breaker, the journal under `analysis/<system>/uplift-journal/`) |
| `reimagine-scaffold.js` | `modernize-reimagine` Phase E (one scaffolder per service, batches of 3, the journal under `analysis/<system>/scaffold-journal/`) |
| `portfolio-assess.js` | `modernize-assess --portfolio` (one survey agent per system, rows journaled to `analysis/portfolio-rows.json`) |

When a command and a script disagree, the script wins: fix the command. The return shapes documented in
the scripts (for example `rules_result.json` with its `stats` block) are contracts — `render_rules.py`
and the telemetry read them.
