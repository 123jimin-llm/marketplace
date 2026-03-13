## AGENTS.md for `worklog/spec/`

Current-state behavioral truths. Flat files named `s{NNNN}-kebab-name.md`.

**Immutable on their own** — only a task may modify a spec. Code diverging from a spec is a bug.

### Frontmatter

```toml
+++
id = "s0001"
title = "Topic name"
created = 2025-01-15
updated = 2025-01-15
tags = []
updated_by = []           # task IDs that modified this, append-only
+++
```

### Cross-references from specs

```
spec ──updated_by─────▶ task  (append-only trace)
```

`updated_by` is appended to, never replaced — it forms an audit trail.

Specs are not archived. They exist or they are deleted. Use git history for prior versions.
