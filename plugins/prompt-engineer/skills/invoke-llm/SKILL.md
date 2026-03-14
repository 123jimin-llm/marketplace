---
name: invoke-llm
description: "Run prompts against LLMs. Trigger on: test/send/invoke a prompt, get a completion, compare models, matrix sweep, batch-test prompts."
---

# Invoke LLM

Script: `scripts/invoke-llm.py`

Raw LLM API calls (text in, text out). No tool use, no agent context, no skills.

Prefer TOML config mode over multiple script invocations — a single matrix run handles sweeps, produces structured output, and avoids repeated shell calls.

## Single-shot mode

```bash
invoke-llm.py "What is the capital of France?"
invoke-llm.py "Write a haiku" -s "You are a poet"
invoke-llm.py -U prompt.md -S system.md -o output.md
invoke-llm.py -S role.md -S rules.md -U context.md -U question.md
invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --json
invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --toml
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
| `--toml` | TOML output with metadata (response, model, tokens, latency, stop_reason) |

`--json` and `--toml` are mutually exclusive. Repeatable flags join with `"\n\n"`. When combining `-u`/`-U` (or `-s`/`-S`), strings come before file contents.

## TOML config mode

```bash
invoke-llm.py -c run.toml                   # run from config
invoke-llm.py -c run.toml --dry-run         # print matrix shape, don't execute
invoke-llm.py -c run.toml --json            # JSONL output to stdout
invoke-llm.py -c run.toml --toml            # TOML output to stdout
```

`-c` is mutually exclusive with single-shot flags. `--dry-run` requires `-c`.

### TOML schema

```toml
# Used with prompt-engineer:invoke-llm skill.
[generation]
model = ["claude-sonnet-4-6", "gpt-5-mini"]   # scalar = fixed, array = sweep
temperature = [0.0, 0.5, 1.0]
max_tokens = 4096
separator = "\n\n"                    # join between same-role entries; default "\n\n"

[vars]
input = "inputs/case1.md"            # named file refs, content read at runtime

[[prompts]]
role = "system"                       # "system" or "user"
file = ["strict.md", "relaxed.md"]    # array = sweep dimension

[[prompts]]
role = "user"
prompt = "inline text"                # use file or prompt, not both

[[prompts]]                           # multiple same-role entries = concatenation
role = "user"
file = "question.md"
substitute = true                     # replace {{key}} placeholders with [vars] content
separator = "\n---\n"                 # per-entry override (join point before this entry)

[output]
file = "results.jsonl"
```

**Comments:** Start config files with `# Used with prompt-engineer:invoke-llm skill.` so they're identifiable as inputs to this skill.

Matrix = cartesian product of all array values across `[generation]` and `[[prompts]]`. Above example: 2 models × 3 temps × 2 system files = 12 runs.

**Path resolution:** All file paths (`file`, `[vars]`, `[output].file`) resolve relative to the TOML file's parent directory. If `run.toml` is in `project/tests/`, then `file = "../src/prompt.md"` resolves to `project/src/prompt.md`.

Per-run errors are recorded without aborting. Summary table prints to stderr after completion. Requires `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`.
