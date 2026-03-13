---
name: invoke-llm
description: Use when the user asks to run a prompt against an LLM or test a prompt.
---

# Invoke LLM

Run a prompt against an LLM. Prints the response to stdout, or JSON with metadata when `--json` is used.

Write prompts to files, then invoke with `-U`/`-S` — keeps prompts reusable and version-controlled. All prompt flags are repeatable; multiple values are joined with double newlines.

```bash
# Quick one-shot
python scripts/invoke-llm.py "What is the capital of France?"

# System + user strings
python scripts/invoke-llm.py "Write a haiku" -s "You are a poet"

# File-based (preferred)
python scripts/invoke-llm.py -U prompt.md -S system.md
python scripts/invoke-llm.py -U prompt.md -S system.md -o output.md

# Compose multiple prompts
python scripts/invoke-llm.py -S role.md -S rules.md -U context.md -U question.md

# Different model
python scripts/invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --json
```

| Flag | Description |
|------|-------------|
| (positional) | User prompt string (shorthand for `-u`) |
| `-u TEXT` | User prompt string (repeatable) |
| `-U FILE` | User prompt from file (repeatable) |
| `-s TEXT` | System prompt string (repeatable) |
| `-S FILE` | System prompt from file (repeatable) |
| `-m MODEL` | Model ID. Claude → Anthropic API; others → OpenAI API. Default: `claude-sonnet-4-6` |
| `-t TEMP` | Temperature. Default: `1.0` |
| `--max-tokens N` | Max output tokens. Default: `4096` |
| `-o FILE` | Write output to file (still prints to stdout) |
| `--json` | JSON output with metadata (response, model, tokens, latency, stop_reason) |

## Dependencies

See `../../lib/requirements.txt`. Assume all packages are pre-installed.
