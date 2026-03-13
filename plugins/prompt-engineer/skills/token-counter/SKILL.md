---
name: token-counter
description: This skill should be used when the user asks to count tokens, measure prompt length, check token usage, compare token counts across models, or get a per-section token breakdown.
---

# Token Counter

Count tokens for strings and/or files. Accepts multiple inputs and models — prints a comparison table when there's more than one.

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
| (positional) | Strings to count tokens for (repeatable) |
| `-f FILE` | File path to count (repeatable) |
| `-m MODEL` | Model or encoding (repeatable). Accepts Claude models (`claude-opus-4-6`), OpenAI models (`gpt-5-mini`), or tiktoken encodings (`cl100k_base`). Default: `claude-opus-4-6` |
| `-s` | Per-section breakdown (YAML frontmatter + `##` headings). Use when the user wants to find which sections are expensive |

## Dependencies

`anthropic`, `openai`, `tiktoken` — assume pre-installed.
