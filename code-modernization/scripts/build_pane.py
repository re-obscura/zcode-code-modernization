#!/usr/bin/env python3
"""The status dashboard behind /code-modernization:modernize-panel - the ZCode replacement for the
upstream live pane (which needs Claude Code's early-access function hooks). It reads the same files
the pane read, draws the same picture, and refreshes itself.

    build_pane.py <system> [workspace] [--json] [--out <file>]

Everything is read from analysis/<system>/ and modernized/<system>*/ plus topology.json; nothing is
guessed by a model, and a fact that is not on disk is shown as missing. The output is a self-contained
page (PANE.html beside REPORT.html) that reloads itself every 20 seconds, so a window left open follows
the work; --json prints the same data as JSON (what /modernize-panel json shows). Exit 1 when the
system has no artifacts yet. It never raises on bad artifacts: what cannot be read is reported missing.
"""
import base64
import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_report as br  # noqa: E402

REFRESH_SECONDS = 20

# Tile colours: the pane's mid-tones, readable on a light or a dark terminal page.
STATE_STYLE = {
    "proven": ("#2ea043", "proven"),
    "partly": ("#d29922", "partly proven"),
    "not": ("#f85149", "NOT proven"),
    "built": ("#58a6ff", "built, not verified yet"),
    "changed": ("#db6d28", "changed since verified"),
    "none": ("#6e7681", "not built"),
}


def one_line(value, limit=200):
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()[:limit]


def load_json(src, path, label):
    data, _ = src.json(path, label)
    return data


def verification_modules(src):
    """Per-module verdicts from VERIFICATION.json, in the order the pack wrote them."""
    ver = load_json(src, os.path.join(src.adir, "VERIFICATION.json"), "VERIFICATION.json")
    view = br.proof_view(ver) if ver else None
    if not view:
        return None, [], {}
    modules = {}
    for m in view.get("modules") or []:
        name = one_line(m.get("name"), 120)
        verdict = one_line(m.get("verdict"), 20)
        modules[name.lower()] = verdict
        modules[re.sub(r"\s+", "-", name.lower())] = verdict
    problems = [one_line(p, 220) for p in (view.get("problems") or [])[:6]]
    signoff = view.get("signoff") or {}
    return view.get("verdict"), problems, {"modules": modules, "signed": bool(str(signoff.get("name", "")).strip() and str(signoff.get("decision", "")).strip())}


def map_nodes(topo):
    """Leaf tiles: (id, name, domain, loc, file). Grouped by their domain container when there is one."""
    tiles = []

    def walk(node, domain, depth):
        if not isinstance(node, dict) or depth > 12:
            return
        children = node.get("children")
        if isinstance(children, list) and children:
            label = one_line(node.get("name"), 80)
            for child in children:
                walk(child, label, depth + 1)
            return
        loc = node.get("loc")
        tiles.append({
            "id": one_line(node.get("id"), 120),
            "name": one_line(node.get("name"), 80),
            "domain": domain or "",
            "loc": loc if isinstance(loc, int) and loc >= 0 else 0,
            "file": one_line(node.get("file"), 200),
        })

    if isinstance(topo, dict):
        walk(topo.get("root"), "", 0)
    return tiles


def module_dir(src, name):
    return os.path.join(src.mdir, src.system, name)


def tile_state(src, name, file, ver):
    """One state per tile: proven > partly > not > changed > built > not built."""
    verdict = ""
    if ver:
        for key in (one_line(name, 120).lower(), re.sub(r"\s+", "-", one_line(name, 120).lower()),
                    base_of(file).lower()):
            verdict = ver["modules"].get(key, "")
            if verdict:
                break
    stem = base_of(file) or one_line(name, 120)
    module_path = None
    for cand in (module_dir(src, stem), module_dir(src, one_line(name, 120))):
        if os.path.isdir(cand):
            module_path = cand
            break
    notes = os.path.join(module_path, "TRANSFORMATION_NOTES.md") if module_path else None
    built = bool(module_path)
    if verdict == "PROVEN":
        state = "proven"
        if built and notes and os.path.isfile(notes):
            try:
                if os.path.getmtime(notes) > os.path.getmtime(os.path.join(src.adir, "VERIFICATION.json")):
                    state = "changed"
            except OSError:
                pass
    elif verdict == "PARTLY PROVEN":
        state = "partly"
    elif verdict == "NOT PROVEN":
        state = "not"
    elif built:
        state = "built"
    else:
        state = "none"
    return state, built


