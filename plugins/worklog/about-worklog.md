# About Worklog

## Definition

- **Spec**: What the system should do. Immutable except through tasks.
- **Plan**: A work proposal targeting specs. Lifecycle: draft → approved → active → archived/abandoned.
- **Task**: A unit of work implementing a plan and/or modifying specs. Lifecycle: pending → active → done → archived.
- **Worklog**: A flat-file directory (`spec/`, `plan/`, `task/`, `archive/`) of these items, stored as Markdown with TOML frontmatter. Repo-local, git-versioned, operated primarily by an LLM agent.

## Principles

### 1. Specs are the source of truth, not code

Code that diverges from a spec is a bug. The response is to fix the code or amend
the spec through a task — not to silently accept drift.

### 2. Write specs from plans, not from code

Deriving specs from code risks encoding bugs as requirements. Specs are written
from the plan's intent, then updated through tasks as implementation reveals
necessary deviations.

### 3. Lifecycle transitions are decision points

Each transition forces a question: approval asks "is this worth doing?", marking a
task done asks "did we update the specs to match what we actually built?", archiving
a plan asks "are all implementing tasks finished?" Skipping a transition skips the
question.

### 4. Convention-enforced, not system-enforced

Nothing prevents you from editing a spec without a task or archiving with `mv`.
`validate.py` detects violations after the fact; `archive.py` enforces status checks
and cleans cross-references during archiving. Neither can prevent violations — only
catch them. The system is only as reliable as its operator.

---

## Common Pitfalls

### Skipping the plan lifecycle

Going straight from "idea" to "task" without a plan, or creating tasks against a
`draft` plan that was never approved. Small reactive work can skip plans, but
anything touching specs should go through the full lifecycle. The failure mode is
building the wrong thing and only discovering it at spec-update time.

### Forgetting to update specs after implementation

The task is `done`, the plan is archivable, but the specs still say TBD in three
sections. Implementation decisions that deviated from the plan need to be reflected
back into specs *before* archiving. Once a plan is archived, the context for why
you deviated is buried.

### Writing specs from code

This is the inverse of principle #2 and it's the most insidious pitfall. After
implementation, it's tempting to just read the code and transcribe what it does
into a spec. This encodes bugs as requirements and loses the "why."

### Using `mv` to archive

Bypasses status validation and cross-reference cleanup. The archived item's ID
stays in `blocked_by` fields of active items, and those items remain incorrectly
blocked. Always use `archive.py`.

### Not cleaning `blocked_by` when blockers complete

If you complete a task but don't archive it promptly (or archive it with `--force`
while it's not `done`), downstream items stay blocked. `archive.py` handles this
automatically for properly-completed items, but abandoned items require manual
cleanup.

### Letting completed plans rot

A plan whose tasks are all done is just noise in the active directory. Archive it.
`validate.py` will flag these as "archivable plans" but only if you run it.

### Logging false mistakes

When reviewing your own work, it's tempting to note every potential issue as a
"mistake." Non-mistakes recorded as mistakes are noise that erodes trust in the
mistake log. Only log things that were actually wrong and that you'd do differently.

---

## Current Issues (v0.1.2)

### No enforcement, only convention

The system relies entirely on operator discipline (human or LLM). Nothing prevents
you from editing a spec directly without a task, creating a task against a draft
plan, or archiving with `mv`. The scripts validate and assist but cannot enforce.
This is a design choice (flat files, no daemon), but it means the system is only as
reliable as its operator.

### Spec "immutability" is aspirational

Specs are described as immutable (only modifiable through tasks), but there is no
mechanism — not even a validation check — that detects direct spec edits outside of
a task context. A determined or careless operator can edit specs freely.

### No script-level tests

The quiz system tests LLM comprehension of worklog concepts, but the Python scripts
themselves (`archive.py`, `validate.py`, etc.) have no unit or integration tests.
A bug in `archive.py`'s cross-reference cleanup would silently corrupt worklog
state.

### Scripts are copied, not linked

`init-worklog.py` copies scripts into each repo's `worklog/script/` directory.
When the plugin's scripts are updated, existing repos keep stale copies. There is
no update mechanism — you'd have to re-run init or manually replace files.

### `updated_by` deprecation is incomplete

The field is deprecated in favor of `find-refs.py`, but existing worklogs may still
contain it. `validate.py` warns about it but doesn't auto-remove it. The migration
path is manual: notice the warning, delete the field.

### No spec archiving lifecycle

Plans and tasks have clear archive criteria (done/abandoned + all downstream
complete). Specs can be archived but there's no defined trigger for when a spec
*should* be archived. A spec that no active plan targets and no active task
modifies might be archivable — but `validate.py` doesn't flag this.

### Tag management is entirely manual

`tags.md` is a flat list with no tooling to add, remove, or audit tags. There's no
validation that tags used in frontmatter actually exist in `tags.md`, and no way to
find unused tags. Tags are effectively free-text with a suggested vocabulary.

### No validation gate between plan approval and spec creation

Plans declare `targets` (specs to create or modify), but nothing checks that those
specs actually exist before the plan moves to `active` or tasks begin. Agents
routinely start implementation without ever creating the targeted specs.

### Tests have no worklog representation

Tests are not a worklog concept — no directory, no item type, no cross-reference
field, no lifecycle step. Agents write tests after implementation using the code as
reference, coupling tests to implementation details rather than spec behavior.

### No distinction between specs and user-facing documentation

Specs contain TOML frontmatter, worklog IDs, and cross-references — they are not
user-readable. There is no `docs/` directory or mechanism to produce user-facing
documentation from specs.
