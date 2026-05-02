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

## Running locally

Full stack (FastAPI bridge + Barista frontend) with one command:

```bash
./scripts/dev.sh
```

First run bootstraps everything that's missing — Python venv (prefers `uv`,
falls back to stdlib `venv`), `[service,dinov2]` deps, Playwright Chromium,
the cellar baseline embeddings (12 captures, ~3 min), and `barista/node_modules`.
Subsequent runs skip straight to launch. Ctrl+C stops both servers cleanly.

Open the Vite URL it prints (default `http://localhost:5173/`). The URL
input in the top-right calls the FastAPI bridge at `http://localhost:8000`
by default; override with `barista/.env.local` (`VITE_TASTE_API_URL=…`)
to point at a teammate's machine, an ngrok tunnel, or a deploy.

Other entry points (no orchestrated stack needed):
- `python -m milkshake taste --url <URL>` — URL → Ingredients JSON to stdout
- `python -m photographer baseline build [--embedder histogram|dinov2]` — rebuild the cellar baseline
- `python scripts/smoke_taste_url.py` — gold + gunk + failure-mode end-to-end check
- `python3 scripts/bake_barista_presets.py` — refresh the static cellar presets in Barista's preset picker

Full README at the repo root has the longer version (overrides, model
licensing, failure modes).
</INSTRUCTIONS>
