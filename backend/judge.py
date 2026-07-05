"""The Chairman — the v0 'loss function'. Scores anonymized turns, picks a winner,
writes the verdict. Structured JSON from day one so the POC doubles as an RL dataset
(ARCHITECTURE §7).
"""
from __future__ import annotations

import string

from . import config, openrouter, personas
from .economy import RoundScores, TurnScore


def _anonymize(turns: list[dict]) -> tuple[str, dict[str, str]]:
    """Map each turn to a label A, B, C... Returns (rendered_block, label->agent_id)."""
    labels = string.ascii_uppercase
    label_to_agent: dict[str, str] = {}
    lines = []
    for i, t in enumerate(turns):
        label = labels[i]
        label_to_agent[label] = t["agent_id"]
        lines.append(f"[{label}]\n{t['text']}")
    return "\n\n".join(lines), label_to_agent


async def judge_round(
    round_num: int, turns: list[dict], transcript_digest: list[str]
) -> RoundScores:
    """Call the chairman to score this round's turns. `turns` = [{agent_id, text}]."""
    if not turns:
        return RoundScores(by_agent={}, winner_id=None, runner_up_id=None)

    block, label_to_agent = _anonymize(turns)
    already = (
        "\n".join(f"- {c}" for c in transcript_digest)
        if transcript_digest
        else "(nothing yet — this is round 1)"
    )
    user = (
        f"ROUND {round_num} TURNS (anonymized):\n\n{block}\n\n"
        f"ARGUMENTS ALREADY MADE IN EARLIER ROUNDS (for novelty/redundancy):\n{already}\n\n"
        "Score every labelled turn. Return strict JSON per the rubric."
    )
    data = await openrouter.complete_json(
        config.CHAIRMAN_MODEL,
        [
            {"role": "system", "content": personas.CHAIRMAN_JUDGE_SYSTEM},
            {"role": "user", "content": user},
        ],
    )

    by_agent: dict[str, TurnScore] = {}
    for row in data.get("scores", []):
        label = str(row.get("label", "")).strip().upper()
        agent_id = label_to_agent.get(label)
        if not agent_id:
            continue
        by_agent[agent_id] = TurnScore(
            agent_id=agent_id,
            novelty=_clamp(row.get("novelty")),
            evidence=_clamp(row.get("evidence")),
            persuasion=_clamp(row.get("persuasion")),
            redundancy=_clamp(row.get("redundancy")),
            new_claims=[str(c) for c in (row.get("new_claims") or [])][:3],
        )

    winner_id = label_to_agent.get(str(data.get("winner", "")).strip().upper())
    runner_up_id = label_to_agent.get(str(data.get("runner_up", "")).strip().upper())

    # Fallback / sanity: if the judge didn't name a valid winner, rank by weighted total.
    if by_agent and (winner_id not in by_agent):
        ranked = sorted(by_agent.values(), key=lambda s: s.total, reverse=True)
        winner_id = ranked[0].agent_id
        runner_up_id = ranked[1].agent_id if len(ranked) > 1 else None
    if runner_up_id == winner_id:
        runner_up_id = None

    return RoundScores(
        by_agent=by_agent,
        winner_id=winner_id,
        runner_up_id=runner_up_id,
        reason=str(data.get("reason", "")),
    )


async def write_verdict(brief: str, transcript: list[dict], scoreboard: dict) -> dict:
    """Final synthesis. transcript = [{agent_id, name, role, round, text}]."""
    lines = []
    for t in transcript:
        lines.append(f"[Round {t['round']}] {t['name']} · {t['role']}: {t['text']}")
    body = "\n\n".join(lines)
    tallies = ", ".join(f"{name}: {pts}" for name, pts in scoreboard.items())
    user = (
        f"CAMPAIGN BRIEF:\n{brief}\n\n"
        f"FULL DEBATE TRANSCRIPT:\n{body}\n\n"
        f"ROUND-WIN TALLY: {tallies}\n\n"
        "Write the verdict as strict JSON."
    )
    data = await openrouter.complete_json(
        config.CHAIRMAN_MODEL,
        [
            {"role": "system", "content": personas.CHAIRMAN_VERDICT_SYSTEM},
            {"role": "user", "content": user},
        ],
        max_tokens=900,
    )
    credits = []
    for c in data.get("credits", []):
        credits.append(
            {"agent": str(c.get("agent", "")), "argument": str(c.get("argument", ""))}
        )
    return {"text": str(data.get("text", "")).strip(), "credits": credits}


def _clamp(v, lo: int = 0, hi: int = 10) -> int:
    try:
        return max(lo, min(hi, int(round(float(v)))))
    except (TypeError, ValueError):
        return 0
