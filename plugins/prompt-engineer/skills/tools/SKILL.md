---
name: tools
description: Use when the user asks to count tokens, measure prompt length, or check token usage for a string or file.
---

# Prompt Tools

## Available scripts

- **`scripts/token-count.py`** — Count tokens in a string or file.

## Token Count

Count tokens for a string or file. Report the result to the user.

```bash
python scripts/token-count.py "text"
python scripts/token-count.py -f path/to/file.md
python scripts/token-count.py -f path/to/SKILL.md -s
```

### Flags

| Flag | Description |
|------|-------------|
| `-f` | Treat input as a file path |
| `-s` | Per-section breakdown (YAML frontmatter + `##` headings). Use when the user wants to find which sections are expensive |
| `-m MODEL` | Model or encoding to count against. Accepts Claude models (`claude-opus-4-6`), OpenAI models (`gpt-4o`), or tiktoken encodings (`cl100k_base`). Defaults to `claude-opus-4-6` |

### Dependencies

`anthropic` for Claude models (default), `tiktoken` for OpenAI models/encodings. Assume installed; do not check or install.
