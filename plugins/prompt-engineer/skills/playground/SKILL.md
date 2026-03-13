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
├── task.md                  # Goal, evaluation criteria, constraints
├── prompts/
│   └── <slot>/              # Named slot ("main", "system", "critic", …)
│       ├── config.toml      # Slot config (default variation)
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

[composition]
separator = "\n\n"   # default join between parts
substitute = false   # default; when true, replace {{input}} in part text

# Single-message mode (parts/role cannot coexist with [[composition.messages]]):
parts = ["prompts/main", "inputs"]
# role = "user"      # default

# Multi-message mode:
# [[composition.messages]]
# role = "system"    # required
# parts = ["preamble.md", "prompts/main"]
#
# [[composition.messages]]
# role = "user"      # required
# parts = ["prompts/main"]
# substitute = true  # {{input}} in prompts/main replaced with input content
```

#### Composition

Assembles prompt variations and inputs into LLM messages. Paths resolve relative to playground root; directories resolve to the selected variation/case at run time.

- **`parts`** — ordered list of paths. `"inputs"` is reserved (resolves to current test case; do not use as a prompt slot name).
- **`role`** — `"user"` (default at root) | `"system"` | `"assistant"`. Required in `[[composition.messages]]`.
- **`separator`** — string between parts. Default `"\n\n"`.
- **`substitute`** — replace `{{input}}` in part text with input content; `"inputs"` in `parts` is ignored.
- Root-level `separator` and `substitute` are defaults inherited by each message.
- `parts`/`role` (single message) and `[[composition.messages]]` cannot coexist.

### task.md

Free-form markdown: goal, evaluation criteria, constraints.

### Prompts

Each slot has a `config.toml`:

```toml
default = "base"
```

### Frontmatter

Prompts, inputs, and outputs support optional YAML frontmatter (all fields optional).

`prompts/*/*.md` and `inputs/*.md`:

```yaml
---
comments: Free-form note on purpose or intent.
---
```

`outputs/*/*.md`:

```yaml
---
score: 4
comments: Good structure but too verbose in paragraph 2.
---
```

Scale and criteria come from `task.md`. Default: 1–5.

### Inputs

One file per test case. Filename (without extension) = case name in outputs.

## Run

(TODO)

## Evaluate

Score outputs by editing their YAML frontmatter (see Frontmatter above).

## Compare

Read outputs across runs for the same cases. Present side-by-side summary with scores as a markdown table.
