## AGENTS.md for `worklog/plan/`

Future-facing designs — mutable ideas not yet (or being) applied to code. Each plan is a subfolder named `p{NNNN}-kebab-name`.

Archived to `archive/plan/` when fully applied or abandoned.

### Subfolder contents

- `overview.md` — **mandatory**. Problem statement, proposed solution, and carries the frontmatter.
- Additional topic-specific files as needed (`api.md`, `open.md`, etc.).

### Frontmatter (`overview.md`)

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

### Cross-references from plans

```
plan ──targets────────▶ spec
plan ──blocked_by─────▶ task | plan
```

Tasks reference plans via `implements` — do not maintain a task list here.
