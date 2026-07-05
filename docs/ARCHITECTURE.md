# Architecture — The Roundtable (POC, ≤30-min build)

Base: fork of `karpathy/llm-council` (FastAPI + OpenRouter backend, React/Vite frontend, JSON file storage). We keep its bones — `openrouter.py` (parallel LLM calls), `main.py` (API), `storage.py` (JSON persistence), frontend scaffolding — and replace the 3-stage council with a **round-based debate engine + budget economy**.

---

## 1. System Overview

```
┌──────────────────────────────  Browser (React/Vite)  ─────────────────────────────┐
│  RoundTable.jsx        BudgetBar.jsx      Scoreboard.jsx      VerdictPanel.jsx     │
│  (circular SVG,        (per-agent         (per-round          (chairman            │
│   speaker glow)         credit bars)       scores/winner)      synthesis)          │
│                    ▲ SSE stream of DebateEvents                                    │
└────────────────────┼───────────────────────────────────────────────────────────────┘
                     │  POST /api/debate  +  GET /api/debate/{id}/events (SSE)
┌────────────────────┼───────────────────────────────────────────────────────────────┐
│  FastAPI backend    │                                                              │
│  ┌───────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ debate.py     │─▶│ economy.py       │  │ judge.py       │  │ personas.py    │   │
│  │ (round loop,  │  │ (budgets, costs, │  │ (chairman:     │  │ (JSON persona  │   │
│  │  turn order,  │  │  rewards, fines, │  │  score turns,  │  │  pack: prompts │   │
│  │  transcript)  │  │  mute/revive)    │  │  pick winner,  │  │  + incentives) │   │
│  └───────────────┘  └──────────────────┘  │  verdict)      │  └────────────────┘   │
│          │                                └────────────────┘                       │
│          ▼                                                                          │
│  openrouter.py (kept from fork — async parallel/serial model calls)                │
│  storage.py    (kept — JSON per-debate persistence for replay)                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

One model (cheap/fast via OpenRouter) × 5 system prompts = 5 agents. Chairman = a stronger model, called with `response_format: json` for scoring.

## 2. Backend modules

### 2.1 `personas.py` — persona pack (config, not code)
```python
PERSONAS = [
  {
    "id": "brand_manager",
    "name": "Priya · Brand Manager",
    "color": "#E11D48",
    "system": """You are Priya, Brand Manager. You protect long-term brand equity...
      PRIVATE INCENTIVE: you win rounds by proving short-term hacks damage the brand.
      RULES: Every turn you MUST (1) introduce at least one idea or fact not yet said,
      (2) directly rebut one named colleague, (3) stay under 150 words."""
  },
  # media_manager, scriptwriter, copywriter, media_planner ...
]
CHAIRMAN_SYSTEM = "You are a neutral chairman. Judge anonymized turns. Return strict JSON."
```
Swapping domains later = new JSON file. Nothing else changes.

### 2.2 `economy.py` — the budget engine (server-authoritative)
```python
@dataclass
class Wallet:
    balance: int = 1000
    muted: bool = False

BASE_FEE = 50
TOKEN_RATE = 0.1          # credits per output token
WIN_REWARD, RUNNERUP_REWARD = 300, 100
REDUNDANCY_FINE, REDUNDANCY_THRESHOLD = 100, 7

def charge(wallet, tokens):      # called after each turn
    wallet.balance -= int(BASE_FEE + tokens * TOKEN_RATE)
    wallet.muted = wallet.balance <= 0

def settle_round(wallets, scores):   # rewards, fines, possible revivals
    ...
```
Every mutation emits a `DebateEvent` so the UI can animate bars honestly.

### 2.3 `judge.py` — the "loss function" (v0)
After each round, one chairman call with anonymized turns → strict JSON:
```json
{"scores": [{"label":"A","novelty":8,"evidence":6,"persuasion":7,"redundancy":2,
             "new_claims":["UGC creators under 10k followers out-convert macro 3:1"]}],
 "winner":"A","runner_up":"C","reason":"..."}
```
`turn_score = 0.4·novelty + 0.3·evidence + 0.3·persuasion − 0.5·redundancy`

Anti-convergence is enforced at three layers:
1. **Prompt:** each turn prompt embeds a compressed digest `ARGUMENTS ALREADY MADE — DO NOT REPEAT: [...]` (built from judge-extracted `new_claims`, so it stays short instead of the full transcript).
2. **Judgment:** redundancy score above.
3. **Economy:** redundancy ≥ 7 ⇒ fine; novelty drives round wins ⇒ rewards. Agents "optimize" against this because muting = losing voice.

All (state, turn, score) triples are appended to `debates/{id}.json` — this is the future RL dataset (see §7).

### 2.4 `debate.py` — orchestrator
```python
async def run_debate(brief, rounds=3):
    yield event("debate_start", agents=..., budgets=...)
    digest = []
    # Round 1: parallel opening statements (fast)
    # Rounds 2..R: sequential turns, each sees transcript digest + scoreboard
    for r in range(1, rounds+1):
        for agent in speaking_order(r):          # rotate order each round
            if wallets[agent].muted: yield event("turn_skipped", agent); continue
            text, tokens = await speak(agent, brief, digest, scoreboard)
            charge(wallets[agent], tokens)
            yield event("turn", agent, text, wallets)
        scores = await judge_round(...)
        settle_round(wallets, scores)
        digest += extract_new_claims(scores)
        yield event("round_result", scores, wallets)
    verdict = await chairman_verdict(brief, transcript, scoreboard)
    yield event("verdict", verdict)
