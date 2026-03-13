---
name: playground
# NOTE: For this skill, brevity of description is preferred over false-negative trigger.
description: Scaffold prompt playgrounds; test variations across inputs, score outputs.
---

# Playground

A directory for evaluating and improving prompts against inputs.

## Structure

```
<playground>/
├── config.toml              # Generation and composition settings
├── task.md                  # Goal, evaluation criteria, constraints (free-form markdown)
├── prompts/
│   └── <slot>/              # Named slot ("main", "system", "critic", …)
│       ├── config.toml      # { default = "base" }
│       └── <variation>.md   # Freeform name ("base", "concise", "v2")
├── inputs/
│   └── <case>.md            # One file per test case; stem = case name in outputs
└── outputs/
    └── <run-label>/         # Human-chosen ("baseline", "concise-v2", …)
        ├── run.toml         # Standalone invoke-llm TOML (see invoke-llm skill)
        └── <case>.md        # LLM output; YAML frontmatter for eval
```

## Scaffold

Ask user for: directory path, task description, prompt slots (default: single `main`), initial inputs. Create `config.toml`, `task.md`, one variation per slot, and inputs. Do NOT create `outputs/`.

### config.toml

```toml
[generation]
model = "claude-sonnet-4-6"
temperature = 1.0
max_tokens = 4096

[composition]
separator = "\n\n"   # join between parts; inherited by each message
substitute = false   # true → replace {{input}} in part text; "inputs" in parts becomes [vars]

# Single-message mode (cannot coexist with [[composition.messages]]):
parts = ["prompts/main", "inputs"]
# role = "user"      # default

# Multi-message mode:
# [[composition.messages]]
# role = "system"
# parts = ["preamble.md", "prompts/main"]
#
# [[composition.messages]]
# role = "user"
# parts = ["prompts/main"]
# substitute = true
```

Paths resolve relative to playground root. Directory paths (e.g., `"prompts/main"`) resolve to the selected variation at run time. `"inputs"` resolves to the current test case.

### Frontmatter

All `.md` files support optional YAML frontmatter. Frontmatter is stripped before LLM calls.

- `prompts/*/*.md`, `inputs/*.md`: `comments:` (free-form note).
- `outputs/*/*.md`: `score:` (1–5, scale/criteria from `task.md`), `comments:`.

## Run

```
scripts/playground-run.py <playground-dir> -l <run-label> [-v SLOT=VAR,...] [-i PATTERN] [--dry-run] [--json]
```

| Flag | Description |
|------|-------------|
| `<playground-dir>` | Positional. Path to playground root. |
| `-l` / `--label` | Run label. Required unless `--dry-run`. |
| `-v` / `--variation` | Slot variations. Repeatable. `-v main=base,concise` sweeps both. `-v main=*` sweeps all `.md` in slot. Omitted slots use default. |
| `-i` / `--inputs` | Filter inputs by name pattern. Default: all. |
| `--dry-run` | Print generated TOMLs to stdout, don't execute. |
| `--json` | Include metadata (tokens, latency) in output frontmatter. |

**Output:** Single combo → `outputs/<label>/<case>.md` + `run.toml`. Multiple combos → `outputs/<label>/<combo-label>/` subdirs.

## Evaluate

Score outputs by editing their YAML frontmatter (`score:`, `comments:`).
