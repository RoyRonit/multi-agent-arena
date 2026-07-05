// Final synthesis card (FRONTEND §4 verdict state).
export default function Verdict({ verdict, agents, onExport, onNewDebate }) {
  const colorFor = (name) => {
    const a = agents.find((x) => x.name.toLowerCase() === String(name).toLowerCase());
    return `var(--${a?.color || 'chairman'})`;
  };
  return (
    <div className="verdict-backdrop">
      <div className="verdict-card">
        <div className="micro-caps">The Verdict</div>
        <h2>Chairman's synthesis</h2>
        <div className="verdict-text">{verdict.text}</div>
        {verdict.credits?.length > 0 && (
          <div className="credits">
            <div className="micro-caps">Winning arguments</div>
            {verdict.credits.map((c, i) => (
              <div className="credit" key={i} style={{ '--dot': colorFor(c.agent) }}>
                <span className="c-dot" />
                <span>
                  <span className="c-agent">{c.agent}</span>{' '}
                  <span className="c-arg">{c.argument}</span>
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="verdict-actions">
          <button className="text-btn" onClick={onNewDebate}>
            ← New debate
          </button>
          <button className="pill pill-sm" onClick={onExport}>
            Export transcript
          </button>
        </div>
      </div>
    </div>
  );
}
