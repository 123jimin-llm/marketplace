---
name: worklog
description: "Manage project tasks, plans, and specs via flat-file worklog. Trigger on: create task, plan work, track progress, initialize worklog, manage specs, archive task, what should I work on."
---

# Worklog

Repo-agnostic flat-file project management. Keep files small; each must be readable independently.

`archive/` (`archive/task/`, `archive/plan/`, `archive/spec/`) is write-only — do not read under normal use.

**NEVER use `mv`, `git mv`, or manual file moves to archive items.** Always use `worklog/script/archive.py` — it validates status and cleans up cross-references. If `worklog/script/` does not exist, run `init-worklog.py` first to create it.

## Items

IDs: 4-digit increment per class (`t0001`, `p0001`, `s0001`). Scan active + `archive/` when assigning. Kebab suffix is filename only, not in frontmatter.

| Type | Location | Statuses | Archive to |
|------|----------|----------|------------|
| Spec | `spec/s{NNNN}-kebab.md` | — | `archive/spec/` |
| Plan | `plan/p{NNNN}-kebab.md` or `plan/p{NNNN}-kebab/` | draft, approved, active, abandoned | `archive/plan/` |
| Task | `task/t{NNNN}-kebab.md` or `task/t{NNNN}-kebab/` | pending, active, blocked, done | `archive/task/` |

Directory format: `{id}-kebab/index.md` + supporting files. Flat format: `{id}-kebab.md` (default for new items).

Default to flat files. When supporting files are needed (`steps.md`, `notes.md`), promote to directory: move `{id}.md` → `{id}/index.md`, then add files alongside.

- Specs are **immutable** — only a task may modify or archive. Write spec content from the plan, not the codebase. Code diverging from a spec is a bug.
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

## Cross-References

Forward-only. Use `find-refs.py` for reverse lookups.

```
plan ──targets────────▶ spec
task ──implements─────▶ plan
task ──modifies───────▶ spec
task ──blocked_by─────▶ task | plan
plan ──blocked_by─────▶ task | plan
```

Use `find-refs.py` to find which tasks modified a spec (reverse lookup of `modifies`).

## Lifecycle

1. Write a **plan** (`draft`) targeting specs to create or modify.
2. When approved, create **tasks** that `implement` it.
3. Tasks work through steps, modifying **specs**.
4. Archive completed tasks, then the plan when all tasks finish.

Small or reactive work can skip the plan — start directly as a task.

## Source Code Markers

When a task modifies source code that implements a spec, mark the connection using `@worklog sNNNN` in comments. Use the comment style appropriate for the language and codebase conventions.

**File-level** — at the top of a file, listing all specs it implements:

    @worklog s0001 (login flow), s0003 (session handling)

**Inline** — near specific code tied to a spec:

    @worklog s0001

When you encounter an existing `@worklog` marker while editing code, invoke `/worklog` to check whether the referenced spec needs updating.

## Validation

Run `worklog/script/validate.py` after any batch of changes. It checks:
- Dangling cross-references (target ID does not exist)
- Stale `blocked_by` entries (blocking item already done/archived)
- Plans ready to archive (all implementing tasks complete)
- Invalid statuses and missing required fields
- Deprecated fields (`updated_by`) — remove when encountered

Archiving a completed item automatically removes it from `blocked_by` fields of active items. Archiving an abandoned item warns but does not auto-clean.

## Scripts

Scripts live in `worklog/script/`. If the directory is missing, run `init-worklog.py` to create it. All accept `-w PATH` for worklog root (default: `./worklog`). Run `--help` for full usage.

```bash
worklog/script/next-id.py task                         # next available ID (e.g. t0015)
worklog/script/list.py task -s active                  # list items; -s status, -t tag, --json
worklog/script/find-refs.py t0001 [--include-archive]  # reverse-lookup references to an ID
worklog/script/archive.py t0001 [--force]              # move completed item to archive/
worklog/script/validate.py [--strict]                  # check refs, statuses, archivable items
```
