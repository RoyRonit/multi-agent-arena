import Meter from './Meter';

// Dot + name/role + budget meter. Used in the hero roster and under the table.
export default function AgentChip({ agent, budget, max, ticker }) {
  const muted = budget?.muted;
  const balance = budget?.balance ?? max;
  return (
    <div
      className={`chip${muted ? ' muted' : ''}`}
      style={{ '--dot': `var(--${agent.color})` }}
    >
      <span className="dot" />
      <span>
        <div className="chip-name">{agent.name}</div>
        <div className="chip-role">{agent.role}</div>
      </span>
      <span className="chip-meter">
        <Meter balance={balance} max={max} muted={muted} ticker={ticker} />
      </span>
    </div>
  );
}
