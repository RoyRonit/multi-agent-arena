import { useEffect, useState } from 'react';
import AgentChip from './AgentChip';

const EXAMPLE =
  'Launch a premium cold-brew coffee brand to Gen-Z in India on a ₹50L quarterly budget. We need a hero campaign for the next 3 months.';

// Pre-debate hero — the empty state is the marketing page (FRONTEND §4).
// If the server has an access phrase set, an ASCII captcha gates the Convene button.
export default function Hero({ agents, maxBalance, onConvene }) {
  const [brief, setBrief] = useState('');
  const [rounds, setRounds] = useState(3);

  const [gate, setGate] = useState({ required: false, art: null });
  const [phrase, setPhrase] = useState(() => sessionStorage.getItem('rt_phrase') || '');
  const [gateError, setGateError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch('/api/gate')
      .then((r) => r.json())
      .then(setGate)
      .catch(() => setGate({ required: false, art: null }));
  }, []);

  const canConvene = brief.trim() && (!gate.required || phrase.trim()) && !busy;

  const handleConvene = async () => {
    setGateError('');
    setBusy(true);
    const res = await onConvene(brief.trim(), rounds, phrase.trim());
    setBusy(false);
    if (res && res.ok === false) {
      if (res.status === 401) setGateError('Incorrect phrase — read the captcha and try again.');
      else if (res.status === 429) setGateError(res.message || 'Daily limit reached.');
      else setGateError(res.message || 'Could not start.');
      return;
    }
    if (gate.required) sessionStorage.setItem('rt_phrase', phrase.trim());
  };

  return (
    <div className="hero">
      <div className="eyebrow micro-caps">The Roundtable</div>
      <h1>Five specialists. One brief.<br />Watch them earn their say.</h1>
      <p className="sub">
        A marketing team debates your brief across rounds. Speaking costs budget; novelty
        wins it back. The Chairman scores every turn and writes the verdict.
      </p>

      <div className="brief-form">
        <textarea
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          placeholder={EXAMPLE}
          aria-label="Campaign brief"
        />

        {gate.required && (
          <div className="gate">
            <div className="gate-label micro-caps">Type the phrase to enter</div>
            <pre className="captcha" aria-hidden="true">{gate.art}</pre>
            <input
              className="gate-input mono"
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              placeholder="type it here"
              aria-label="Access phrase from the captcha above"
              autoComplete="off"
              spellCheck="false"
              onKeyDown={(e) => e.key === 'Enter' && canConvene && handleConvene()}
            />
            {gateError && <div className="gate-error mono">{gateError}</div>}
          </div>
        )}

        <div className="controls">
          <label className="rounds-select micro-caps">
            Rounds
            <select value={rounds} onChange={(e) => setRounds(Number(e.target.value))}>
              {[2, 3, 4, 5].map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <button className="pill" disabled={!canConvene} onClick={handleConvene}>
            {busy ? 'Convening…' : 'Convene'}
          </button>
        </div>
      </div>

      <div className="hero-roster">
        {agents.map((a) => (
          <AgentChip key={a.id} agent={a} budget={{ balance: maxBalance }} max={maxBalance} />
        ))}
      </div>
    </div>
  );
}