def base_of(path):
    return re.sub(r".*/", "", str(path or ""))


def brief_state(src):
    brief = src.read(os.path.join(src.adir, "MODERNIZATION_BRIEF.md"), "MODERNIZATION_BRIEF.md")
    if brief is None:
        return None, [], False
    phases = []
    for m in re.finditer(r"(?ms)^#{2,4}[ \t]*Phase[ \t]+(\d+)[ \t]*[-—:][ \t]*(.*)$", brief):
        phases.append({"n": int(m.group(1)), "name": one_line(m.group(2), 80)})
        block = brief[m.end():m.end() + 800]
        for line in block.split("\n"):
            if re.match(r"(?i)^\s*Command\s*:", line):
                phases[-1]["command"] = one_line(line.split(":", 1)[1], 80)
                break
    approved = False
    for line in brief.split("\n"):
        m = re.match(r"(?i)^\s*Approved by\s*:(.*?)(?:Date\s*:.*)?$", line)
        if m:
            approved = bool(re.search(r"[A-Za-z0-9]", m.group(1)))
            break
    return phases, [], approved


def attention(src, glance, ver, problems, approved):
    """What needs a person: the pane's Attention block, from the same files."""
    items = []
    for problem in problems:
        items.append(problem)
    rules = glance.get("rules") or {}
    reviews = load_json(src, os.path.join(src.adir, "RULE_REVIEWS.json"), "RULE_REVIEWS.json")
    reviews = reviews.get("reviews") if isinstance(reviews, dict) else None
    reviews = reviews if isinstance(reviews, dict) else {}
    open_flagged = int(rules.get("defects") or 0) + int(rules.get("sme") or 0)
    if rules and open_flagged and not reviews:
        items.append("%d rule(s) are flagged for a person (a suspected defect or an SME question) and nobody has reviewed them yet: run modernize-review." % open_flagged)
    if rules and reviews:
        discuss = sum(1 for v in reviews.values() if isinstance(v, dict) and str(v.get("verdict", "")) == "discuss")
        wrong = sum(1 for v in reviews.values() if isinstance(v, dict) and str(v.get("verdict", "")) == "wrong")
        if discuss:
            items.append("%d rule(s) are still under discussion: the build stops on a P0 one until it is settled." % discuss)
        if wrong:
            items.append("%d rule(s) are marked wrong: they are not used as a test oracle." % wrong)
    if glance.get("steps") and any(s["key"] == "brief" and s["done"] for s in glance["steps"]) and not approved:
        items.append("The brief is unsigned: nothing is built until a person approves it (modernize-sign fills the block).")
    eq = glance.get("equivalence")
    if eq and eq.get("state") == "red":
        items.append(one_line(eq.get("headline"), 220))
    ver_info = glance.get("proof")
    if ver_info and ver_info.get("verdict") in ("PARTLY PROVEN", "NOT PROVEN"):
        items.append("The proof is %s: a person signs VERIFICATION.md when it is PROVEN, and decides every open difference." % ver_info["verdict"])
    return items[:8]


