---
name: playground
description: Scaffold prompt playgrounds; test variations across inputs, score outputs.
---

# Playground

A directory for evaluating and improving prompts against inputs. One playground = one task.

## Structure

```
<playground>/
├── config.toml              # Generation defaults
├── task.md                  # Goal, evaluation criteria, constraints
├── prompts/
│   └── <slot>/              # Named slot ("main", "system", "critic", …)
│       └── <variation>.md   # Freeform name (e.g., "base", "concise", "v2")
├── inputs/
│   └── <case>.md
└── outputs/
    └── <run-label>/         # Human-chosen ("baseline", "concise-v2", …)
        ├── run.toml
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
```

### task.md

Free-form markdown: goal, evaluation criteria, constraints.

### Prompts

Plain markdown. Input is appended after the prompt.

### Inputs

One file per test case. Filename (without extension) = case name in outputs.

## Run

For each (prompt-combination × input), invoke `invoke-llm.py` from the `invoke-llm` skill:

```bash
python ../../invoke-llm/scripts/invoke-llm.py \
  -S prompts/system/<variation>.md \
  -U prompts/main/<variation>.md \
  -U inputs/<case>.md \
  -m <model> -t <temperature> --max-tokens <max_tokens> --json \
  -o outputs/<run-label>/<case>.md
```

System-prompt slots use `-S`; all others use `-U`. Input is always the final `-U`.

After all cases, write `run.toml`:

```toml
[generation]
model = "claude-sonnet-4-6"
temperature = 1.0
max_tokens = 4096

[prompts]
system = "base"
main = "concise"
```

## Evaluate

Score output files by adding YAML frontmatter:

```yaml
---
score: 4
comments: Good structure but too verbose in paragraph 2.
---
```

Scale and criteria come from `task.md`. Default: 1–5.

## Compare

Read outputs across runs for the same cases. Present side-by-side summary with scores as a markdown table.
