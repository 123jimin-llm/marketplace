## AGENTS.md for `worklog/`

This subtree is **repo-agnostic** — it tracks work, plans, and specs independent of what this repository builds.

Keep files small and modularized. Each file must be readable independently.

### Subdirectories

- `task/` — active units of work. See `task/AGENTS.md`.
- `plan/` — future-facing designs. See `plan/AGENTS.md`.
- `spec/` — current-state behavioral truths. See `spec/AGENTS.md`.
- `tag/` — tag definitions. See `tag/AGENTS.md`.
- `script/` — agent-executable scripts. See `script/AGENTS.md`.
- `archive/` — write-only graveyard. See `archive/AGENTS.md`.

### ID format

4-digit increment with a letter prefix per class. Each class has its own independent counter.

| Class | Format | Example |
|---|---|---|
| Task  | `t{NNNN}-kebab-name` | `t0001-bootstrap-worklog` |
| Plan  | `p{NNNN}-kebab-name` | `p0001-plugin-system` |
| Spec  | `s{NNNN}-kebab-name` | `s0001-auth` |

To assign the next ID, scan existing entries in the class directory **and** `archive/` for the highest number.

### Frontmatter format

All worklog items use TOML frontmatter delimited by `+++`. Example:

```toml
+++
id = "t0001"
title = "Short imperative title"
status = "pending"
created = 2025-01-15
tags = []
blocked_by = []
implements = []
modifies = []
+++
```

### Cross-references

All references are **forward-only**: the referencing doc names the target ID. Do not maintain backlinks manually — use scripts for reverse lookups.

```
plan ──targets────────▶ spec
task ──implements─────▶ plan
task ──modifies───────▶ spec
task ──blocked_by─────▶ task | plan
plan ──blocked_by─────▶ task | plan
spec ──updated_by─────▶ task  (append-only audit trail)
```
