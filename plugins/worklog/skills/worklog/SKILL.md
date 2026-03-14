---
name: worklog
description: "Manage project tasks, plans, and specs via flat-file worklog. Trigger on: create task, plan work, track progress, initialize worklog, manage specs, archive task, what should I work on."
---

# Worklog

Repo-agnostic flat-file project management. Keep files small; each must be readable independently.

`archive/` (`archive/task/`, `archive/plan/`) is write-only — do not read under normal use.

## Items

IDs: 4-digit increment per class (`t0001`, `p0001`, `s0001`). Scan active + `archive/` when assigning. Kebab suffix is filename only, not in frontmatter.

| Type | Location | Statuses | Archive to |
|------|----------|----------|------------|
| Spec | `spec/s{NNNN}-kebab.md` | — | never |
| Plan | `plan/p{NNNN}-kebab.md` or `plan/p{NNNN}-kebab/` | draft, approved, active, abandoned | `archive/plan/` |
| Task | `task/t{NNNN}-kebab.md` or `task/t{NNNN}-kebab/` | pending, active, blocked, done | `archive/task/` |

Directory format: `{id}-kebab/index.md` + supporting files. Flat format: `{id}-kebab.md` (default for new items).

Default to flat files. When supporting files are needed (`steps.md`, `notes.md`), promote to directory: move `{id}.md` → `{id}/index.md`, then add files alongside.

- Specs are **immutable** — only a task may modify. Code diverging from a spec is a bug.
- Plans: flat file, or directory with `index.md` + additional files as needed. Do not maintain a task list.
- Tasks: flat file, or directory with `index.md` + optional `steps.md` (checklist), `notes.md` (scratchpad).
- Tags: `tags.md` at worklog root — one per line as `- name: description`.

### Frontmatter

`+++`-delimited TOML. Include only fields marked for the type.

```toml
+++
id = "t0001"
title = "Fix login timeout"
status = "pending"
created = 2025-01-15
tags = ["auth"]
implements = ["p0003"]
+++
```

| Field | Spec | Plan | Task | Values / notes |
|-------|:----:|:----:|:----:|----------------|
| `id` | x | x | x | e.g. `"t0001"` |
| `title` | x | x | x | string |
| `created` | x | x | x | `YYYY-MM-DD` |
| `updated` | x | | | `YYYY-MM-DD` |
| `tags` | x | x | x | `[]` |
| `status` | | x | x | see statuses above |
| `blocked_by` | | x | x | task/plan IDs |
| `targets` | | x | | spec IDs to create/modify |
| `implements` | | | x | plan IDs |
| `modifies` | | | x | spec IDs |
| `updated_by` | x | | | task IDs, append-only |

## Cross-References

Forward-only. Use `find-refs.py` for reverse lookups.

```
plan ──targets────────▶ spec
task ──implements─────▶ plan
task ──modifies───────▶ spec
task ──blocked_by─────▶ task | plan
plan ──blocked_by─────▶ task | plan
spec ──updated_by─────▶ task  (append-only)
```

## Lifecycle

1. Write a **plan** (`draft`) targeting specs to create or modify.
2. When approved, create **tasks** that `implement` it.
3. Tasks work through steps, modifying **specs**.
4. Archive completed tasks, then the plan when all tasks finish.

Small or reactive work can skip the plan — start directly as a task.

## Scripts

All accept `-w PATH` for worklog root (default: `./worklog`). Run `--help` for full usage.

```bash
init-worklog.py [path]                  # scaffold directory tree
next-id.py task                         # next available ID (e.g. t0015)
list.py task -s active                  # list items; -s status, -t tag, --json
find-refs.py t0001 [--include-archive]  # reverse-lookup references to an ID
archive.py t0001 [--force]              # move completed item to archive/
```
