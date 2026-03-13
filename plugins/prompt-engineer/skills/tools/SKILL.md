---
name: tools
description: Use when the user asks to count tokens, measure prompt length, or check token usage for a string or file.
---

# Prompt Tools

## Token Count

Run `scripts/token-count.py` from this skill's directory to count tokens. Report the result to the user.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/token-count.py" "text"
python "${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/token-count.py" -f path/to/file.md
```

### Dependencies

`anthropic` for Claude models (default), `tiktoken` for OpenAI models/encodings.

### Flags

- `-f` — Input is a file path.
- `-s` — Per-section breakdown (YAML frontmatter + `##` headings). Use when the user wants to find which sections are expensive.
- `-m MODEL` — Model or encoding to count against. Accepts Claude models (`claude-opus-4-6`), OpenAI models (`gpt-4o`), or tiktoken encodings (`cl100k_base`). Defaults to `claude-opus-4-6`.
