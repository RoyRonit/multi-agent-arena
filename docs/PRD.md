# PRD — "The Roundtable": Persona-Based Multi-Agent Debate Arena

**Version:** 0.1 (POC) · **Owner:** Roy · **Target build time:** ≤ 30 minutes · **Base:** fork of [karpathy/llm-council](https://github.com/karpathy/llm-council)

---

## 1. Problem Statement

When a marketer asks a single LLM for a campaign idea, they get one homogenized, averaged answer. Real creative quality comes from *productive disagreement* between specialists — a brand manager fighting a media planner over budget allocation surfaces trade-offs a single model never voices. There is no lightweight tool that (a) simulates a specialist team debating a brief, (b) makes the economics of the debate visible (who's spending, who's winning), and (c) structurally forces novelty so agents don't converge into agreement theater.

## 2. Goals

1. **G1 — Visible multi-agent debate:** User submits one brief; 5 marketing personas argue across ≥2 rounds; every turn is visible in real time on a roundtable UI.
2. **G2 — Transparent economics:** Each agent has a token/credit budget shown live to the user; speaking costs budget; winning a round earns a reward that replenishes it.
3. **G3 — Forced novelty ("anti-convergence loss"):** Each turn is scored for novelty vs. everything already said. Repetition is penalized (budget deduction, lower round score); new ideas/facts are rewarded. Measured target: ≥70% of turns introduce at least one claim not present in prior turns (judge-scored).
4. **G4 — Hostable POC today:** Single-command run, deployable to Render/Railway/Fly with one env var (`OPENROUTER_API_KEY`).
5. **G5 — Usable output:** A Chairman synthesis at the end that credits the winning arguments, so the user leaves with a decision, not just a transcript.

## 3. Non-Goals (v0)

- **No real RL / gradient-based loss optimization.** "Loss function" in v0 is an LLM-judge scoring rubric + budget economics, not model fine-tuning. (Real training is a v2+ research direction.)
- **No multi-domain persona packs.** Marketing only. The persona schema is generic so legal/product/finance packs are a config file away, but we won't build them now.
- **No auth, persistence beyond local JSON, or multi-user rooms.** Single-session, single-user POC.
- **No human-in-the-loop mid-debate steering** (interjections, voting). P2.
- **No cost billing to real money.** Budgets are abstract credits mapped loosely to tokens.

## 4. Users & User Stories

Primary persona: **Marketing lead / founder** briefing a campaign.

- As a marketing lead, I want to paste a campaign brief and watch 5 specialist agents debate it, so that I see trade-offs I'd miss from one AI answer.
- As a user, I want to see each agent's remaining budget as a live bar/ring, so I understand who has "spent themselves out" and why an agent went quiet.
- As a user, I want to see who won each round and why, so the reward system feels earned and not arbitrary.
- As a user, I want each round to produce *new* arguments and facts, so round 3 isn't a rephrasing of round 1.
- As a user, I want a final synthesized recommendation crediting the winning arguments, so I can act on the debate.
- As a user, I want to see a clear "bankrupt" state when an agent runs out of budget (agent grays out, skips turns), so the economy has real consequences.

## 5. The Cast (Marketing Persona Pack v1)

Each persona = system prompt with: role identity, private incentive, argumentation style, and a "novelty mandate."

| Agent | Persona core | Bias / private incentive | Style |
|---|---|---|---|
| **Brand Manager** | Guardian of long-term brand equity and consistency | Distrusts performance hacks; defends positioning | Principled, cites brand case studies |
| **Media Manager** | Owns channel execution & platform realities | Wants feasible, platform-native ideas | Pragmatic, data-dropping, blunt |
| **Scriptwriter** | Narrative and hook craft for video | Fights for emotional storytelling over metrics | Vivid, example-led, pitches openings verbatim |
| **Copywriter** | Words that convert; headlines, CTAs | Believes one killer line beats a big plan | Punchy, rewrites others' ideas sharper |
| **Media Planner** | Budget allocation, reach/frequency math | Kills ideas that don't survive CPM math | Quantitative, skeptical, brings numbers each turn |

**Chairman (non-playing):** neutral judge + synthesizer. Scores rounds, allocates rewards, writes the final answer.

## 6. Core Mechanics (the "game")

### 6.1 Budget
- Every agent starts with **B₀ = 1,000 credits** (configurable).
- Speaking a turn costs `cost = base_fee (50) + tokens_generated × 0.1` (tunable).
- Budget is rendered live per agent. At **budget ≤ 0** the agent is **muted** (grayed on the table, skips turns) until/unless a reward revives it.

### 6.2 Rounds
- A debate = **R rounds** (default 3). Round 1: opening positions (parallel). Rounds 2+: each agent sees the full transcript + current scoreboard and must rebut/build.
- After each round the **Chairman judges** all turns (agent names anonymized, as in llm-council) on a rubric:
  - **Novelty (0–10):** new ideas/facts not present in any earlier turn
  - **Evidence (0–10):** concrete facts, numbers, examples
  - **Persuasion (0–10):** directly engages and counters other agents
- **Round winner** = highest total. Reward: **+300 credits** to winner, **+100** runner-up.

### 6.3 Anti-convergence "loss" (v0 implementation)
The optimization target for each agent turn is:

```
score(turn) = w1·novelty + w2·evidence + w3·persuasion − w4·redundancy_penalty
```

- `redundancy_penalty`: Chairman flags overlap with prior turns (0–10). Overlap ≥ 7 ⇒ additional **−100 credit fine**.
- Enforced two ways: (a) *prompt-level* — each agent's turn prompt includes "arguments already made (do not repeat)" digest and a hard instruction to contribute ≥1 new idea and ≥1 new fact; (b) *economics-level* — the fine/reward loop above. This is the honest v0 stand-in for a trained loss; the reward signal is logged per turn so v2 could actually train on it.

### 6.4 End state
Debate ends after R rounds or when ≤1 agent is solvent. Chairman writes the **Verdict**: recommendation + "winning arguments" attribution + dissent worth keeping.

## 7. Requirements

### P0 (must ship in POC)
- [ ] Fork llm-council; replace model-council with persona-council (same OpenRouter model × 5 system prompts is fine)
- [ ] Round loop (default 3) with sequential turn streaming to UI
- [ ] Budget engine: per-turn cost deduction, mute at 0, reward on round win, fine on redundancy — all server-authoritative
- [ ] Chairman judge call after each round returning structured JSON scores (novelty/evidence/persuasion/redundancy)
- [ ] Roundtable UI: 5 avatars on a circle, active speaker highlighted, live budget bar per agent, per-round scoreboard, streamed turn text
- [ ] Final Verdict panel
- [ ] Single env var config; deployable (FastAPI serves built frontend)

### P1 (fast follow)
- [ ] SSE/WebSocket token-level streaming (P0 can stream turn-by-turn)
- [ ] Persona pack as JSON config → swap domains (product team, legal, VC panel)
- [ ] Debate replay/export (markdown transcript download)
- [ ] Per-agent cumulative win/loss record across sessions

### P2 (future)
- [ ] User interjections and user voting affecting rewards
- [ ] Embedding-based redundancy scoring (cosine sim vs. transcript) replacing judge-only
- [ ] Real preference-signal logging → DPO/RL fine-tuning of persona agents
- [ ] Different underlying models per persona; budget = real dollar spend

## 8. Success Metrics (POC)
- **Novelty rate:** ≥70% of round-2+ turns score novelty ≥6 (leading)
- **Debate completion:** full 3-round debate + verdict completes in <90s wall time, <$0.10 API cost per debate
- **Legibility check:** a viewer can answer "who is winning and why" from the UI alone (informal test with 3 people)
- **Deployability:** cold clone → running locally in ≤5 min

## 9. Acceptance Criteria (P0 spot checks)
- Given an agent at 40 credits, when their turn cost is 55, then they go bankrupt mid-round, are visually muted, and skip subsequent turns.
- Given Chairman flags Copywriter's turn redundancy = 8, then Copywriter is fined 100 credits and the fine appears in the event log.
- Given round 2 ends, when scores are computed, then exactly one winner (+300) and one runner-up (+100) are credited and budget bars animate.
- Given the debate ends, then the Verdict cites at least 2 agents by name with their winning arguments.

## 10. Open Questions
- **(design)** Budget unit shown to user: raw credits vs. "$" theming? → v0: credits.
- **(eng)** One model × 5 personas vs. 5 different models? → v0: one cheap fast model (e.g. `claude-haiku` / `gemini-flash` via OpenRouter) for cost & speed; config already supports mixing.
- **(product)** Should a bankrupt agent be permanently out, or revivable by next-round reward? → v0: revivable (more fun, less punitive), flag to toggle.
- **(non-blocking, research)** How to log reward signals so they're actually usable for future RL — see architecture doc §7.

## 11. Timeline / Phasing
- **T+30 min:** P0 running locally (this doc's scope)
- **T+1 day:** P1 streaming + persona packs, deploy to Railway/Render
- **Later:** P2 research track (real reward learning)