def collect(system, workspace):
    src = br.Source(workspace, system)
    a = lambda name: os.path.join(src.adir, name)  # noqa: E731
    reviews_raw = load_json(src, a("RULE_REVIEWS.json"), "RULE_REVIEWS.json")
    reviews = reviews_raw.get("reviews") if isinstance(reviews_raw, dict) else {}
    reviews = {k: v for k, v in reviews.items() if isinstance(v, dict)} if isinstance(reviews, dict) else {}
    glance = {"rules": None, "security": None, "baseline": None, "topology": None, "equivalence": None, "proof": None}

    rules_text = src.read(a("BUSINESS_RULES.md"), "BUSINESS_RULES.md")
    if rules_text is not None:
        cards = [b for b in br.parse_rules(rules_text) if b["k"] == "rule"]
        if cards:
            facts = br.rule_facts(rules_text, cards, reviews)
            facts["sme"] = sum(1 for c in cards if c.get("conf") not in ("", "High"))
            glance["rules"] = facts
    glance["security"] = br.security_facts(src.read(a("SECURITY_FINDINGS.md"), "SECURITY_FINDINGS.md") or "") if os.path.isfile(a("SECURITY_FINDINGS.md")) else None
    topo = load_json(src, a("topology.json"), "topology.json")
    glance["topology"] = br.topology_facts(topo)
    eq = load_json(src, a("EQUIVALENCE.json"), "EQUIVALENCE.json")
    if eq:
        view = br.equivalence_view(eq)
        glance["equivalence"] = {k: view[k] for k in ("state", "headline", "problems", "tally")} if view else {
            "state": "red", "headline": "EQUIVALENCE.json could not be used, so equivalence is not proven.", "problems": [], "tally": None}

    verdict, problems, ver = verification_modules(src)
    if verdict:
        glance["proof"] = {"verdict": verdict, "counts": {}, "modules": [], "problems": problems}

    phases, _, approved = brief_state(src)

    mods = [os.path.join(src.mdir, system + s) for s in ("", "-uplifted", "-reimagined")]
    done = {"preflight": os.path.isfile(a("PREFLIGHT.md")), "assess": os.path.isfile(a("ASSESSMENT.md")),
            "map": topo is not None, "rules": rules_text is not None,
            "brief": os.path.isfile(a("MODERNIZATION_BRIEF.md")),
            "build": any(br.nonempty_dir(p) for p in mods), "harden": os.path.isfile(a("SECURITY_FINDINGS.md"))}
    glance["steps"] = [{"key": k, "label": label, "done": bool(done[k])} for k, label in br.STEPS]
    glance["next"] = br.next_step(system, done, glance)
    tracks = {"rewrite": [mods[0]], "same-stack uplift": [a("DELTA_CATALOG.md"), a("PLAYBOOK.md"), mods[1]],
              "reimagine": [a("AI_NATIVE_SPEC.md"), a("REIMAGINED_ARCHITECTURE.md"), mods[2]]}
    ranked = sorted(((br.newest(p), k) for k, p in tracks.items() if br.newest(p)), reverse=True)
    glance["track"] = {"label": ranked[0][1],
                       "why": "newest artifact: " + os.path.relpath(ranked[0][0][1], workspace).replace(os.sep, "/")} if ranked else None

    tiles = map_nodes(topo)
    for tile in tiles:
        state, built = tile_state(src, tile["name"], tile["file"], ver if ver else None)
        tile["state"] = state
        tile["built"] = built
    if not tiles and done["build"]:
        folders = []
        for p in mods:
            if br.nonempty_dir(p):
                try:
                    folders += [e.name for e in os.scandir(p) if e.is_dir(follow_symlinks=False)]
                except OSError:
                    pass
        tiles = [{"id": f, "name": f, "domain": "", "loc": 0, "file": "", "state": "built", "built": True} for f in folders[:200]]
        for tile in tiles:
            if ver:
                verdict_name = ver["modules"].get(tile["name"].lower(), "")
                tile["state"] = {"PROVEN": "proven", "PARTLY PROVEN": "partly", "NOT PROVEN": "not"}.get(verdict_name, "built")

    uplift_units = []
    uplifted = os.path.join(src.mdir, system + "-uplifted")
    if br.nonempty_dir(uplifted):
        baseline = src.read(a("BASELINE.md"), "BASELINE.md") or ""
        units = []
        try:
            units = [e.name for e in os.scandir(uplifted) if e.is_dir(follow_symlinks=False)][:200]
        except OSError:
            pass
        uplift_units = [{"name": u, "baseline": u.lower() in baseline.lower(),
                         "state": ("proven" if verdict == "PROVEN" else "built") if br.nonempty_dir(os.path.join(uplifted, u)) else "none"}
                        for u in units]

    data = {"v": 1, "kind": "pane", "system": system[:200], "workspace": os.path.basename(workspace) or workspace,
            "generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "refresh": REFRESH_SECONDS, "glance": glance, "phases": phases, "briefApproved": approved,
            "map": tiles, "upliftUnits": uplift_units,
            "attention": attention(src, glance, verdict, problems, approved),
            "notes": list(src.notes)}
    if not src.found and not tiles and not data["upliftUnits"]:
        return None
    return data


