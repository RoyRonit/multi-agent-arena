// The center SVG ring (FRONTEND §5). One hairline circle, 5 nodes, speaker glow,
// rebuttal chord. No avatars, no emoji.
const CX = 200;
const CY = 200;
const R = 150;

function nodePos(i, n) {
  const angle = (-90 + i * (360 / n)) * (Math.PI / 180);
  return { x: CX + R * Math.cos(angle), y: CY + R * Math.sin(angle) };
}

export default function Table({ agents, budgets, activeAgent, round, totalRounds, rebuttal }) {
  const pos = {};
  agents.forEach((a, i) => (pos[a.id] = nodePos(i, agents.length)));

  return (
    <div className="table-wrap">
      <svg className="table-svg" viewBox="0 0 400 400" role="img" aria-label="Debate table">
        <circle cx={CX} cy={CY} r={R} fill="none" stroke="var(--hairline)" strokeWidth="1" />

        {rebuttal && pos[rebuttal.from] && pos[rebuttal.to] && (
          <line
            key={rebuttal.key}
            className="rebuttal-chord"
            x1={pos[rebuttal.from].x}
            y1={pos[rebuttal.from].y}
            x2={pos[rebuttal.to].x}
            y2={pos[rebuttal.to].y}
            stroke={`var(--${agents.find((a) => a.id === rebuttal.from)?.color})`}
            strokeWidth="1"
            opacity="0.25"
          />
        )}

        <text className="ring-center" x={CX} y={CY + 4} textAnchor="middle">
          {round ? `ROUND ${round}/${totalRounds}` : `${totalRounds} ROUNDS`}
        </text>

        {agents.map((a) => {
          const p = pos[a.id];
          const muted = budgets[a.id]?.muted;
          const speaking = activeAgent === a.id;
          const accent = muted ? 'var(--ink-30)' : `var(--${a.color})`;
          return (
            <g
              key={a.id}
              className={`node${speaking ? ' speaking' : ''}`}
              style={{ '--glow': `var(--${a.color})` }}
            >
              <circle
                className="node-circle"
                cx={p.x}
                cy={p.y}
                r={speaking ? 24.6 : 22}
                fill="var(--card)"
                stroke={accent}
                strokeWidth="1.5"
              />
              <text
                className="node-initial"
                x={p.x}
                y={p.y + 6}
                textAnchor="middle"
                fill={muted ? 'var(--ink-30)' : 'var(--ink)'}
              >
                {a.name[0]}
              </text>
              <text
                className="node-name"
                x={p.x}
                y={p.y + 40}
                textAnchor="middle"
                fill="var(--ink-60)"
              >
                {a.name}
              </text>
              {muted && (
                <text className="node-tag" x={p.x} y={p.y + 52} textAnchor="middle">
                  SILENCED
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
