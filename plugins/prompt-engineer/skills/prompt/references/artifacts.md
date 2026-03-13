# Prompt Artifacts

Guidance for writing specific types of prompt-adjacent files.

## Always-Included Content

Empirical findings on prompt fragments that are injected into every conversation (system prompts, AGENTS.md, CLAUDE.md, skill descriptions, etc.):

- **Redundancy hurts.** Content restating what End AI already knows increases reasoning tokens 10-22% without improving outcomes. When existing documentation is removed, the same content helps — the harm is duplication, not the content itself.
- **Overviews are inert.** Codebase summaries, architectural overviews, and broad style guides do not help End AI reach relevant files faster or complete tasks better.
- **Instructions add compliance overhead.** Every directive competes for End AI's reasoning budget — producing more tool calls, more file traversal, and more reasoning tokens.
- **Auto-generation is net-negative.** LLM-generated always-included content reduced success rates in 5/8 tested settings and increased cost 20-23%. Human-written content improved success +4% — but only when minimal.
- **Include only non-discoverable, task-critical content.** Repo-specific tooling requirements, non-obvious test commands, operational landmines. Short, human-written, pruned aggressively.

## AGENTS.md Files

Repo-embedded prompt fragments scoped by directory.

### Structure

- First heading: `## AGENTS.md for <project name>` (root) or `## AGENTS.md for \`<path>/\`` (nested).
- Write in direct imperatives — no introductory text before or after the heading.
- Nested files supplement the parent for their subtree.

### Content

Include only non-discoverable information — things not obtainable from repo contents alone:

- Architectural intent, design rationale, non-obvious component relationships.
- Tooling gotchas, non-obvious conventions, operational landmines, external references.
- When tools are involved, state whether End AI defaults to acting or informing — this is not inferred from context.
- NOT directory layout, tech stack, or other repo-inferable facts.

Mark plans distinctly from current-state descriptions (e.g., `TODO`/`PLANNED` labels, or a dedicated section).

When a subdirectory has its own `AGENTS.md`, list its path and brief purpose in the parent — don't duplicate its content.

### Empirical Evidence

From "Evaluating AGENTS.md" (ICML) — findings not already covered in Always-Included Content:

- Tool/command mentions in context files dramatically increased usage of those tools, even when unnecessary.
- Developer-written files improved success +4% but still increased steps and cost — confirming that even helpful content has overhead.

### Maintenance

Prune aggressively — stale directives mislead worse than missing ones.

## Agent Skills

Guidance for writing `SKILL.md` files following the [Agent Skills](https://agentskills.io) open standard.

### Progressive Disclosure

Skills load in three tiers — structure accordingly:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup for all skills.
2. **Instructions** (< 5000 tokens recommended): Full `SKILL.md` body loaded on activation.
3. **Resources** (as needed): Files in `scripts/`, `references/`, `assets/` loaded only when required.

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files. Keep file references one level deep from `SKILL.md` — avoid nested reference chains.

### Descriptions

The `description` field carries the entire burden of triggering. Max 1024 characters.

- Write in third person ("Processes Excel files", not "I can help you" or "You can use this").
- Focus on user intent, not implementation mechanics.
- Include both what the skill does and when to use it, including non-obvious trigger contexts.
- Be specific: "Helps with documents" fails; "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction" works.
- Err on the side of being pushy — agents tend to under-trigger rather than over-trigger. Explicitly list contexts where the skill applies, including when the user doesn't name the domain directly.

#### Optimizing Descriptions

To systematically improve triggering:

1. Create 20 eval queries (8-10 should-trigger, 8-10 should-not-trigger) with realistic user phrasing, file paths, personal context, and varying formality.
2. Should-trigger queries: vary phrasing, explicitness, detail, and complexity. Most valuable are cases where the skill would help but the connection isn't obvious.
3. Should-not-trigger queries: focus on near-misses that share keywords but need something different. "Write a fibonacci function" is too easy — "write a python script that reads a csv and uploads rows to postgres" (involves CSV but needs ETL, not analysis) is a real test.
4. Split 60% train / 40% validation. Optimize against train, measure generalization on validation.
5. Avoid adding specific keywords from failed queries — find the general category those queries represent. If stuck after several iterations, try a structurally different description rather than incremental tweaks.

### Degrees of Freedom

Match specificity to task fragility:

- **High freedom** (text instructions, general direction): Multiple valid approaches, context-dependent decisions.
- **Medium freedom** (pseudocode, parameterized scripts): Preferred pattern exists, some variation acceptable.
- **Low freedom** (exact scripts, no modification): Fragile operations, consistency critical, specific sequence required.

### Claude Code Frontmatter

Claude Code extends the Agent Skills standard with additional frontmatter fields:

| Field | Effect |
|---|---|
| `disable-model-invocation: true` | Only user can invoke via `/name`. Use for side-effect workflows (deploy, send messages). |
| `user-invocable: false` | Only the model can invoke. Use for background knowledge that isn't a meaningful user action. |
| `context: fork` | Run in an isolated subagent. Skill content becomes the task prompt — must contain explicit instructions, not just guidelines. |
| `agent` | Which subagent type to use with `context: fork` (e.g., `Explore`, `Plan`, `general-purpose`). |
| `allowed-tools` | Tools the model can use without permission prompts when this skill is active. |
| `model` | Model override when this skill is active. |
| `argument-hint` | Autocomplete hint (e.g., `[issue-number]`). |

### Scripts in Skills

When a task repeatedly requires the same deterministic logic, bundle a script in `scripts/` rather than letting each invocation reinvent it.

- Use self-contained scripts with inline dependencies (PEP 723 for Python, `npm:` imports for Deno).
- Avoid interactive prompts — agents run in non-interactive shells.
- Provide `--help` output, structured output (JSON/CSV over free-form text), and helpful error messages.
- Separate data (stdout) from diagnostics (stderr).
- Design for idempotency — agents may retry.
