---
name: token-counter
description: Count tokens in strings or files. Trigger on: how many tokens, measure prompt length, context window fit, token budget, per-section breakdown.
---

# Token Counter

Script: `scripts/token-count.py`

```bash
token-count.py "some text"
token-count.py -f prompt.md
token-count.py "v1" "v2" -f base.md
token-count.py "v1" "v2" -m claude-opus-4-6 -m gpt-5-mini
token-count.py -f SKILL.md -s
```

| Flag | Description |
|------|-------------|
| (positional) | Strings to count (repeatable) |
| `-f FILE` | File to count (repeatable) |
| `-m MODEL` | Model or tiktoken encoding (repeatable). Default: `claude-opus-4-6` |
| `-s` | Per-section breakdown (YAML frontmatter + `##` headings) |

Multiple inputs or models print a comparison table.
