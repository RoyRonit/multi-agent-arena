// The micrographic vocabulary (FRONTEND §3). Everything is a string.

const FULL = '▓'; // ▓
const EMPTY = '░'; // ░
const SPARK = ['▁', '▃', '▅', '▆', '█']; // ▁▃▅▆█

// meter(640, 1000) -> "▓▓▓▓▓▓░░░░"  (10 cells = max)
export function meter(balance, max, cells = 10) {
  const ratio = max > 0 ? Math.max(0, Math.min(1, balance / max)) : 0;
  const filled = Math.round(ratio * cells);
  return FULL.repeat(filled) + EMPTY.repeat(cells - filled);
}

// spark([2,5,8,4]) -> "▁▃█▃"  (per-agent novelty across rounds, max 5 glyphs)
export function spark(values, lo = 0, hi = 10) {
  if (!values || !values.length) return '';
  return values
    .slice(-5)
    .map((v) => {
      const t = Math.max(0, Math.min(1, (v - lo) / (hi - lo || 1)));
      return SPARK[Math.round(t * (SPARK.length - 1))];
    })
    .join('');
}

export function signed(n) {
  return n > 0 ? `+ ${n}` : `− ${Math.abs(n)}`; // uses − for minus
}
