---
name: worklog
description: "Manage project tasks, plans, and specs via flat-file worklog. Trigger on: create task, plan work, track progress, initialize worklog, manage specs, archive task, what should I work on."
---

# Worklog

A flat-file project management system for LLM agents. All state lives in scannable, convention-driven files so any agent session can bootstrap itself from this skill alone. The worklog subtree is **repo-agnostic** — it tracks work independent of what the repository builds. Keep files small and modularized; each file must be readable independently.

## Directory Structure

```text
worklog/
├── task/              # Active units of work (subfolders)
├── plan/              # Future-facing designs (subfolders)
├── spec/              # Current-state behavioral truths (flat files)
├── tag/               # Tag definitions (one file per tag)
└── archive/           # Write-only graveyard — do not read under normal use
    ├── task/
    └── plan/
```

## Item Types

| Type | Dir | Naming | Entry file | Statuses | Archive? |
|------|-----|--------|------------|----------|----------|
| Spec | `spec/` (flat) | `s{NNNN}-kebab.md` | — (file itself) | — | Never (delete or keep) |
| Plan | `plan/` (subfolder) | `p{NNNN}-kebab/` | `index.md` | draft, approved, active, abandoned | `archive/plan/` |
| Task | `task/` (subfolder) | `t{NNNN}-kebab/` | `index.md` | pending, active, blocked, done | `archive/task/` |

### Spec

Flat files in `spec/`. **Immutable on their own** — only a task may modify a spec. Code diverging from a spec is a bug. Specs are never archived; they exist or they are deleted (use git history for prior versions).

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

### Plan

Subfolders in `plan/`. Archived to `archive/plan/` when fully applied or abandoned.

- `index.md` — **mandatory**. Problem statement, proposed solution, frontmatter.
- Additional topic-specific files as needed (`api.md`, `open.md`, etc.).

```toml
+++
id = "p0001"
title = "Short descriptive title"
status = "draft"          # draft | approved | active | abandoned
created = 2025-01-15
tags = []
blocked_by = []           # IDs: "t0003", "p0002", etc.
targets = []              # spec IDs this plan would create or modify
+++
```

Tasks reference plans via `implements` — do not maintain a task list here.

### Task

Subfolders in `task/`. On completion (`status = "done"`), move to `archive/task/` promptly.

- `index.md` — **mandatory**. Defines what this task achieves, carries the frontmatter.
- `steps.md` — breakdown / checklist. Created only when needed.
- `notes.md` — scratchpad, decisions, blockers. Created only when needed.

```toml
+++
id = "t0001"
title = "Short imperative title"
status = "pending"        # pending | active | blocked | done
created = 2025-01-15
tags = []
blocked_by = []           # IDs: "t0003", "p0002", etc.
implements = []           # plan IDs
modifies = []             # spec IDs
+++
```

### Tags

One file per tag in `tag/`, named `{tag_name}.md`. Brief description, no frontmatter. The filename is the ID.

## ID Format

4-digit increment with a letter prefix. Each class has its own counter. The frontmatter `id` field is the prefix+number only (e.g. `"t0001"`); the kebab suffix is part of the filename/folder name.

| Class | Format | Filename example |
|---|---|---|
| Task  | `t{NNNN}` | `t0001-bootstrap-worklog/` |
| Plan  | `p{NNNN}` | `p0001-plugin-system/` |
| Spec  | `s{NNNN}` | `s0001-auth.md` |

IDs span active + archive — always scan both when assigning.

## Cross-References

All references are **forward-only**. Use `find-refs.py` for reverse lookups.

```
plan ──targets────────▶ spec
task ──implements─────▶ plan
task ──modifies───────▶ spec
task ──blocked_by─────▶ task | plan
plan ──blocked_by─────▶ task | plan
spec ──updated_by─────▶ task  (append-only)
```

## Lifecycle

1. Write a **plan** (`draft`) describing a desired change and which specs it targets.
2. When approved, create one or more **tasks** that `implement` it.
3. Each task works through its steps, modifying **specs** as it goes.
4. Completed tasks are archived. When all tasks for a plan are done, the plan is archived.

Not every task needs a plan — small or reactive work can start directly as a task.

## Scripts

All scripts accept `-w PATH` to set the worklog root (default: `./worklog`).

```bash
# init-worklog.py — scaffold directory tree with .gitkeep
init-worklog.py [path]          # default: ./worklog

# next-id.py — print next available ID
next-id.py task                 # -> t0001
next-id.py plan                 # -> p0003

# list.py — list items by type/status/tag
list.py task                    # all tasks
list.py task -s active          # filter by status
list.py spec -t auth            # filter by tag
list.py plan --json             # JSON output

# find-refs.py — reverse-lookup cross-references (frontmatter + body)
find-refs.py t0001              # who references t0001?
find-refs.py s0002 --include-archive

# archive.py — move completed items to archive/
archive.py t0001                # task must be "done"
archive.py p0003 --force        # skip status check (plans: "abandoned" or "active")
```
