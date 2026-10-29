#!/usr/bin/env python3
"""Nomology platform specs: convert, check and sync.

The specs live in this repo as Markdown (specs/<AREA>/<ID>.md) and are mirrored in the
Platform Spec Workspace (a claude.ai artifact). This tool moves content between the two
and checks the repo for broken links and template mismatches.

Commands
  check                     Validate every spec (links, parents, template sections, citations).
  index                     Regenerate specs/README.md, meta/open-questions.md and templates/*.md.
  import <export.json>      Bring a workspace export into the repo (workspace -> repo).
  export [-o FILE]          Build the import file for the workspace (repo -> workspace).

Standard library only (Python 3.9+). Run from the repo root:  python3 tools/specs.py check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
TEMPLATES = ROOT / "templates"
META = ROOT / "meta"
FORMAT = "nomology-spec-workspace/1"

# Front-matter fields, in the order they are written. Values are JSON (which is also valid YAML).
FM_FIELDS = ["id", "title", "parent", "order", "type", "template", "childTemplate", "status",
             "owner", "indicative", "summary", "links", "rev", "syncHash",
             "createdAt", "updatedAt", "updatedBy"]
# Fields that make up a spec's content (used for change detection in both directions).
CONTENT_FIELDS = ["title", "parent", "order", "type", "template", "childTemplate", "status",
                  "owner", "indicative", "summary", "links", "spec", "checks", "citations"]

SEC_RE = re.compile(r"^<!-- (section|check):([A-Za-z0-9_\-]+) -->\s*$")
BLOCK_RE = re.compile(r"^<!-- (checks|citations|end) -->\s*$")
LINK_RE = re.compile(r"\[\[([A-Za-z0-9\-]+)(?:#([A-Za-z0-9_\-]+))?\]\]")
CITE_RE = re.compile(r"\[(R\d+)\]")


# ---------------------------------------------------------------- helpers

def die(msg: str) -> None:
    print("error: " + msg, file=sys.stderr)
    sys.exit(1)


def canon(v) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def norm(s: str) -> str:
    # Leading blank lines and trailing whitespace are not content.
    return s.lstrip("\n").rstrip()


def content_of(node: dict) -> dict:
    out = {}
    for f in CONTENT_FIELDS:
        v = node.get(f)
        if f in ("spec", "checks"):
            v = {k: norm(s) for k, s in (v or {}).items() if isinstance(s, str) and s.strip()}
        if f in ("links", "citations"):
            v = v or []
        if f == "indicative":
            v = bool(v)
        if f in ("childTemplate", "owner", "template", "parent") and not v:
            v = None
        out[f] = v
    return out


def content_hash(node: dict) -> str:
    return hashlib.sha256(canon(content_of(node)).encode()).hexdigest()[:16]


def load_templates() -> dict:
    t = {}
    for p in sorted(TEMPLATES.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        t[d["id"]] = d
    return t


def area_of(key: str, nodes: dict) -> str:
    seen = set()
    k = key
    while nodes.get(k, {}).get("parent") and k not in seen:
        seen.add(k)
        k = nodes[k]["parent"]
    return k


def children_map(nodes: dict) -> dict:
    kids: dict = {}
    for k, n in nodes.items():
        kids.setdefault(n.get("parent"), []).append(k)
    for v in kids.values():
        v.sort(key=lambda k: (nodes[k].get("order") or 0, k))
    return kids


def numbering(nodes: dict) -> dict:
    kids, num = children_map(nodes), {}

    def walk(p, pre):
        for i, k in enumerate(kids.get(p, []), 1):
            num[k] = f"{pre}{i}"
            walk(k, num[k] + ".")
    walk(None, "")
    return num


def tpl_id_of(n: dict, nodes: dict, templates: dict) -> str | None:
    """Same rule as the workspace page: own template, else parent's childTemplate, else parent template's child."""
    if n.get("template"):
        return n["template"]
    p = nodes.get(n.get("parent") or "")
    if p:
        if p.get("childTemplate"):
            return p["childTemplate"]
        pt = templates.get(tpl_id_of(p, nodes, templates) or "")
        if pt and pt.get("child"):
            return pt["child"]
    return "area" if n.get("type") == "area" else "requirement"


# ---------------------------------------------------------------- Markdown <-> node

def node_to_md(n: dict, nodes: dict, templates: dict, num: dict) -> str:
    tid = tpl_id_of(n, nodes, templates)
    tpl = templates.get(tid or "", {})
    labels = {s["id"]: s.get("label", s["id"]) for s in tpl.get("sections", [])}
    clabels = {c["id"]: c.get("label", c["id"]) for c in tpl.get("checks", [])}
    order = [s["id"] for s in tpl.get("sections", [])]
    corder = [c["id"] for c in tpl.get("checks", [])]

    fm = ["---"]
    meta = dict(n)
    meta["id"] = n["key"]
    meta["syncHash"] = content_hash(n)
    for f in FM_FIELDS:
        if f in ("childTemplate",) and not meta.get(f):
            continue
        fm.append(f"{f}: {json.dumps(meta.get(f), ensure_ascii=False)}")
    fm.append("---")

    out = ["\n".join(fm), "",
           f"# {num.get(n['key'], '')} {n.get('title', '')}".rstrip(), "",
           "<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->", ""]
    if n.get("summary"):
        out += ["> " + n["summary"].replace("\n", " "), ""]

    spec = {k: v for k, v in (n.get("spec") or {}).items() if isinstance(v, str) and v.strip()}
    for sid in [s for s in order if s in spec] + sorted(s for s in spec if s not in order):
        out += [f"<!-- section:{sid} -->", f"## {labels.get(sid, sid)}", "", norm(spec[sid]), ""]

    checks = {k: v for k, v in (n.get("checks") or {}).items() if isinstance(v, str) and v.strip()}
    if checks:
        out += ["<!-- checks -->", "## Template checks", ""]
        for cid in [c for c in corder if c in checks] + sorted(c for c in checks if c not in corder):
            out += [f"<!-- check:{cid} -->", f"### {clabels.get(cid, cid)}", "", norm(checks[cid]), ""]

    if n.get("citations"):
        out += ["<!-- citations -->", "## Citations", "", "```json",
                json.dumps(n["citations"], indent=2, ensure_ascii=False), "```", ""]
    out += ["<!-- end -->", ""]
    return "\n".join(out)


def _strip_chunk(lines: list, heading_level: str) -> str:
    # drop leading blank lines and the generated heading, trailing whitespace
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith(heading_level + " "):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines).rstrip()


def parse_fm_value(raw: str):
    raw = raw.strip()
    if raw == "":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if raw in ("~", "null"):
            return None
        if raw in ("true", "false"):
            return raw == "true"
        return raw.strip("'\"")


def md_to_node(text: str, path: Path) -> dict:
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing front matter")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError(f"{path}: unterminated front matter")
    node: dict = {}
    for line in text[3:end].strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}: bad front matter line: {line!r}")
        k, v = line.split(":", 1)
        node[k.strip()] = parse_fm_value(v)
    body = text[end + 4:].splitlines()
    spec, checks, citations = {}, {}, []
    cur_kind, cur_id, buf = None, None, []

    def flush():
        nonlocal citations
        if cur_kind == "section":
            v = _strip_chunk(buf[:], "##")
            if v:
                spec[cur_id] = v
        elif cur_kind == "check":
            v = _strip_chunk(buf[:], "###")
            if v:
                checks[cur_id] = v
        elif cur_kind == "citations":
            raw = "\n".join(buf)
            m = re.search(r"```json\s*\n(.*?)\n```", raw, re.S)
            if m:
                citations = json.loads(m.group(1))
    for line in body:
        m = SEC_RE.match(line)
        b = BLOCK_RE.match(line)
        if m or b:
            flush()
            buf = []
            if m:
                cur_kind, cur_id = m.group(1), m.group(2)
            else:
                cur_kind, cur_id = (b.group(1), None)
                if cur_kind in ("checks", "end"):
                    cur_kind = None
            continue
        if cur_kind:
            buf.append(line)
    flush()
    node["key"] = node.pop("id", None) or path.stem
    node["spec"], node["checks"], node["citations"] = spec, checks, citations
    if not citations:
        node.pop("citations")
    return node


def read_repo() -> dict:
    nodes = {}
    for p in sorted(SPECS.rglob("*.md")):
        if p.name == "README.md" or p.name.endswith(".workspace.md"):
            continue
        n = md_to_node(p.read_text(encoding="utf-8"), p)
        if n["key"] in nodes:
            die(f"duplicate spec id {n['key']} in {p}")
        n["_path"] = str(p.relative_to(ROOT))
        nodes[n["key"]] = n
    return nodes


def spec_path(key: str, nodes: dict) -> Path:
    return SPECS / area_of(key, nodes) / f"{key}.md"


# ---------------------------------------------------------------- generated files

def write_index(nodes: dict, templates: dict, meta: dict) -> None:
    num, kids = numbering(nodes), children_map(nodes)
    lines = [f"# {meta.get('title') or 'Platform specifications'}", "",
             "Generated by `python3 tools/specs.py index`. Do not edit by hand.", ""]
    if meta.get("note"):
        lines += [meta["note"], ""]
    counts: dict = {}
    for n in nodes.values():
        counts[n.get("status") or "outline"] = counts.get(n.get("status") or "outline", 0) + 1
    lines += [f"**{len(nodes)} specs**: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())), "",
              "Number · ID · template · status · title", ""]

    def walk(p, d):
        for k in kids.get(p, []):
            n = nodes[k]
            rel = spec_path(k, nodes).relative_to(SPECS).as_posix()
            lines.append(f"{'  ' * d}- {num[k]} [`{k}`]({rel}) · {tpl_id_of(n, nodes, templates)} · "
                         f"{n.get('status') or 'outline'} · {n.get('title', '')}")
            walk(k, d + 1)
    walk(None, 0)
    (SPECS / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    q = ["# Open questions and assumptions", "",
         "Generated from every spec's *Open questions* section by `python3 tools/specs.py index`. "
         "Answer them in the spec itself, then regenerate.", ""]
    total = 0
    for area in kids.get(None, []):
        block = []
        stack = [area]
        order = []
        while stack:
            k = stack.pop(0)
            order.append(k)
            stack = kids.get(k, []) + stack
        for k in order:
            text = (nodes[k].get("spec") or {}).get("questions", "")
            items = [l.strip() for l in text.splitlines() if l.strip().startswith("- [ ]")]
            if items:
                rel = "../specs/" + spec_path(k, nodes).relative_to(SPECS).as_posix()
                block += [f"### {num[k]} [{nodes[k]['title']}]({rel})", ""] + items + [""]
                total += len(items)
        if block:
            q += [f"## {num[area]} {nodes[area]['title']}", ""] + block
    q.insert(4, f"**{total} open items.**\n")
    (META / "open-questions.md").write_text("\n".join(q) + "\n", encoding="utf-8")

    tl = ["# Spec templates", "", "Each spec uses one template (front matter `template`, or inherited from its parent). "
          "The JSON files are the source; the Markdown files are generated for reading.", "",
          "| Template | Name | Used for |", "|---|---|---|"]
    for tid, t in sorted(templates.items(), key=lambda x: (x[1].get("order", 99), x[0])):
        tl.append(f"| [`{tid}`]({tid}.md) | {t.get('name', tid)} | {(t.get('useFor') or '').replace('|', '/')} |")
        md = [f"# Template: {t.get('name', tid)} (`{tid}`)", "", "Generated from `" + tid + ".json`. Edit the JSON, then run `python3 tools/specs.py index`.", "",
              f"**Purpose:** {t.get('purpose', '')}", "", f"**Depth:** {t.get('depth', '')}", "",
              f"**Default child template:** `{t.get('child')}`" if t.get("child") else "", "", "## Sections", "",
              "Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.", ""]
        for s in t.get("sections", []):
            md += [f"### `{s['id']}` {s.get('label', '')} (level {s.get('level')})", "", s.get("guide", ""), ""]
            if s.get("example"):
                md += ["Illustrative example (not a requirement):", "", "> " + s["example"].replace("\n", "\n> "), ""]
        md += ["## Checks", ""]
        for c in t.get("checks", []):
            md += [f"### `{c['id']}` {c.get('label', '')}", "", f"**Question:** {c.get('question', '')}", ""]
            md += [f"- {p}" for p in c.get("probes", [])] + [""]
            md += [f"**Good answer:** {c.get('goodAnswer', '')}", ""]
            if c.get("redFlags"):
                md += ["**Red flags:**", ""] + [f"- {r}" for r in c["redFlags"]] + [""]
        (TEMPLATES / f"{tid}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (TEMPLATES / "README.md").write_text("\n".join(tl) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- commands

def cmd_check(_args) -> int:
    templates = load_templates()
    nodes = read_repo()
    problems = []
    for k, n in nodes.items():
        p = n["_path"]
        if Path(p).stem != k:
            problems.append(f"{p}: file name does not match id {k}")
        if n.get("parent") and n["parent"] not in nodes:
            problems.append(f"{p}: parent {n['parent']} does not exist")
        tid = tpl_id_of(n, nodes, templates)
        t = templates.get(tid or "")
        if not t:
            problems.append(f"{p}: unknown template {tid}")
            continue
        sids = {s["id"] for s in t.get("sections", [])}
        cids = {c["id"] for c in t.get("checks", [])}
        for s in n.get("spec", {}):
            if s not in sids:
                problems.append(f"{p}: section '{s}' is not in template {tid}")
        for c in n.get("checks", {}):
            if c not in cids:
                problems.append(f"{p}: check '{c}' is not in template {tid}")
        text = json.dumps(n.get("spec", {})) + json.dumps(n.get("checks", {}))
        for ref, part in LINK_RE.findall(text):
            if ref not in nodes:
                problems.append(f"{p}: link [[{ref}]] points to a spec that does not exist")
        cited = set(CITE_RE.findall(text))
        have = {c.get("id") for c in n.get("citations", []) or []}
        for r in sorted(cited - have):
            problems.append(f"{p}: [{r}] has no citation entry")
        for l in n.get("links") or []:
            if l.get("to") not in nodes:
                problems.append(f"{p}: typed link to {l.get('to')} does not exist")
        if n.get("status") == "approved" and n.get("syncHash") and n["syncHash"] != content_hash(n):
            problems.append(f"{p}: approved spec changed since last sync; approved specs are superseded, not edited (raise a new record)")
    # cycle check
    for k in nodes:
        seen, x = set(), k
        while x and x in nodes:
            if x in seen:
                problems.append(f"{nodes[k]['_path']}: parent chain loops")
                break
            seen.add(x)
            x = nodes[x].get("parent")
    for pr in problems:
        print(pr)
    print(f"{len(nodes)} specs checked, {len(problems)} problem(s).")
    return 1 if problems else 0


def cmd_index(_args) -> int:
    templates = load_templates()
    nodes = read_repo()
    meta = json.loads((META / "blueprint.json").read_text(encoding="utf-8")) if (META / "blueprint.json").exists() else {}
    write_index(nodes, templates, meta)
    print("Regenerated specs/README.md, meta/open-questions.md and templates/*.md")
    return 0


def cmd_import(args) -> int:
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if data.get("format") != FORMAT:
        die(f"not a workspace export (format {data.get('format')!r}, expected {FORMAT!r})")
    incoming = {n["key"]: n for n in data["nodes"]}
    templates = {t["id"]: t for t in data.get("templates", [])} or load_templates()
    existing = read_repo() if SPECS.exists() else {}
    TEMPLATES.mkdir(exist_ok=True)
    META.mkdir(exist_ok=True)
    for tid, t in templates.items():
        t = {k: v for k, v in t.items() if k != "version"}
        (TEMPLATES / f"{tid}.json").write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if data.get("meta"):
        (META / "blueprint.json").write_text(json.dumps(data["meta"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    num = numbering(incoming)
    written = unchanged = conflicts = 0
    for k, n in incoming.items():
        old = existing.get(k)
        target = spec_path(k, incoming)
        if old:
            local_changed = old.get("syncHash") and old["syncHash"] != content_hash(old)
            remote_changed = content_hash(n) != (old.get("syncHash") or content_hash(old))
            if local_changed and remote_changed and content_hash(n) != content_hash(old):
                side = target.with_name(f"{k}.workspace.md")
                side.write_text(node_to_md(n, incoming, templates, num), encoding="utf-8")
                print(f"CONFLICT {k}: changed in both places; workspace version written to {side.relative_to(ROOT)}")
                conflicts += 1
                continue
            if not remote_changed and Path(ROOT / old["_path"]) == target:
                unchanged += 1
                continue
            if Path(ROOT / old["_path"]) != target:
                (ROOT / old["_path"]).unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(node_to_md(n, incoming, templates, num), encoding="utf-8")
        written += 1
    removed = 0
    for k, old in existing.items():
        if k not in incoming:
            if not old.get("syncHash"):
                print(f"KEPT {k}: new in the repo and not yet in the workspace; run export and import it there")
                continue
            if old["syncHash"] != content_hash(old):
                print(f"KEPT {k}: deleted in the workspace but edited in the repo; resolve by hand")
                continue
            (ROOT / old["_path"]).unlink()
            removed += 1
    for d in sorted(SPECS.glob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    meta = data.get("meta") or {}
    write_index(read_repo(), load_templates(), meta)
    print(f"Imported: {written} written, {unchanged} unchanged, {removed} removed, {conflicts} conflict(s).")
    return 1 if conflicts else 0


def cmd_export(args) -> int:
    nodes = read_repo()
    templates = load_templates()
    out_nodes = []
    for k, n in sorted(nodes.items()):
        n = {f: v for f, v in n.items() if not f.startswith("_")}
        n["baseRev"] = n.get("rev")
        n.pop("syncHash", None)
        out_nodes.append(n)
    meta = json.loads((META / "blueprint.json").read_text(encoding="utf-8")) if (META / "blueprint.json").exists() else None
    payload = {"format": FORMAT, "direction": "repo-to-workspace", "nodes": out_nodes,
               "templates": list(templates.values()), "meta": meta}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out} ({len(out_nodes)} specs, {len(templates)} templates). "
          "Import it in the Spec Workspace: Overview > Repo sync > Import from repo.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("index")
    p = sub.add_parser("import")
    p.add_argument("file")
    p = sub.add_parser("export")
    p.add_argument("-o", "--output", default="build/workspace-import.json")
    args = ap.parse_args()
    return {"check": cmd_check, "index": cmd_index, "import": cmd_import, "export": cmd_export}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