```

### 2.5 API (replaces llm-council's endpoints)
| Endpoint | Purpose |
|---|---|
| `POST /api/debate` `{brief, rounds?}` | create debate, returns `id` |
| `GET /api/debate/{id}/events` | **SSE stream** of DebateEvents (turn, budget_update, round_result, verdict) |
| `GET /api/debate/{id}` | full stored state (replay) |

SSE > WebSocket here: one-directional, trivial with FastAPI `StreamingResponse`, works on all PaaS hosts.

## 3. Event schema (single contract UI ↔ backend)
```ts
type DebateEvent =
 | {type:"debate_start", agents:Agent[], budgets:Record<string,number>}
 | {type:"turn", agent:string, text:string, cost:number, balance:number}
 | {type:"turn_skipped", agent:string, reason:"bankrupt"}
 | {type:"round_result", round:number, scores:Score[], winner:string,
    rewards:Record<string,number>, fines:Record<string,number>, budgets:Record<string,number>}
 | {type:"verdict", text:string, credits:{agent:string, argument:string}[]}
```

## 4. Frontend (keep Vite scaffold, replace App internals)

- **RoundTable.jsx** — SVG circle; 5 avatar nodes at `angle = i·72°`; active speaker gets glow + connecting line to center; bankrupt agents at 30% opacity with a 💸 badge.
- **BudgetBar.jsx** — ring or bar under each avatar; animates on `turn` (red tick down) and `round_result` (green tick up / red fine). Numbers always visible (G2).
- **TranscriptFeed.jsx** — chat-style feed, persona-colored, streamed per turn.
- **Scoreboard.jsx** — per-round table: N / E / P / R scores, 🏆 winner.
- **VerdictPanel.jsx** — final synthesis with "winning arguments" chips linking back to turns.
- State: single `useReducer` fed by an `EventSource`; no state library needed.

## 5. Deployment (POC)
- `npm run build` → FastAPI serves `frontend/dist` as static (add `StaticFiles` mount to `main.py`).
- One Dockerfile (python:3.12-slim, copy dist, `uvicorn backend.main:app`). Host on Railway/Render/Fly. Config = `OPENROUTER_API_KEY` only.
- Cost control: haiku/flash-class model for agents, 150-word turn cap, 3 rounds ⇒ ~20 LLM calls ≈ cents per debate.

## 6. 30-minute build order
1. **(0–5)** Clone fork, strip `council.py` 3-stage logic; keep `openrouter.py`, `storage.py`, `main.py` shell.
2. **(5–12)** `personas.py` (5 prompts + chairman) + `economy.py` (~60 lines).
3. **(12–20)** `debate.py` round loop + `judge.py` JSON scoring + SSE endpoint.
4. **(20–28)** Frontend: RoundTable SVG + budget bars + transcript feed wired to EventSource (replace existing App.jsx content; reuse its CSS/tab patterns where possible).
5. **(28–30)** Smoke test with a real brief; tune fees so ~1 agent goes broke by round 3 (drama calibration).

## 7. Path from "game economics" to a real loss (v2 research note)
The v0 reward signal `(state, action=turn_text, reward=turn_score+Δbudget)` is logged per turn. That's a preference/reward dataset:
- **Cheap next step:** best-of-n at inference — sample 2 candidate turns per agent, judge picks one (rejection sampling ≈ optimizing the same objective, no training).
- **Real step:** DPO on (winning turn, losing turn) pairs per persona, or GRPO with the judge rubric as reward model. The anti-convergence term becomes an explicit diversity reward: `−sim(turn_emb, transcript_embs)`.
This is why judge output is structured JSON from day one — the POC doubles as a data collector.

## 8. Key risks & mitigations
- **Agreement collapse** (agents politely converge) → private incentives in personas + mandatory rebuttal rule + redundancy fine.
- **Judge inconsistency** → anonymized labels (inherited from llm-council), fixed rubric, temperature 0, strict JSON.
- **Latency** → parallel round 1, small model, word caps; SSE keeps perceived latency low.
- **Runaway cost** → hard cap: max rounds, max tokens/turn, per-debate call ceiling.
