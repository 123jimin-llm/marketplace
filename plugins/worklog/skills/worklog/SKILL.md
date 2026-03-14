---
name: worklog
description: "Manage project tasks, plans, and specs via flat-file worklog. Trigger on: create task, plan work, track progress, initialize worklog, manage specs, archive task, what should I work on."
---

# Worklog

Repo-agnostic flat-file project management. Keep files small; each must be readable independently.

`archive/` (`archive/task/`, `archive/plan/`) is write-only — do not read under normal use.

## Items

IDs: 4-digit increment per class (`t0001`, `p0001`, `s0001`). Scan active + `archive/` when assigning. Kebab suffix is filename only, not stored in frontmatter. All frontmatter is `+++`-delimited TOML.

### Spec — `spec/s{NNNN}-kebab.md`

Flat files. **Immutable** — only a task may modify. Code diverging from a spec is a bug. Never archived (delete or use git history).

```toml
+++
id = "s0001"
title = "Topic name"
created = 2025-01-15
updated = 2025-01-15
tags = []
updated_by = []           # task IDs, append-only audit trail
+++
```

### Plan — `plan/p{NNNN}-kebab/`

Subfolders. Archive to `archive/plan/` when fully applied or abandoned.

- `index.md` — **required**. Problem statement, proposed solution, frontmatter.
- Additional files as needed.

```toml
+++
id = "p0001"
title = "Short descriptive title"
status = "draft"          # draft | approved | active | abandoned
created = 2025-01-15
tags = []
blocked_by = []           # task or plan IDs
targets = []              # spec IDs to create or modify
+++
```

Do not maintain a task list — tasks reference plans via `implements`.

### Task — `task/t{NNNN}-kebab/`

Subfolders. Archive to `archive/task/` promptly when `status = "done"`.

- `index.md` — **required**. What this task achieves, frontmatter.
- `steps.md` — checklist. Create when needed.
- `notes.md` — scratchpad. Create when needed.

```toml
+++
id = "t0001"
title = "Short imperative title"
status = "pending"        # pending | active | blocked | done
created = 2025-01-15
tags = []
blocked_by = []           # task or plan IDs
implements = []           # plan IDs
modifies = []             # spec IDs
+++
```

### Tag — `tag/{name}.md`

One file per tag. Brief description, no frontmatter.

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
