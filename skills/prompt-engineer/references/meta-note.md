# Meta-Note on Prompt Engineering

Empirical observations from iterative prompt engineering work. For self-improvement of the prompt-engineer skill — not reference material for normal prompt-engineering tasks.

---

**1. The user's true intent is rarely their first request.** A request for "vivid description" often means "immersive storytelling with character-driven pacing." The surface request describes a symptom; the underlying intent is structural. Expect the real goal to emerge over multiple feedback rounds.

**2. Enforcement mechanisms are not interchangeable.** Same principle, dramatically different compliance depending on structural presentation. Ranked for behavioral constraints:

- Numbered sequences / arrow chains: Strongest. Treated as executable procedures.
- Concrete example pairs (NO/YES): Strong. Calibrates pattern-matching.
- Intensifier language ("always," "never," "must"): Increases compliance but rigidifies output.
- Formatting emphasis (bold, headers, caps): Weak. Not reliably interpreted as behavioral priority.
- Metaphorical framing: Near-zero for specific constraints. Useful only for high-level reasoning.

**3. Over-specification suppresses creativity.** Detailed sub-categories and checklists get treated as inventories to fill. Condensed core principles produce freer generalization. Mechanism: finite reasoning budget — tokens parsing instructions are tokens not spent on creative problem-solving.

**4. "You may" and "You must" produce entirely different behavior.** Describing a tool as "important" or "available" does not ensure use. "Dialogue is a key means of characterization" → no dialogue. "Give characters dialogue" → dialogue. For expected behavior, use imperative verbs.

**5. Anti-patterns should target the subtle violation.** Banning "don't state emotions before physical description" stops "she looked angry" but produces "with anger, her fist clenched." Model the sneaky version the AI would actually produce.

**6. Principles have systemic effects beyond their stated scope.** A pacing principle also improved character personality, emotional depth, and immersion. Conversely, a principle preventing narrator editorializing also suppressed dialogue and internal monologue. Evaluate by systemic impact, not stated intent.

**7. Persistent habits require explicit bans.** Some behaviors survive any amount of positive guidance. When a behavior persists through 2+ revision cycles, stop guiding implicitly and ban explicitly.

**8. Condensing a prompt can improve output quality.** Reducing sixteen lines to eight — preserving core principles — produced better output on the same scenarios. Instructions restating default behavior dilute attention to instructions that actually matter.

**9. One well-chosen example outperforms extensive explanation.** For qualitative goals, a single NO/YES pair consistently outperformed multi-sentence explanations. Pattern-matching is more reliable than interpretation for subtle distinctions.

**10. Test with diverse scenarios.** Three different scenarios revealed three different failure modes from the same prompt. Any single scenario hides the majority of issues.

**11. Revision has diminishing returns.** First cycle captures the majority of improvement. By the fourth, changes are incremental.

**12. Reasoning models and instruction-following models need different prompting.** Heavy procedural constraints on a reasoning model degrade output — the model spends its reasoning budget on compliance. When model type is unknown, default to reasoning-model assumptions.

**13. Tool use defaults must be set explicitly.** Whether the AI defaults to acting or informing is not reliably inferred from context. When a prompt involves tools, state the default posture directly.

## Open Questions

- Hierarchical grouping: most effective way to communicate hierarchy in prompts? Candidates: XML tags, Markdown headers, indentation, numbered nesting. May differ by model family or context window position.
- NO/YES example placement: group in a dedicated section, or place inline next to the calibrated instruction? Trade-off between global readability and local enforcement strength.
