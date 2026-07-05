"""The budget engine — server-authoritative (PRD §6, ARCHITECTURE §2.2).

Speaking costs credits; winning a round pays; redundancy is fined; balance <= 0 mutes.
Every mutation returns numbers the orchestrator turns into DebateEvents so the UI can
animate bars honestly.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config


@dataclass
class Wallet:
    balance: int = field(default_factory=lambda: config.START_BALANCE)
    muted: bool = False

    def snapshot(self) -> dict:
        return {"balance": self.balance, "muted": self.muted}


def new_wallets(agent_ids: list[str]) -> dict[str, Wallet]:
    return {aid: Wallet() for aid in agent_ids}


def turn_cost(tokens: int) -> int:
    return int(config.BASE_FEE + tokens * config.TOKEN_RATE)


def charge(wallet: Wallet, tokens: int) -> int:
    """Deduct the cost of a turn. Returns the cost charged. Mutes if it empties."""
    cost = turn_cost(tokens)
    wallet.balance -= cost
    if wallet.balance <= 0:
        wallet.balance = max(wallet.balance, 0)
        wallet.muted = True
    return cost


def settle_round(
    wallets: dict[str, Wallet], round_scores: "RoundScores"
) -> dict:
    """Apply rewards + fines after a judged round.

    Returns a per-agent delta report: {agent_id: {"reward":int,"fine":int,"delta":int}}.
    Revival rule: any reward that lifts balance above 0 un-mutes the agent (v0 = revivable).
    """
    report: dict[str, dict] = {aid: {"reward": 0, "fine": 0, "delta": 0} for aid in wallets}

    # Fines first (redundancy), then rewards (so a winner who was also redundant nets out).
    for aid, sc in round_scores.by_agent.items():
        if sc.redundancy >= config.REDUNDANCY_THRESHOLD:
            report[aid]["fine"] = config.REDUNDANCY_FINE

    if round_scores.winner_id and round_scores.winner_id in report:
        report[round_scores.winner_id]["reward"] += config.WIN_REWARD
    if round_scores.runner_up_id and round_scores.runner_up_id in report:
        report[round_scores.runner_up_id]["reward"] += config.RUNNERUP_REWARD

    for aid, r in report.items():
        delta = r["reward"] - r["fine"]
        r["delta"] = delta
        w = wallets[aid]
        w.balance += delta
        if w.balance <= 0:
            w.balance = max(w.balance, 0)
            w.muted = True
        elif w.balance > 0:
            w.muted = False  # revived
    return report


def budgets_view(wallets: dict[str, Wallet]) -> dict[str, dict]:
    return {aid: w.snapshot() for aid, w in wallets.items()}


def solvent_count(wallets: dict[str, Wallet]) -> int:
    return sum(1 for w in wallets.values() if not w.muted)


# --- lightweight scoring container the judge fills and economy reads ---


@dataclass
class TurnScore:
    agent_id: str
    novelty: int = 0
    evidence: int = 0
    persuasion: int = 0
    redundancy: int = 0
    new_claims: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return (
            config.W_NOVELTY * self.novelty
            + config.W_EVIDENCE * self.evidence
            + config.W_PERSUASION * self.persuasion
            - config.W_REDUNDANCY * self.redundancy
        )


@dataclass
class RoundScores:
    by_agent: dict[str, TurnScore]
    winner_id: str | None
    runner_up_id: str | None
    reason: str = ""
