## AGENTS.md for `worklog/task/`

Active units of work. Each task is a subfolder named `t{NNNN}-kebab-name`.

On completion (`status = "done"`), move the entire folder to `archive/task/` promptly.

### Subfolder contents

- `index.md` — **mandatory**. Defines what this task achieves and carries the frontmatter.
- `steps.md` — breakdown / checklist.
- `notes.md` — scratchpad, decisions, blockers.

Optional files are created only when needed.

### Frontmatter (`index.md`)

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

### Cross-references from tasks

```
task ──implements─────▶ plan
task ──modifies───────▶ spec
task ──blocked_by─────▶ task | plan
```
