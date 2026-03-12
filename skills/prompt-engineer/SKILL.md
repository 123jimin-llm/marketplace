---
name: prompt-engineer
description: Draft and revise LLM prompts, system prompts, AGENTS.md, and Agent Skills. Use when writing, reviewing, or debugging any AI instructions.
---

# Prompt Engineering

## Terms

- **Dev AI**: AI drafting the prompt from human intent.
- **End AI**: AI executing the prompt. Same or different model, no shared context with Dev AI.
- **Baseline**: What End AI produces unprompted. The starting point — not the enemy.
- **Prompt**: Self-contained directives for End AI.
- **Performance**: How well End AI output matches intended outcome.

## Writing Principles

### 1. Discovery

Surface intended outcome before drafting.

- When intent is vague, probe for the actual goal — ask why, not what.
- Collect failure samples: examples of undesirable End AI output reveal Baseline gaps the Prompt must address.
- Stop when intent is clear, not when all questions are asked.

### 2. Goal & Context

Define intended outcome (not just format), then supply info End AI would otherwise guess or miss.

- Check Baseline first — restating it wastes tokens and anchors toward generic output.
- Persona, domain, audience traits: include only what serves Performance.
- An Anchor Metaphor can guide End AI across undefined scenarios, but has near-zero effect on specific constraints — use Constraints for precision.

### 3. Constraints

Add only where Baseline deviates from intended outcome. Match enforcement to type:

- **Ordering/procedure** → Numbered steps or arrow chains. Strongest enforcement, but suppresses flexibility — use when ordering matters; prefer Goal & Context when it doesn't.
- **Pattern calibration** → NO/YES example pairs.
- **Behavioral** → Directive verbs ("Emit structured logs"), not permissive declarations ("Structured logging is preferred").
- **Rationale-backed** → State why concretely ("Output is parsed by CI"), not abstractly ("This improves quality"). End AI generalizes better from concrete reasons.

Excessive constraints suppress creativity in open-ended tasks. Specify minimum rules, then leave room.

### 4. Clarity

Precise structure over verbose explanation; precise words over vague ones.

- Numbered steps for ordering, lists for parallel items, arrow notation for sequences.
- Re-read without authorial context. Simulate End AI's literal reading: if an instruction can be plausibly misread, it will be.
- Test key terms against boundary cases — rephrase unclear terms. Verify examples do not narrow or widen the parent term past intent.
- Compression amplifies syntactic ambiguity. Many short words are noun-verb homographs — ensure sentence structure forces the intended part of speech.

### 5. Anti-Pattern

Ban recurring quality-degrading patterns with concrete replacement behaviors.

- Default to positive directives. Escalate to explicit bans only for persistent behaviors (surviving 2+ revision cycles).
- Target the sneaky variant — End AIs comply with the letter while violating the spirit through modifiers, cause-chains, and synonyms.
- One NO/YES pair often outperforms extensive explanation for style/tone/pattern goals.
- A ban without a replacement creates avoidance, not improvement.

### 6. Validation

Test against diverse scenarios, then revise.

- A single test hides most failure modes. Minimum: three scenarios stressing different aspects.
- Distinguish harmful violations from harmless ones; stop when marginal gain falls below marginal complexity.
- First revision captures most improvement. Recognize diminishing returns.

## Token Economy

Optimize token density for Performance — maximum signal-to-noise, not minimum length.

Priority: **Performance >= Meaning > Length**

1. **Merge**: Combine redundant expressions.
2. **Prune**: Remove Baseline-restating instructions and instructions whose removal improves output. Compression must not weaken enforcement (directive → descriptive), lose high-impact directives, or distort scope (task-specific promoted to universal).
3. **Select**: Omit examples if explanation suffices. Exception: one NO/YES pair often beats explanation for style/tone/pattern goals. For novel task patterns, broader example sets beyond single pairs may be warranted.
4. **Structure**: Lists over prose. Numbered steps for ordering. Skip if causality is lost.
5. **Encoding**:
   - Prefer ASCII where meaning is preserved.
   - Avoid markdown emphasis unless semantically essential. Use hierarchy and list ordering for emphasis.
   - Write in End User's language despite English being more token-efficient — prevents output leakage.
   - Never compress past potential misinterpretation — End AI reads compressed phrasing more literally than Dev AI intends.

## Design Notes

Non-procedural rationale supplementing the principles above.

- **Context > Persona**: Contextualizing viewpoint and knowledge beats "You are..." declarations. If persona is core to the outcome, reinforce via mindset and behavior patterns, not role labels.
- **Format Synchrony**: End AI leaks the Prompt's tone, format, and style into output. The prompt *is* a style example whether you intend it or not.
- **Inducing Thought**: Guide reasoning via Goal, Context, Metaphor — not procedural chain-of-thought. Numbered steps maximize compliance but rigidify reasoning.
- **Iterative Convergence**: First revision captures most improvement. At some point, gains come from revising test scenarios or task framing, not the prompt.
- **Model Capability Matching**: Reasoning models perform best with high-level goals, concise context, and room to determine approach. Instruction-following models benefit from explicit steps and detailed constraints. Applying heavy procedural constraints to a reasoning model degrades output — tokens spent on compliance are tokens not spent on problem-solving. When model type is unknown, default to reasoning-model assumptions.

## References

- [references/creative.md](references/creative.md) — Narrative fiction, roleplay, chatbot persona, aesthetic output. Load when the prompt's output is *experienced* rather than consumed.
- [references/artifacts.md](references/artifacts.md) — Writing AGENTS.md files, Agent Skills (SKILL.md), and always-included context files. Load when creating or reviewing prompt artifacts.
- [references/meta-note.md](references/meta-note.md) — Empirical observations on prompt engineering patterns. For meta-improving this skill; not for normal prompt-engineering work.
