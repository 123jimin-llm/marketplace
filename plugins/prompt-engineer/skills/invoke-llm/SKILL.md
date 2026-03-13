---
name: invoke-llm
description: Run prompts against LLMs. Trigger on: test/send/invoke a prompt, get a completion, compare models, matrix sweep, batch-test prompts.
---

# Invoke LLM

Script: `scripts/invoke-llm.py`

## Single-shot mode

```bash
invoke-llm.py "What is the capital of France?"
invoke-llm.py "Write a haiku" -s "You are a poet"
invoke-llm.py -U prompt.md -S system.md -o output.md
invoke-llm.py -S role.md -S rules.md -U context.md -U question.md
invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --json
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

Repeatable flags are joined with double newlines. When combining `-u`/`-U` (or `-s`/`-S`), strings come before file contents.

## TOML config mode

```bash
invoke-llm.py -c run.toml                   # run from config
invoke-llm.py -c run.toml --dry-run         # print matrix shape, don't execute
invoke-llm.py -c run.toml --json            # JSONL output to stdout
```

`-c` is mutually exclusive with single-shot flags. `--dry-run` requires `-c`.

### TOML schema

```toml
[generation]
model = "claude-sonnet-4-6"          # scalar = fixed, array = sweep
temperature = 1.0                     # array → sweep dimension
max_tokens = 4096

[[prompts]]
role = "system"                       # "system" or "user"
file = ["strict.md", "relaxed.md"]    # array = sweep dimension
# OR: prompt = "inline text"          # file and prompt are mutually exclusive

[[prompts]]                           # multiple same-role entries = concatenation
role = "user"
file = "question.md"

[output]
file = "results.jsonl"                # optional JSONL output
```

Matrix = cartesian product of all array values across `[generation]` and `[[prompts]]`. File paths resolve relative to the TOML file's parent directory.

### Example: matrix sweep

```toml
[generation]
model = ["claude-sonnet-4-6", "gpt-5-mini"]
temperature = [0.0, 0.5, 1.0]

[[prompts]]
role = "system"
file = ["strict.md", "relaxed.md"]

[[prompts]]
role = "user"
file = "question.md"

[output]
file = "results.jsonl"
```

2 models × 3 temps × 2 system prompts = 12 runs. Per-run errors are recorded without aborting. Summary table prints to stderr after completion.

Requires `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY` environment variables.
