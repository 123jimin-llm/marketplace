---
name: token-counter
description: Use when the user asks to count tokens, measure prompt length, or check token usage.
---

# Token Counter

Count tokens for strings and/or files. Accepts multiple inputs and models — prints a comparison table when there's more than one.

```bash
# Single string or file
python scripts/token-count.py "some text"
python scripts/token-count.py -f prompt.md

# Multiple strings and files, mixed freely
python scripts/token-count.py "v1 prompt" "v2 prompt" -f base.md

# Cross with multiple models
python scripts/token-count.py "v1" "v2" -f base.md -m claude-opus-4-6 -m gpt-5-mini

# Section breakdown (single file)
python scripts/token-count.py -f SKILL.md -s
python scripts/token-count.py -f SKILL.md -s -m claude-opus-4-6 -m gpt-5-mini
```

| Flag | Description |
|------|-------------|
| (positional) | Strings to count tokens for (repeatable) |
| `-f FILE` | File path to count (repeatable) |
| `-m MODEL` | Model or encoding (repeatable). Accepts Claude models (`claude-opus-4-6`), OpenAI models (`gpt-5-mini`), or tiktoken encodings (`cl100k_base`). Default: `claude-opus-4-6` |
| `-s` | Per-section breakdown (YAML frontmatter + `##` headings). Use when the user wants to find which sections are expensive |

## Dependencies

See `../../lib/requirements.txt`. Assume all packages are pre-installed.
