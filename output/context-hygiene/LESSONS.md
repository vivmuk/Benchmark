# Context Hygiene — Extracted Lessons

## Sources
1. Slide: Context Hygiene (Brandon Li) — Less is more checklist + links
2. HumanLayer: Writing a good CLAUDE.md / AGENTS.md
3. IFScale: How Many Instructions Can LLMs Follow at Once? (arXiv:2507.11538)
4. LongBench v2 (arXiv:2412.15204)
5. Anthropic Claude Code memory + best practices

## Key empirical lessons
- Instruction-following degrades as instruction density rises; even strong frontier models only ~68% at 500 simultaneous instructions (IFScale).
- Smaller / non-reasoning models degrade faster than large reasoning models.
- Models bias toward earlier (and often later) instructions; middle rules get lost.
- Adding more always-on rules can reduce adherence to *all* rules, not just the new ones.
- Long context benchmarks (LongBench v2) show deep understanding over huge contexts is still hard; more tokens ≠ free intelligence.
- Always-on files are loaded every session and are highest leverage — keep them short and universal.
- Progressive disclosure (skills/docs on demand) beats stuffing procedures into root instructions.
- Sessions are effectively stateless; durable knowledge must be written to files.
- Context compaction (summaries + pointers) beats carrying raw history forever.
- Prefer deterministic tools (linters/tests/hooks) over LLM-as-style-police.

## Operating rules to teach agents
1. Always-on ≤ ~100 lines, universal only
2. Move depth to skills/docs with a short index
3. Write durable memory to files
4. Compact long threads into a Context Card
5. Guard the instruction budget; no duplicate paraphrases
6. Verify with commands/artifacts before claiming done

## Artifacts
- Infographic: `context-hygiene-infographic.png`
- Skill proposal: Skill Workshop `context-hygiene` (pending apply)
