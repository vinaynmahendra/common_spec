# CLAUDE.md: working on the Nomology platform specs

This repo holds the requirements and specifications for Nomology's new multi-tenant legal-tech platform. Nomology runs two products on it, CORD and TERES, through three entities: NTPL in India, TAPL in Singapore, and a US entity. Each spec is one Markdown file. The same specs are mirrored in the **Platform Spec Workspace** (a claude.ai artifact), where people browse and review them. Read this file before changing anything.

## The platform, in one paragraph

The platform runs Next.js (App Router) in a Turborepo monorepo (packages are `@nomology/*`), in TypeScript, with Prisma.

| Concern | Choice |
|---|---|
| Database | Postgres: one shared database per region, with `tenant_id` and forced row-level security. The tenant is set per transaction through a Prisma client extension. |
| Connection pooling | PgBouncer in transaction mode |
| Workflows | Self-hosted Temporal per region; code-defined state machines; BullMQ on Redis |
| Hosting | ECS, or Azure Container Apps where required |
| Regions | India, Singapore and US; data stays in region |
| Regulation | SEBI ODR (aggregator reporting via NSE), the DPDP Act, Singapore PDPA, US state law, WCAG 2.2 AA |

Approved decisions are in `specs/ADR/` and must not be contradicted.

## Layout

| Path | What it is |
|---|---|
| `specs/<AREA>/<ID>.md` | One spec per file. `<AREA>` is the ID of the top-level area (`PKG`, `WF`, `APP`, …). |
| `specs/README.md` | The numbered tree of all specs (generated) |
| `templates/<id>.json` | The template each kind of spec follows: sections (level 1 Core, 2 Full, 3 Optional), guidance, illustrative examples, review checks. **Source of truth.** |
| `templates/<id>.md` | Readable version of each template (generated) |
| `meta/shared-model.md` | **Binding vocabulary**: configuration scopes, role keys, permission and setting naming, change lifecycle, workflow authoring boundary, AI principles, agreed decisions D1–D13 |
| `meta/open-questions.md` | Every open question across all specs (generated) |
| `meta/blueprint.json` | Workspace title and the scope note |
| `tools/specs.py` | Check, index and sync tool (Python 3.9+, standard library only) |

## Spec file format

```
---
id: "PKG-settings-ai"            <- permanent; equals the file name; never change it
title: "AI settings"
parent: "PKG-settings-catalogue"  <- the parent spec's id (null for an area)
order: 2                          <- position among siblings
type: "feature"                   <- area | capability | feature | requirement | decision | design
template: "config"                <- template id (null = inherited from the parent)
status: "draft"                   <- outline | draft | review | approved | built
owner: null
indicative: false
summary: "one line"
links: []                         <- typed links: [{"rel": "depends", "to": "ID"}]
rev: 1                            <- workspace revision at last sync: do not edit
syncHash: "…"                     <- content hash at last sync: do not edit
createdAt / updatedAt / updatedBy
---
# 5.7.3.2 AI settings             <- generated heading (number from the tree)

<!-- section:purpose -->
## Purpose and scope
…text…

<!-- checks -->
## Template checks
<!-- check:tenancy -->
### Tenant isolation
…answer…

<!-- citations -->
## Citations
```json
[{"id": "R1", "kind": "standard", "title": "…", "url": "…"}]
```
<!-- end -->
```

Rules:
- **Markers and front matter:**
  - Edit the text between the markers. Keep every `<!-- … -->` marker. The heading straight after a marker is regenerated from the template, so don't rely on editing it.
  - Front-matter values are JSON (strings in double quotes). `rev` and `syncHash` are maintained by the sync tool.
- **Sections:** a section id must exist in the spec's template (`templates/<template>.json`). To add a section, add a `<!-- section:<id> -->` block. Template order is applied on the next sync.
- **Internal links:** `[[ID]]` links to a spec and `[[ID#section-id]]` to one part of it. The ID must exist.
- **Citations:** `[R1]` in the text must match an entry under Citations. Cite only real, authoritative sources you have confirmed (regulations, standards, official vendor docs). No citation is better than a guessed one.
- **New spec:**
  1. Create `specs/<AREA>/<NEW-ID>.md` with the front matter above. Set `rev: 0` and omit `syncHash`.
  2. Make the ID the area prefix plus a short slug of at most 5 words, for example `PKG-settings-ai`.
  3. Pick the template that fits.
- **Moving a spec:** change `parent` and `order`. The file moves folder on the next sync if its area changes.
- **Approved specs** (`status: "approved"`, mainly ADRs) are never edited. Supersede them with a new record linked both ways. `tools/specs.py check` flags edits.

## How to write

- Follow the template's `guide` and `depth` for each section. Write every Core section, most Full sections, and `questions`.
- Plain English. No marketing language. Prefer tables and bullet lists.
- Use numbered requirements with one prefix per spec (`CFG-FR-7`), Given/When/Then acceptance criteria, and schema or code sketches where the template asks for them.
- Be specific to this platform: real routes (`/admin/...`, `/platform/...`, `/me/settings`), tables, Temporal workflow and BullMQ queue names, permission keys (`resource:action`), setting keys (`domain.area.name`), personas and role keys from `meta/shared-model.md`, and the three regions.
- Never invent facts about real organisations (HKIAC, SEBI, NSE, clients) or legal figures. Write "Assumption: …, to be confirmed by legal" and add an Open question with an owner.
- Do not copy a template's illustrative example into a spec.
- A parent summarises and links; detail lives in the child. Each setting key is defined in exactly one settings catalogue (`specs/PKG/PKG-settings-*.md`). Each permission key is listed in `specs/PKG/PKG-permission-catalogue.md`.

## Before you commit

```bash
python3 tools/specs.py check   # must report 0 problems
python3 tools/specs.py index   # regenerate the tree, open questions and template pages
```
Work on a branch and open a pull request. CI runs `check` on every pull request.

## Keeping the repo and the workspace in step

**Both are kept.** The repo is where engineers and Claude Code work. The workspace is where people browse, review and comment, and where non-engineers edit.

| Direction | Steps |
|---|---|
| Workspace → repo | In the workspace: **Overview → Repo sync → Export for repo (.json)**. In the repo, on a branch: `python3 tools/specs.py import workspace-export.json`, then check, commit and open a pull request. |
| Repo → workspace | After merging to `main`: `python3 tools/specs.py export`, which writes `build/workspace-import.json`. In the workspace: **Overview → Repo sync → Import from repo**. Review the summary, then apply. |

Conflicts:
- **Changed in both places:** a spec changed in both places since the last sync is never overwritten.
  - In the repo, `import` writes the workspace version beside the file as `<ID>.workspace.md`. Merge the two by hand, delete the side file, then import again or commit.
  - In the workspace, conflicts are listed and skipped.
- **Deletions:** a spec deleted in the workspace is removed from the repo on import, unless it was edited in the repo.
- **Workspace-only specs:** specs that exist only in the workspace are kept there and reported. Export them to bring them into the repo.

Sync often, and don't edit the same spec in both places between syncs. A Claude session that has access to the workspace artifact (Claude Cowork) can also run the sync for you. Ask it to "sync the repo and the Spec Workspace".

## Good first tasks

- Work through `meta/open-questions.md` for one area, with the owners named there.
- Take a decision in `specs/ADR/` from Proposed to Approved once the CTO decides. Approval is the CTO's.
- Turn a data-model spec (`PKG-settings-data-model`, `PKG-authorization-data-model`, `WF-process-definition-model`) into a Prisma schema in the platform repo, keeping the spec in step.
