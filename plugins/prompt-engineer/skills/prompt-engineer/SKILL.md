---
name: prompt-engineer
description: This skill should be used when the user asks to "write a prompt", "shorten a prompt", "review my system prompt", "debug prompt output", "write a SKILL.md", "review my CLAUDE.md", or "write an AGENTS.md". Drafts, revises, and debugs LLM instructions and prompt artifacts.
---

# Prompt Engineering

## Terms

- **Prompt**: Directives for End AI.
- **Dev AI**: AI drafting Prompt from human intent.
- **End AI**: AI executing Prompt. No shared context with Dev AI.
- **Baseline**: What End AI produces unprompted.
- **Performance**: How well End AI output matches intent.

## Process

1. **Baseline** — run the task with minimal or no Prompt. Note divergences from intent.
2. **Draft** — add only what moves End AI toward intent. Load <references/creative.md> for fiction, roleplay, or persona work, or <references/artifacts.md> for files that contain prompts, before drafting.
3. **Cold-read** — re-read Prompt as End AI, without authorial context. Every term, abbreviation, and compressed phrase that depends on Dev AI's intent to parse correctly will be misinterpreted.
4. **Test** — minimum three diverse scenarios. Revise Prompt, then stop when marginal gain < marginal complexity.

## Principles

Ordered by impact. Priority: **Performance >= Meaning > Length**.

1. Removing Baseline-restating or redundant instructions improves output — noise dilutes attention, including in markup and formatting. When in doubt, cut.
2. Define intended outcome, not output format. Describe viewpoint and knowledge End AI needs, not role labels. Supply only what End AI would guess or miss.
3. Use imperative verbs ("Emit structured logs"), not declarations ("Structured logging is preferred").
4. State concrete reasons ("Output is parsed by CI"). End AI generalizes better from concrete rationale.
5. Select the lightest enforcement that works: explanation alone → one NO/YES pair → numbered steps. Each level gains compliance but costs flexibility. Reasoning models degrade under heavy procedural constraints — default to lighter enforcement when model type is unknown.
6. Prompt leaks its own tone, format, and style into output. Write Prompt in the style you want End AI to produce.
7. Every constraint competes for End AI's reasoning budget. Constraints affect behavior beyond their stated scope — evaluate by systemic impact.
8. Ban the sneaky variant — End AI complies with the letter via modifiers, cause-chains, and synonyms. Pair every ban with a replacement behavior.

## References

- <references/creative.md> — Fiction, roleplay, persona, aesthetic output.
- <references/artifacts.md> — AGENTS.md, Agent Skills, always-included context files.
- <references/meta-note.md> — Empirical observations for meta-improving this skill.
