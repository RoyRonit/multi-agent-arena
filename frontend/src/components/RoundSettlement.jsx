import { spark } from '../lib/glyphs';

// Mono score table: WIN / 2ND / FINE rows (FRONTEND §3 event log vocabulary).
export default function RoundSettlement({ record, agentById, noveltyHistory }) {
  const { round, scores, winner, runner_up, rewards, fines, reason } = record;

  const rows = scores.map((s) => {
    const a = agentById[s.agent] || {};
    let tag = '—';
    let cls = '';
    if (s.agent === winner) {
      tag = 'WIN';
      cls = 'win';
    } else if (s.agent === runner_up) {
      tag = '2ND';
    }
    const reward = rewards?.[s.agent] || 0;
    const fine = fines?.[s.agent] || 0;
    const delta = reward - fine;
    return { s, a, tag, cls, delta, fine };
  });

  return (
    <div className="settlement">
      <div className="micro-caps" style={{ marginBottom: 8 }}>
        ── Round {round} settled ───────────
      </div>
      {rows.map(({ s, a, tag, cls, delta }) => (
        <div className={`rowline ${cls}`} key={s.agent}>
          <span className="tag">{tag}</span>
          <span>
            {a.name || s.agent}{' '}
            <span className="scores">
              N{s.novelty} · E{s.evidence} · P{s.persuasion} · R{s.redundancy}
            </span>{' '}
            <span className="scores">{spark(noveltyHistory[s.agent] || [])}</span>
          </span>
          <span
            className={`delta ${delta > 0 ? 'pos' : delta < 0 ? 'neg' : ''}`}
          >
            {delta > 0 ? `+${delta}` : delta < 0 ? `−${Math.abs(delta)}` : ''}
          </span>
          <span className="scores">{Number(s.total).toFixed(1)}</span>
        </div>
      ))}
      {reason && <div className="reason">{reason}</div>}
    </div>
  );
}
