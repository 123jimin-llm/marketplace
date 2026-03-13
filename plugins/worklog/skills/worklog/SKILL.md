---
name: worklog
description: "Manage project tasks, plans, and specs via flat-file worklog. Trigger on: create task, plan work, track progress, initialize worklog, manage specs, archive task, what should I work on."
---

# Worklog

A flat-file project management system for LLM agents. All state lives in scannable, convention-driven files so any agent session can bootstrap itself by reading `AGENTS.md` files.

If the project has a `worklog/AGENTS.md`, **read it first** — it may contain project-specific overrides.

## Directory Structure

```text
worklog/
├── AGENTS.md          # Root conventions
├── task/              # Active units of work (subfolders)
├── plan/              # Future-facing designs (subfolders)
├── spec/              # Current-state behavioral truths (flat files)
├── tag/               # Tag definitions (one file per tag)
└── archive/           # Write-only graveyard
    ├── task/
    └── plan/
```

## Item Types

| Type | Dir | Naming | Entry file | Statuses | Archive? |
|------|-----|--------|------------|----------|----------|
| Spec | `spec/` (flat) | `s{NNNN}-kebab.md` | — (file itself) | — | Never (delete or keep) |
| Plan | `plan/` (subfolder) | `p{NNNN}-kebab/` | `index.md` | draft, approved, active, abandoned | `archive/plan/` |
| Task | `task/` (subfolder) | `t{NNNN}-kebab/` | `index.md` | pending, active, blocked, done | `archive/task/` |

Plans may include additional files. Tasks may include `steps.md` (checklist) and `notes.md` (scratchpad).

### Frontmatter fields

All items use `+++`-delimited TOML. Common fields: `id`, `title`, `created`, `tags = []`.

| Field | Spec | Plan | Task | Notes |
|-------|:----:|:----:|:----:|-------|
| `updated` | x | | | |
| `status` | | x | x | see statuses above |
| `blocked_by` | | x | x | task or plan IDs |
| `targets` | | x | | spec IDs to create/modify |
| `implements` | | | x | plan IDs |
| `modifies` | | | x | spec IDs |
| `updated_by` | x | | | task IDs, append-only audit trail |

Specs are **immutable on their own** — only a task may modify a spec.

### Tags

One file per tag in `tag/`, named `{tag_name}.md`. Brief description, no frontmatter.

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
# init-worklog.py — scaffold directory tree with AGENTS.md + .gitkeep
init-worklog.py [path]          # default: ./worklog
init-worklog.py --force         # overwrite existing AGENTS.md files

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
