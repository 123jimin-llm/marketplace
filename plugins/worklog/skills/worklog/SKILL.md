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
├── script/            # Project-specific scripts
└── archive/           # Write-only graveyard
    ├── task/
    └── plan/
```

## Item Types

### Specs — what is true now

Flat files in `spec/` named `s{NNNN}-kebab-name.md`. A spec describes current-state behavior. Code diverging from a spec is a bug.

**Immutable on their own** — only a task may modify a spec. `updated_by` forms an append-only audit trail.

```toml
+++
id = "s0001"
title = "Topic name"
created = 2025-01-15
updated = 2025-01-15
tags = []
updated_by = []         # task IDs, append-only
+++
```

Specs are never archived — they exist or they are deleted.

### Plans — what should change

Subfolders in `plan/` named `p{NNNN}-kebab-name`. A plan proposes a change: problem statement, solution design, and which specs it would create or modify.

Mandatory file: `overview.md` (carries frontmatter). Additional files as needed.

```toml
+++
id = "p0001"
title = "Short descriptive title"
status = "draft"          # draft | approved | active | abandoned
created = 2025-01-15
tags = []
blocked_by = []           # task or plan IDs
targets = []              # spec IDs this plan would create or modify
+++
```

Archived to `archive/plan/` when fully applied or abandoned.

### Tasks — what to do

Subfolders in `task/` named `t{NNNN}-kebab-name`. A task is a concrete unit of work that implements plans and modifies specs.

Mandatory file: `goal.md` (carries frontmatter). Optional: `steps.md` (checklist), `notes.md` (scratchpad).

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

On completion (`status = "done"`), archive the entire folder.

### Tags

One file per tag in `tag/`, named `{tag_name}.md`. Brief description, no frontmatter.

## ID Format

4-digit increment with a letter prefix. Each class has its own counter.

| Class | Format | Example |
|---|---|---|
| Task  | `t{NNNN}` | `t0001-bootstrap-worklog` |
| Plan  | `p{NNNN}` | `p0001-plugin-system` |
| Spec  | `s{NNNN}` | `s0001-auth` |

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

## Frontmatter Format

All worklog items use **TOML frontmatter** delimited by `+++`. No YAML support.

## Scripts

### `init-worklog.py` — Scaffold worklog directory tree

```bash
init-worklog.py [path]          # default: ./worklog
init-worklog.py --force         # overwrite existing AGENTS.md files
```

| Flag | Description |
|------|-------------|
| `path` (positional) | Root path for the worklog (default: `./worklog`) |
| `--force` | Overwrite existing AGENTS.md files |

Creates the full directory tree with AGENTS.md files and .gitkeep files. Idempotent — skips existing files unless `--force`.

### `next-id.py` — Get next available ID

```bash
next-id.py task                 # -> t0001
next-id.py plan -w ./worklog   # -> p0003
next-id.py spec                # -> s0001
```

| Flag | Description |
|------|-------------|
| `item_class` (positional) | `task`, `plan`, or `spec` |
| `-w PATH` | Worklog root directory (default: `./worklog`) |

### `list.py` — List items by type/status/tag

```bash
list.py task                    # all tasks
list.py task -s active          # active tasks only
list.py spec -t auth            # specs tagged "auth"
list.py plan --json             # JSON output
```

| Flag | Description |
|------|-------------|
| `item_class` (positional) | `task`, `plan`, or `spec` |
| `-s STATUS` | Filter by status |
| `-t TAG` | Filter by tag |
| `-w PATH` | Worklog root directory (default: `./worklog`) |
| `--json` | Output as JSON instead of table |

### `find-refs.py` — Reverse-lookup cross-references

```bash
find-refs.py t0001                  # who references t0001?
find-refs.py s0002 --include-archive
```

| Flag | Description |
|------|-------------|
| `target_id` (positional) | The ID to search for |
| `-w PATH` | Worklog root directory (default: `./worklog`) |
| `--include-archive` | Also search archived items |

Searches both frontmatter reference fields and body text.

### `archive.py` — Archive completed items

```bash
archive.py t0001                # archive task t0001
archive.py p0003 --force        # skip status check
```

| Flag | Description |
|------|-------------|
| `item_id` (positional) | Item ID to archive (t#### or p####) |
| `-w PATH` | Worklog root directory (default: `./worklog`) |
| `--force` | Skip status validation |

Tasks must have `status = "done"`. Plans must have `status = "abandoned"` or `"active"` (fully applied). Use `--force` to override.
