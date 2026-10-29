# Nomology platform requirements and specifications

These are the requirements and specifications for Nomology's multi-tenant legal-tech platform, which runs CORD and TERES across India, Singapore and the US. The repo holds 333 specs in 19 areas, written against 28 templates. They cover foundations, the Next.js app, multi-tenancy, shared packages, domain modules, workflows, AI, integrations, billing, observability, reporting, security, infrastructure, delivery, testing, documentation, the implementation plan and decision records.

| Start here | |
|---|---|
| [specs/README.md](specs/README.md) | The full numbered tree, with status |
| [meta/shared-model.md](meta/shared-model.md) | Vocabulary and agreed conventions every spec follows |
| [meta/open-questions.md](meta/open-questions.md) | Open questions and assumptions, by area |
| [specs/ADR/](specs/ADR/) | Decision records (8 approved, 4 proposed) |
| [templates/README.md](templates/README.md) | The spec templates |
| [CLAUDE.md](CLAUDE.md) | How to edit specs, conventions, and how sync with the Spec Workspace works |

## Tooling

```bash
python3 tools/specs.py check                      # validate links, parents, sections, citations
python3 tools/specs.py index                      # regenerate the tree and question list
python3 tools/specs.py import workspace-export.json   # workspace -> repo
python3 tools/specs.py export                     # repo -> workspace (build/workspace-import.json)
```

The specs are mirrored in the Platform Spec Workspace (a claude.ai artifact) for browsing, review and editing by non-engineers. See CLAUDE.md for the sync rules.

`[[ID]]` in a spec is a link to the spec with that ID: `specs/<AREA>/<ID>.md`.
