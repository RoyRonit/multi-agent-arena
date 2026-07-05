import { useState } from 'react';

// Collapsible mono log — the trust/dev view (FRONTEND §7).
export default function EventLog({ log }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="eventlog">
      <button className="text-btn" onClick={() => setOpen((o) => !o)}>
        {open ? 'Hide log' : `Log · ${log.length}`}
      </button>
      {open && (
        <div className="log-lines">
          {log.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      )}
    </div>
  );
}
