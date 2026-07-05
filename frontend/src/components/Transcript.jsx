import RoundSettlement from './RoundSettlement';

// Chat-style feed, persona-colored, interleaved with per-round settlement blocks.
export default function Transcript({ transcript, rounds, agentById, novelty, totalRounds }) {
  const recordByRound = {};
  rounds.forEach((r) => (recordByRound[r.round] = r));

  const maxRound = Math.max(
    totalRounds || 0,
    ...transcript.map((t) => t.round || 0),
    ...rounds.map((r) => r.round || 0),
    0
  );

  const blocks = [];
  for (let r = 1; r <= maxRound; r++) {
    const turns = transcript.filter((t) => t.round === r);
    if (!turns.length && !recordByRound[r]) continue;
    turns.forEach((t) => {
      const color = `var(--${agentById[t.agent_id]?.color || 'chairman'})`;
      blocks.push(
        <div className={`turn${t.skipped ? ' skipped' : ''}`} key={t.key}>
          <div className="turn-head" style={{ '--dot': color }}>
            <span className="t-dot" />
            <span className="t-name">{t.name}</span>
            <span className="t-role">{t.role}</span>
          </div>
          <div className="turn-body">
            {t.text}
            {t.streaming && <span className="caret"> ▍</span>}
          </div>
          {t.cost != null && !t.skipped && (
            <div className="turn-cost">─ cost {t.cost} ▸ balance updated</div>
          )}
        </div>
      );
    });
    if (recordByRound[r]) {
      blocks.push(
        <RoundSettlement
          key={`settle-${r}`}
          record={recordByRound[r]}
          agentById={agentById}
          noveltyHistory={novelty}
        />
      );
    }
  }

  return <div className="transcript">{blocks}</div>;
}
