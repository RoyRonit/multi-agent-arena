# The Roundtable

A persona-based multi-agent **debate arena**. You paste a marketing brief; five specialist
AI personas argue it across rounds with a live **budget economy** and an **anti-convergence
loss** — speaking costs credits, novelty wins them back, repetition gets fined. A neutral
Chairman scores every turn and writes the final verdict.

Built to the PRD / Architecture / Frontend specs in `../files/`.

## The cast

| Agent | Role | Private incentive |
|---|---|---|
| Priya | Brand Manager | short-term hacks erode brand equity |
| Rohan | Media Manager | ideas must survive real platform mechanics |
| Sana | Scriptwriter | story/hook is the real multiplier |
| Dev | Copywriter | one killer line beats a big plan |
| Mira | Media Planner | if it fails CPM math, it dies |

Chairman (non-playing): judges rounds, allocates rewards/fines, writes the verdict.

## The game (economy)

- Everyone starts with **1000 credits**.
- A turn costs `50 + 0.1 × tokens`. Balance ≤ 0 ⇒ **muted** (grays out, skips turns).
- After each round the Chairman scores every (anonymized) turn on **Novelty / Evidence /
  Persuasion / Redundancy** and picks a winner (**+300**) and runner-up (**+100**).
- Redundancy ≥ 7 ⇒ **−100 fine**. A reward can revive a muted agent.
- All tunable via env (see `.env.example`).

## Run it locally

You need one thing: an **OpenRouter API key** (`OPENROUTER_API_KEY`).

```bash
cd roundtable
cp .env.example .env      # then paste your key into .env
./run.sh                  # backend :8000 + frontend :5173
```

Open http://localhost:5173, paste a brief, hit **Convene**.

### Manual (two terminals)

```bash
# terminal 1 — backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
OPENROUTER_API_KEY=sk-or-... ./.venv/bin/uvicorn backend.main:app --port 8000 --reload

# terminal 2 — frontend
cd frontend && npm install && npm run dev
```

## Access gate (ASCII captcha)

Set `ACCESS_PHRASE` to require a shared password before anyone can start a debate. Users see
the phrase rendered as an ASCII-art captcha they must read and type — casual visitors and bots
can't spend your OpenRouter credits. Leave it empty to run open. Optional `DAILY_DEBATE_CAP`
bounds cost even if the URL leaks.

## Deploy (single container)

```bash
docker build -t roundtable .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=sk-or-... -e ACCESS_PHRASE=ROUNDTABLE roundtable
# open http://localhost:8000  (FastAPI serves the built frontend)
```

Works on Railway / Render / Fly with the env vars above. **For Railway + a Cloudflare domain,
follow [DEPLOY.md](DEPLOY.md)** — step-by-step, including why to use a DNS-only (grey cloud)
CNAME so SSE streaming works.

## Architecture

```
backend/
  config.py       all tunables (models, economy, rounds) — env-overridable
  openrouter.py   async OpenRouter client (streaming + JSON)
  personas.py     the 5-persona pack + chairman prompts (swap file = swap domain)
  economy.py      wallets, charge/reward/fine, mute/revive  (server-authoritative)
  judge.py        chairman: anonymized scoring + verdict (structured JSON)
  debate.py       orchestrator — round loop, yields DebateEvents
  storage.py      per-debate JSON (replay + future RL dataset)
  main.py         FastAPI: POST /api/debate, GET .../events (SSE), static serve
frontend/
  src/state/useDebate.js   EventSource -> useReducer (single source of truth)
  src/lib/glyphs.js        ▓░ meters + sparklines
  src/components/          Hero, Table (SVG ring), AgentChip, Meter,
                           Transcript, RoundSettlement, Verdict, EventLog
```

### Event stream (SSE contract)

`debate_start → round_start → (turn_start → turn_delta* → turn | turn_skipped)* →
round_result → … → verdict → debate_end`

Each debate is stored at `debates/{id}.json` and replayable via `GET /api/debate/{id}`.

## Swapping domains

`personas.py` is pure config. Replace the five personas (e.g. a VC panel, a product team,
a legal review) and nothing else changes — the economy, judge, and UI are domain-agnostic.
