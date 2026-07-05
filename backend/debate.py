"""The orchestrator. An async generator that runs a full debate and yields DebateEvents.

Round 1: opening positions. Rounds 2+: each solvent agent sees a compressed digest of
prior claims + the scoreboard and must rebut/build. Anti-convergence is enforced at the
prompt layer (digest of claims to avoid) and the economy layer (fines/rewards).
"""
from __future__ import annotations

import time
from typing import AsyncIterator

from . import config, economy, judge, personas, storage
from .economy import RoundScores


def _estimate_tokens(text: str) -> int:
    # We stream, so we don't get an exact usage count. ~4 chars/token is fine for the
    # abstract-credit economy (PRD: budgets are abstract, mapped loosely to tokens).
    return max(1, round(len(text) / 4))


def _speaking_order(round_num: int, agent_ids: list[str]) -> list[str]:
    """Rotate turn order each round so no one always speaks first."""
    k = (round_num - 1) % len(agent_ids)
    return agent_ids[k:] + agent_ids[:k]


def _build_turn_messages(
    persona: dict,
    brief: str,
    round_num: int,
    total_rounds: int,
    digest: list[str],
    scoreboard: dict[str, int],
    recent_turns: list[dict],
) -> list[dict]:
    already = (
        "\n".join(f"- {c}" for c in digest[-24:])
        if digest
        else "(nothing yet — you are opening the debate)"
    )
    board = (
        ", ".join(f"{name}: {wins} win(s)" for name, wins in scoreboard.items())
        or "no rounds settled yet"
    )
    if round_num == 1:
        context = "This is ROUND 1. State your opening position on the brief."
    else:
        last = "\n\n".join(
            f"{t['name']} ({t['role']}): {t['text']}" for t in recent_turns[-4:]
        )
        context = (
            f"This is ROUND {round_num} of {total_rounds}. You have heard the room. "
            f"Rebut or build — do not restate.\n\nMOST RECENT TURNS:\n{last}"
        )
    user = (
        f"CAMPAIGN BRIEF:\n{brief}\n\n"
        f"SCOREBOARD (round wins): {board}\n\n"
        f"ARGUMENTS ALREADY MADE — DO NOT REPEAT:\n{already}\n\n"
        f"{context}\n\nYour turn ({persona['name']}, {persona['role']}). Under 150 words."
    )
    return [
        {"role": "system", "content": persona["system"]},
        {"role": "user", "content": user},
    ]


async def run_debate(
    debate_id: str, brief: str, rounds: int
) -> AsyncIterator[dict]:
    """Yield DebateEvents. The caller (SSE endpoint) serializes them to the client."""
    from . import openrouter  # local import so import errors surface as events

    agents = personas.public_agents()
    agent_ids = personas.AGENT_IDS
    wallets = economy.new_wallets(agent_ids)
    digest: list[str] = []
    scoreboard: dict[str, int] = {p["name"]: 0 for p in agents}
    transcript: list[dict] = []
    round_records: list[dict] = []

    def persist(status: str, verdict: dict | None = None):
        storage.save(
            debate_id,
            {
                "id": debate_id,
                "brief": brief,
                "rounds": rounds,
                "status": status,
                "agents": agents,
                "transcript": transcript,
                "round_records": round_records,
                "final_budgets": economy.budgets_view(wallets),
                "scoreboard": scoreboard,
                "verdict": verdict,
                "updated_at": time.time(),
            },
        )

    yield {
        "type": "debate_start",
        "debate_id": debate_id,
        "brief": brief,
        "rounds": rounds,
        "agents": agents,
        "budgets": economy.budgets_view(wallets),
    }
    persist("running")

    try:
        for round_num in range(1, rounds + 1):
            yield {"type": "round_start", "round": round_num, "total": rounds}
            this_round_turns: list[dict] = []

            for aid in _speaking_order(round_num, agent_ids):
                persona = personas.PERSONA_BY_ID[aid]
                wallet = wallets[aid]
                if wallet.muted:
                    yield {
                        "type": "turn_skipped",
                        "agent": aid,
                        "round": round_num,
                        "reason": "bankrupt",
                    }
                    continue

                yield {"type": "turn_start", "agent": aid, "round": round_num}
                messages = _build_turn_messages(
                    persona, brief, round_num, rounds, digest, scoreboard, this_round_turns
                )
                text_parts: list[str] = []
                async for chunk in openrouter.stream_chat(
                    config.AGENT_MODEL,
                    messages,
                    temperature=0.85,
                    max_tokens=config.TURN_MAX_TOKENS,
                ):
                    text_parts.append(chunk)
                    yield {"type": "turn_delta", "agent": aid, "chunk": chunk}

                text = "".join(text_parts).strip()
                tokens = _estimate_tokens(text)
                cost = economy.charge(wallet, tokens)
                turn_row = {
                    "agent_id": aid,
                    "name": persona["name"],
                    "role": persona["role"],
                    "round": round_num,
                    "text": text,
                    "tokens": tokens,
                    "cost": cost,
                }
                transcript.append(turn_row)
                this_round_turns.append(turn_row)

                yield {
                    "type": "turn",
                    "agent": aid,
                    "round": round_num,
                    "text": text,
                    "cost": cost,
                    "balance": wallet.balance,
                    "muted": wallet.muted,
                    "budgets": economy.budgets_view(wallets),
                }
                persist("running")

            # --- judge + settle the round ---
            scores = await judge.judge_round(round_num, this_round_turns, digest)
            report = economy.settle_round(wallets, scores)

            if scores.winner_id:
                scoreboard[personas.PERSONA_BY_ID[scores.winner_id]["name"]] += 1
            for sc in scores.by_agent.values():
                digest.extend(sc.new_claims)

            round_record = _round_record(round_num, scores, report, wallets)
            round_records.append(round_record)
            yield {"type": "round_result", **round_record}
            persist("running")

            if economy.solvent_count(wallets) <= 1:
                yield {"type": "debate_early_end", "reason": "insufficient solvent agents"}
                break

        verdict = await judge.write_verdict(brief, transcript, scoreboard)
        yield {"type": "verdict", **verdict}
        persist("complete", verdict)
        yield {"type": "debate_end"}

    except Exception as exc:  # surface errors to the UI instead of a dead stream
        persist("error")
        yield {"type": "error", "message": f"{type(exc).__name__}: {exc}"}


def _round_record(
    round_num: int, scores: RoundScores, report: dict, wallets: dict
) -> dict:
    rows = []
    for aid, sc in scores.by_agent.items():
        rows.append(
            {
                "agent": aid,
                "novelty": sc.novelty,
                "evidence": sc.evidence,
                "persuasion": sc.persuasion,
                "redundancy": sc.redundancy,
                "total": round(sc.total, 2),
                "new_claims": sc.new_claims,
            }
        )
    rows.sort(key=lambda r: r["total"], reverse=True)
    return {
        "round": round_num,
        "scores": rows,
        "winner": scores.winner_id,
        "runner_up": scores.runner_up_id,
        "reason": scores.reason,
        "rewards": {aid: r["reward"] for aid, r in report.items() if r["reward"]},
        "fines": {aid: r["fine"] for aid, r in report.items() if r["fine"]},
        "budgets": economy.budgets_view(wallets),
    }
