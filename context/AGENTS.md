<INSTRUCTIONS>
## The Taste Engine (Hackathon 2026)
Goal: quantify the subjective “quality” of web UIs and render it as a tangible visual metaphor: a **Virtual Milkshake**.

This repo is built around a 3-tier pipeline, designed so different people (and their coding agents) can implement each tier independently.

### Quick map
- **Photographer**: URL → screenshot + embedding
- **Sommelier**: embedding → principal components → Ingredients JSON (+ debug)
- **Barista**: Ingredients JSON → real-time milkshake visualization

Read these docs before starting work on a tier:
- `context/ARCHITECTURE.md` (system flow + boundaries)
- `context/DATA_CONTRACTS.md` (the interfaces; treat as source of truth)
- `context/ROLE_PHOTOGRAPHER.md`, `context/ROLE_SOMMELIER.md`, `context/ROLE_BARISTA.md` (ownership + DoD)
- `context/AGENT_PROMPTS.md` (copy/paste prompts for setting up a coding agent)
- `context/VOCAB.md` (canonical strings for flavors/textures/assets)

## Project principles
- **Relativity over absolutes**: scores are only meaningful relative to the baseline “Gold (Senior)” vs “Gunk (Bad)” poles.
- **Hard separation of concerns**:
  - Photographer does ingestion + vectorization only.
  - Sommelier does math + mapping only.
  - Barista does visuals only (no scoring logic).
- **Demo-first**: prefer an end-to-end path that works on 3–10 example URLs, even if “smart” parts are v0.

## Non-goals (hackathon scope)
- Perfect “objective” UI taste.
- Production-grade crawling, auth, or bot evasion.
- Large-scale dataset management.
</INSTRUCTIONS>
