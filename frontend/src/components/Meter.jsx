import { meter, signed } from '../lib/glyphs';

// Renders the glyph budget meter + numeric value + a transient ticker.
export default function Meter({ balance, max, muted, ticker }) {
  if (muted && balance <= 0) {
    return (
      <span className="meter" aria-label={`budget 0 of ${max}, silenced`}>
        <span className="cells mono">{meter(0, max)}</span>
        <span className="silenced">SILENCED</span>
      </span>
    );
  }
  return (
    <span className="meter" aria-label={`budget ${balance} of ${max}`}>
      <span className={`cells mono${ticker?.kind === 'charge' ? ' loss-flash' : ''}`}>
        {meter(balance, max)}
      </span>
      <span className="value">{balance}</span>
      {ticker && (
        <span key={ticker.key} className={`ticker ${ticker.kind}`}>
          {signed(ticker.amount)} ▸ {balance}
        </span>
      )}
    </span>
  );
}