STYLE = {
    "proven": "#2ea043", "partly": "#d29922", "not": "#f85149",
    "built": "#58a6ff", "changed": "#db6d28", "none": "#6e7681",
}


def esc(text):
    return (str(text if text is not None else "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_html(data):
    g = data["glance"]
    steps = " ".join('<span class="step%s">%s</span>' % (" on" if s["done"] else "", esc(s["label"])) for s in g["steps"])
    track = ('<span class="track">%s</span>' % esc(g["track"]["label"])) if g.get("track") else ""
    banner = ""
    proof = g.get("proof")
    if proof:
        cls = {"PROVEN": "ok", "PARTLY PROVEN": "warn"}.get(proof["verdict"], "bad")
        banner = '<div class="banner %s">Proof: %s</div>' % (cls, esc(proof["verdict"]))
    elif g["steps"][-1]["done"]:
        banner = '<div class="banner ok">Steps complete</div>'
    nxt = g.get("next") or {}
    next_html = ""
    if nxt.get("command"):
        next_html = ('<div class="next">Next: <code>%s</code><span class="why">%s</span></div>'
                     % (esc(nxt["command"]), esc(nxt.get("why", ""))))
    tiles_by_domain = {}
    for tile in data["map"]:
        tiles_by_domain.setdefault(tile["domain"] or "Modules", []).append(tile)
    groups = []
    for domain in sorted(tiles_by_domain):
        chips = "".join(
            '<span class="tile" style="background:%s" title="%s%s">%s</span>'
            % (STYLE.get(t["state"], STYLE["none"]), esc(t["name"]), (" · %d lines" % t["loc"]) if t["loc"] else "",
               esc(t["name"][:2].upper() or "·"))
            for t in tiles_by_domain[domain])
        groups.append('<div class="domain"><div class="dname">%s</div><div class="tiles">%s</div></div>' % (esc(domain), chips))
    map_html = "".join(groups) or '<div class="muted">No map yet: modernize-map draws one, and the tiles follow the build otherwise.</div>'

    phases = ""
    if data["phases"]:
        rows = "".join('<tr><td>Phase %s</td><td>%s</td><td><code>%s</code></td></tr>'
                       % (p["n"], esc(p["name"]), esc(p.get("command", ""))) for p in data["phases"])
        phases = '<h3>Phases</h3><table>%s</table>' % rows
    modules_rows = ""
    verdicts = (g.get("proof") or {}).get("verdict")
    if data["upliftUnits"]:
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                       % (esc(u["name"]), "baseline covers it" if u["baseline"] else "-", STYLE_NAME.get(u["state"], u["state"]))
                       for u in data["upliftUnits"])
        modules_rows = '<h3>Working copy</h3><table>%s</table>' % rows
    elif verdicts:
        modules_rows = '<div class="muted">Overall proof: %s (per-module verdicts live in VERIFICATION.md)</div>' % esc(verdicts)
    attention = ""
    if data["attention"]:
        attention = '<h3>Attention</h3><ul>%s</ul>' % "".join("<li>%s</li>" % esc(i) for i in data["attention"])
    counts = []
    rules = g.get("rules")
    if rules:
        counts.append("%d rules (%d P0)" % (rules.get("total", 0), rules.get("byPriority", {}).get("P0", 0)))
    topo = g.get("topology")
    if topo:
        counts.append("%d modules, %s lines in the map" % (topo.get("modules", 0), br.num(topo.get("loc", 0))))
    sec = g.get("security") or {}
    if sec:
        counts.append("security: %s critical, %s high" % (sec.get("Critical", 0), sec.get("High", 0)))
    eq = g.get("equivalence")
    if eq:
        counts.append("equivalence: %s" % eq["state"])
    counts_html = ('<div class="counts">%s</div>' % " · ".join(esc(c) for c in counts)) if counts else ""
    notes = ""
    if data["notes"]:
        notes = '<div class="muted small">%s</div>' % esc(" ".join(data["notes"])[:400])

    return """<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="refresh" content="%(refresh)d">
<title>%(system)s — modernization status</title>
<style>
:root{color-scheme:dark}
body{background:#1e1e1e;color:#d4d4d4;font:14px/1.5 system-ui,sans-serif;margin:0;padding:24px}
h1{font-size:20px;margin:0 0 4px}h3{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;margin:20px 0 6px}
code{background:#2d2d2d;padding:2px 6px;border-radius:4px;color:#e8e8e8}
.banner{display:inline-block;padding:3px 10px;border-radius:4px;font-weight:600;margin:8px 0}
.ok{background:#12351c;color:#4ade80}.warn{background:#3a2e10;color:#fbbf24}.bad{background:#3c1a1a;color:#f87171}
.step{display:inline-block;padding:1px 8px;margin:2px 4px 2px 0;border:1px solid #3f3f46;border-radius:10px;font-size:12px;color:#71717a}
.step.on{border-color:#cc785c;color:#e7c8b8}
.track{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;background:#26313a;color:#93c5fd;margin-left:6px}
.next{margin:10px 0 0}.why{color:#9ca3af;margin-left:8px;font-size:13px}
.counts{color:#9ca3af;margin:8px 0}
.domain{margin:8px 0}.dname{font-size:12px;color:#9ca3af}
.tiles{display:flex;flex-wrap:wrap;gap:4px;max-width:900px}
.tile{color:#101418;font:600 10px/18px system-ui;width:26px;height:18px;text-align:center;border-radius:3px}
table{border-collapse:collapse;font-size:13px}td{border-bottom:1px solid #2d2d2d;padding:4px 14px 4px 0;vertical-align:top}
.muted{color:#71717a}.small{font-size:12px}
ul{margin:4px 0;padding-left:20px}li{margin:3px 0}
.meta{position:fixed;top:10px;right:16px;font-size:11px;color:#52525b}
</style></head><body>
<div class="meta">auto-refresh %(refresh)ds · %(generated)s</div>
<h1>%(system)s %(track)s</h1>
%(banner)s
<div>%(steps)s</div>
%(counts)s
%(next_html)s
<h3>Map</h3>
%(map_html)s
%(phases)s
%(modules_rows)s
%(attention)s
%(notes)s
</body></html>""" % {
        "refresh": data["refresh"], "generated": esc(data["generated"]), "system": esc(data["system"]),
        "track": track, "banner": banner, "steps": steps, "counts": counts_html, "next_html": next_html,
        "map_html": map_html, "phases": phases, "modules_rows": modules_rows,
        "attention": attention, "notes": notes,
    }


STYLE_NAME = {"proven": "proven", "partly": "partly proven", "not": "NOT proven", "built": "built"}


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv
    if not args:
        print(__doc__)
        return 2
    system = args[0]
    workspace = os.path.abspath(args[1] if len(args) > 1 else os.getcwd())
    out = os.path.join(workspace, "analysis", system, "PANE.html")
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
    data = collect(system, workspace)
    if data is None:
        print("no artifacts for %s under %s yet" % (system, workspace))
        return 1
    if as_json:
        print(json.dumps(data, ensure_ascii=False))
        return 0
    try:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = "%s.%d" % (out, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(render_html(data))
        os.replace(tmp, out)
    except OSError as err:
        print("could not write %s: %s" % (out, err))
        return 1
    g = data["glance"]
    done = " ".join(s["label"] for s in g["steps"] if s["done"]) or "nothing yet"
    nxt = (g.get("next") or {}).get("command", "")
    print("%s · %s" % (data["system"], g["track"]["label"] if g.get("track") else "no track yet"))
    print("Steps done: %s" % done)
    print("Next: %s" % nxt)
    for item in data["attention"][:3]:
        print("! %s" % item)
    print("Dashboard: %s (refreshes itself every %ds while the window is open)" % (out, data["refresh"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
